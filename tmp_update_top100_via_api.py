import base64
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

INDEX = Path("index.html")
OUT = Path("spotify_ids.json")


def norm(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def get_creds_from_index():
    env_id = (os.getenv("SPOTIFY_CLIENT_ID") or "").strip()
    env_secret = (os.getenv("SPOTIFY_CLIENT_SECRET") or "").strip()
    if env_id and env_secret:
        return env_id, env_secret

    txt = INDEX.read_text(encoding="utf-8")
    m1 = re.search(r"SPOTIFY_CLIENT_ID\s*=\s*'([^']+)'", txt)
    m2 = re.search(r"SPOTIFY_CLIENT_SECRET\s*=\s*'([^']+)'", txt)
    if not m1 or not m2:
        raise RuntimeError("SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET introuvables (env et index.html)")
    return m1.group(1).strip(), m2.group(1).strip()


def get_token(client_id: str, client_secret: str) -> str:
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=body,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        obj = json.loads(res.read().decode("utf-8", "ignore"))
    token = obj.get("access_token", "")
    if not token:
        raise RuntimeError("Impossible de recuperer un token Spotify")
    return token


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def search_artist_id(token: str, name: str):
    params = urllib.parse.urlencode(
        {"q": f"artist:{name}", "type": "artist", "limit": "10", "market": "FR"}
    )
    req = urllib.request.Request(
        f"https://api.spotify.com/v1/search?{params}",
        headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        obj = json.loads(res.read().decode("utf-8", "ignore"))

    items = ((obj.get("artists") or {}).get("items") or [])
    if not items:
        return None, None

    target = normalize_text(name)
    best = None
    best_score = -1
    for item in items:
        iname = item.get("name", "")
        nname = normalize_text(iname)
        pop = int(item.get("popularity", 0) or 0)
        score = pop / 5.0
        if nname == target:
            score += 100
        elif target and target in nname:
            score += 40
        elif nname and nname in target:
            score += 20
        if score > best_score:
            best_score = score
            best = item

    return (best or {}).get("id"), (best or {}).get("name")


TOP100_RAP_FR = [
    "jul", "ninho", "booba", "sch", "damso", "nekfeu", "orelsan", "soprano", "sexion d assaut", "pnl",
    "niska", "gazo", "tiakola", "koba la d", "leto", "maes", "vald", "laceim", "lacrim", "hamza",
    "freeze corleone", "heuss l enfer", "kaaris", "rohff", "youssoupha", "josman", "jok air", "dosseh", "plk", "sdm",
    "zola", "niro", "naps", "naza", "lomepal", "alpha wann", "dinos", "franglish", "gims", "black m",
    "lefa", "dadju", "soolking", "alonzo", "hornet la frappe", "gambi", "fianso", "sofiane", "kalash criminel", "mhd",
    "benab", "soso maness", "zkr", "zed", "rk", "timal", "mister v", "kekra", "deen burbigo", "veerus",
    "zamdane", "disiz", "medine", "sinik", "la fouine", "mister you", "seth gueko", "lino", "iam", "fonky family",
    "lunatic", "sniper", "ideal j", "kery james", "arsenik", "passi", "stomy bugsy", "doc gyneco", "mc solaar", "suprême ntm",
    "caballero", "jeanjass", "ashkidd", "bekar", "khali", "doria", "landy", "uzi", "kofs", "hatik",
    "genezio", "ben plg", "j9ueve", "spri noir", "fabe", "sadek", "sultan", "hooss", "maska", "ol kainry",
]


def main():
    cid, csec = get_creds_from_index()
    token = get_token(cid, csec)

    if OUT.exists():
        data = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        data = {}

    artists = []
    seen = set()
    for name in TOP100_RAP_FR:
        k = norm(name)
        if k and k not in seen:
            seen.add(k)
            artists.append(k)

    added = 0
    updated = 0
    unresolved = []

    for artist in artists:
        try:
            artist_id, _ = search_artist_id(token, artist)
        except Exception:
            artist_id = None

        if artist_id:
            if artist not in data:
                added += 1
            elif data.get(artist) != artist_id:
                updated += 1
            data[artist] = artist_id
        else:
            if artist not in data:
                data[artist] = None
            unresolved.append(artist)

    ordered = {k: data[k] for k in sorted(data.keys())}
    OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    non_null = sum(1 for v in ordered.values() if v)
    print(f"total_keys={len(ordered)} non_null={non_null} added={added} updated={updated} unresolved={len(unresolved)}")
    if unresolved:
        print("unresolved_sample=" + ", ".join(unresolved[:12]))


if __name__ == "__main__":
    main()
