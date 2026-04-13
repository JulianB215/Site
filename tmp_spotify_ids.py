import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request


USER_AGENT = "Mozilla/5.0"
TOKEN_URL_OFFICIAL = "https://accounts.spotify.com/api/token"
TOKEN_URL_FALLBACK = (
    "https://open.spotify.com/get_access_token"
    "?reason=transport&productType=web_player"
)
SEARCH_URL = "https://api.spotify.com/v1/search"
WEB_SEARCH_URL = "https://open.spotify.com/search"
INDEX_FILE = "index.html"


def normalize_text(value):
    text = (value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def request_json(url, headers=None, data=None):
    req = urllib.request.Request(url, headers=headers or {}, data=data)
    with urllib.request.urlopen(req, timeout=30) as res:
        raw = res.read().decode("utf-8", "ignore")
    return json.loads(raw)


def get_spotify_token():
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()

    if client_id and client_secret:
        body = urllib.parse.urlencode(
            {"grant_type": "client_credentials"}
        ).encode("utf-8")
        basic = (f"{client_id}:{client_secret}").encode("utf-8")
        import base64

        headers = {
            "Authorization": "Basic " + base64.b64encode(basic).decode("ascii"),
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        }
        obj = request_json(TOKEN_URL_OFFICIAL, headers=headers, data=body)
        token = obj.get("access_token")
        if token:
            return token

    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://open.spotify.com/",
        "Origin": "https://open.spotify.com",
    }
    obj = request_json(TOKEN_URL_FALLBACK, headers=headers)
    token = obj.get("accessToken")
    if not token:
        raise RuntimeError("Impossible de recuperer un token Spotify")
    return token


def parse_artists_from_index(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    block_match = re.search(
        r"const\s+VERIFIED_SPOTIFY_IDS\s*=\s*\{(.*?)\};",
        content,
        flags=re.DOTALL,
    )
    if not block_match:
        raise RuntimeError("Bloc VERIFIED_SPOTIFY_IDS introuvable dans index.html")

    block = block_match.group(1)
    keys = re.findall(r"'([^']+)'\s*:\s*'[^']*'", block)
    if not keys:
        raise RuntimeError("Aucun rappeur trouve dans VERIFIED_SPOTIFY_IDS")
    return keys


def pick_best_artist(query_name, items):
    nq = normalize_text(query_name)
    best = None
    best_score = -1

    for item in items:
        name = item.get("name", "")
        nn = normalize_text(name)
        popularity = int(item.get("popularity", 0) or 0)

        score = popularity / 5.0
        if nn == nq:
            score += 100
        elif nq in nn:
            score += 40
        elif nn in nq:
            score += 20

        if score > best_score:
            best_score = score
            best = item

    return best


def find_artist_id(token, artist_name, market="FR", limit=10):
    params = {
        "q": f"artist:{artist_name}",
        "type": "artist",
        "limit": str(limit),
        "market": market,
    }
    url = SEARCH_URL + "?" + urllib.parse.urlencode(params)
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
    }
    obj = request_json(url, headers=headers)
    items = (obj.get("artists") or {}).get("items") or []
    if not items:
        return None, None

    best = pick_best_artist(artist_name, items)
    if not best:
        return None, None

    return best.get("id"), best.get("name")


def find_artist_id_via_web(artist_name):
    q = urllib.parse.quote(artist_name)
    url = f"{WEB_SEARCH_URL}/{q}/artists"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://open.spotify.com/",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as res:
        html = res.read().decode("utf-8", "ignore")

    matches = re.findall(r"spotify:artist:([0-9A-Za-z]{22})", html)
    if matches:
        return matches[0], None

    # Secondary pattern used in some page payloads.
    matches = re.findall(r'"/artist/([0-9A-Za-z]{22})"', html)
    if matches:
        return matches[0], None

    return None, None


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Recupere l'ID Spotify de chaque rappeur present dans "
            "VERIFIED_SPOTIFY_IDS (index.html)."
        )
    )
    parser.add_argument(
        "--index",
        default=INDEX_FILE,
        help="Chemin vers index.html (defaut: index.html)",
    )
    parser.add_argument(
        "--market",
        default="FR",
        help="Market Spotify pour la recherche (defaut: FR)",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Fichier de sortie JSON (optionnel)",
    )
    args = parser.parse_args()

    try:
        artists = parse_artists_from_index(args.index)
    except Exception as exc:
        print(f"Erreur initialisation: {exc}", file=sys.stderr)
        return 1

    token = None
    token_error = None
    try:
        token = get_spotify_token()
    except Exception as exc:
        token_error = exc
        print(
            "Token Spotify indisponible, fallback web active "
            f"({exc}).",
            file=sys.stderr,
        )

    result = {}
    unresolved = []

    for artist in artists:
        artist_id, matched_name = None, None
        if token:
            try:
                artist_id, matched_name = find_artist_id(token, artist, market=args.market)
            except Exception as exc:
                print(f"Erreur API pour '{artist}': {exc}", file=sys.stderr)

        if not artist_id:
            try:
                artist_id, matched_name = find_artist_id_via_web(artist)
            except Exception as exc:
                print(f"Erreur fallback web pour '{artist}': {exc}", file=sys.stderr)
                artist_id, matched_name = None, None

        if artist_id:
            result[artist] = artist_id
            print(f"OK  {artist:<20} -> {artist_id} ({matched_name})")
        else:
            result[artist] = None
            unresolved.append(artist)
            print(f"KO  {artist}")

    output = json.dumps(result, ensure_ascii=False, indent=2)
    print("\n=== JSON ===")
    print(output)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"\nEcrit dans: {args.out}")

    if unresolved:
        print("\nRappeurs non resolus:")
        for name in unresolved:
            print(f"- {name}")

    if token_error:
        print(
            "\nInfo: le script a tourne sans token API Spotify "
            "(fallback HTML). Pour des resultats plus precis, definis "
            "SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
