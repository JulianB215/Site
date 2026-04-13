import json, urllib.request, urllib.parse
headers={'User-Agent':'Mozilla/5.0'}
req=urllib.request.Request('https://open.spotify.com/get_access_token?reason=transport&productType=web_player',headers=headers)
raw=urllib.request.urlopen(req,timeout=20).read().decode('utf-8','ignore')
obj=json.loads(raw)
print('hasToken', bool(obj.get('accessToken')))
print('len', len(obj.get('accessToken','')))
print('type', obj.get('accessTokenExpirationTimestampMs'))
