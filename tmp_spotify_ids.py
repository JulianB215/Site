import re, json, urllib.parse, urllib.request
artists = [
'jul','ninho','booba','sch','damso','nekfeu','niska','lacrim','hamza','freeze corleone','lil durk','drake','lil baby','central cee','gazo','diddy','tiakola','werenoi','naps','tayc','abou debeing','lefa','koba lad','maes','soolking','alonzo','lartiste','gradur','kaaris','rohff','vald','dinos','lomepal','orelsan','bigflo et oli','soprano','sinik','sexion d\'assaut','mafia k-1 fry','the game','kendrick lamar','tyler the creator','j cole','future','lil uzi vert','travis scott','post malone','bad bunny','eminem'
]
headers = {'User-Agent':'Mozilla/5.0'}
out = {}
for a in artists:
    q = urllib.parse.quote(a)
    url = f'https://open.spotify.com/search/{q}/artists'
    req = urllib.request.Request(url, headers=headers)
    try:
        html = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except Exception:
        out[a] = None
        continue
    m = re.search(r'spotify:artist:([0-9A-Za-z]{22})', html)
    out[a] = m.group(1) if m else None
print(json.dumps(out, ensure_ascii=False, indent=2))
