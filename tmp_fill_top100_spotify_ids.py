import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

json_path = Path("spotify_ids.json")


def norm_key(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


artists_top_fr = [
    "jul", "ninho", "booba", "sch", "damso", "nekfeu", "orelsan", "soprano", "sexion d assaut",
    "aya nakamura", "angele", "gradur", "mac tyer", "lacrim", "sneazzy", "franglish", "alpha wann",
    "gims", "leto", "dinos", "caballero", "maes", "vald", "pnl", "ademo", "nos", "naps", "niska",
    "hamza", "freeze corleone", "gazo", "tiakola", "koba lad", "koba la d", "soolking", "heuss l enfer",
    "kaaris", "rohff", "youssoupha", "dosseh", "jok air", "lomepal", "lord esperanza", "josman",
    "13 block", "kalash criminel", "naza", "mhd", "benab", "soso maness", "zkr", "zed", "rk", "plk",
    "sdm", "werenoi", "kofs", "lefa", "black m", "hornet la frappe", "gambi", "alonzo", "hatik",
    "fianso", "sofiane", "mister you", "la fouine", "sinik", "medine", "disiz", "sultan", "lims",
    "lartiste", "genezio", "bekar", "khali", "doria", "ashkidd", "moha la squale", "niro", "zola",
    "uzi", "landy", "timal", "mister v", "kekra", "deen burbigo", "veerus", "zamdane", "lino",
    "seth gueko", "psy 4 de la rime", "sniper", "iam", "fonky family", "lunatic", "scred connexion",
    "ideal j", "kery james", "booba 92i", "kery james", "nakk mendosa", "olikainry", "salif", "arsenik",
    "passi", "stomy bugsy", "doc gyneco", "mc solaar", "ntm", "suprême ntm", "x-men"
]

seen = set()
artists = []
for a in artists_top_fr:
    k = norm_key(a)
    if k and k not in seen:
        seen.add(k)
        artists.append(k)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://open.spotify.com/",
}

if json_path.exists():
    data = json.loads(json_path.read_text(encoding="utf-8"))
else:
    data = {}

added = 0
updated = 0
failed = []

for artist in artists:
    q = urllib.parse.quote(artist)
    url = f"https://open.spotify.com/search/{q}/artists"
    req = urllib.request.Request(url, headers=headers)
    try:
        html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
    except Exception:
        failed.append(artist)
        continue

    matches = re.findall(r"spotify:artist:([0-9A-Za-z]{22})", html)
    if not matches:
        matches = re.findall(r'"/artist/([0-9A-Za-z]{22})"', html)

    artist_id = matches[0] if matches else None
    old = data.get(artist)

    if artist_id:
        if artist not in data:
            added += 1
        elif old != artist_id:
            updated += 1
        data[artist] = artist_id
    else:
        if artist not in data:
            data[artist] = None
        failed.append(artist)

ordered = {k: data[k] for k in sorted(data.keys())}
json_path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

non_null = sum(1 for v in ordered.values() if v)
print(f"total_keys={len(ordered)} non_null={non_null} added={added} updated={updated} failed={len(set(failed))}")
if failed:
    print("failed_sample=" + ", ".join(sorted(set(failed))[:15]))
