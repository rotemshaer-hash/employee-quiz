# Uploads every video in map2.tsv to Firebase Storage as videos/lib-<vid>.mp4 using a temporary user,
# skipping files already there with the same size. Writes uploaded.tsv (vid, object, size, url).
# usage: python3 -I storage_upload.py <cred.json> <map2.tsv> <webdir> <out.tsv>
import sys, json, os, time, urllib.request, urllib.error, urllib.parse
KEY = 'AIzaSyC8LImUbMynjKvs2Nr2DCbqlgKxtSqJ_as'
BUCKET = 'employee-quiz-81499.firebasestorage.app'
BASE = 'https://firebasestorage.googleapis.com/v0/b/%s/o' % BUCKET
cred_path, map_path, web, out_path = sys.argv[1:5]
cred = json.load(open(cred_path))
tok = {'id': cred['idToken'], 'at': time.time()}

def refresh():
    data = urllib.parse.urlencode({'grant_type': 'refresh_token', 'refresh_token': cred['refreshToken']}).encode()
    r = json.load(urllib.request.urlopen('https://securetoken.googleapis.com/v1/token?key=' + KEY, data=data, timeout=30))
    tok['id'], tok['at'] = r['id_token'], time.time()

def remote_size(name):
    try:
        r = json.load(urllib.request.urlopen(BASE + '/' + urllib.parse.quote(name, safe=''), timeout=30))
        return int(r.get('size', -1))
    except urllib.error.HTTPError as e:
        if e.code == 404: return None
        raise

done = {}
if os.path.exists(out_path):
    for l in open(out_path):
        p = l.rstrip('\n').split('\t')
        if len(p) == 4: done[p[0]] = p
out = open(out_path, 'a')
rows = [l.rstrip('\n').split('\t') for l in open(map_path) if l.strip()]
ok = fail = 0
for vid, rel, *_ in rows:
    if vid in done: ok += 1; continue
    path = os.path.join(web, rel)
    if not os.path.exists(path): print('MISSING', vid, rel, flush=True); fail += 1; continue
    size = os.path.getsize(path); name = 'videos/lib-%s.mp4' % vid
    url = BASE + '/' + urllib.parse.quote(name, safe='') + '?alt=media'
    if remote_size(name) == size:
        out.write('\t'.join([vid, name, str(size), url]) + '\n'); out.flush(); ok += 1; continue
    for attempt in range(4):
        if time.time() - tok['at'] > 45 * 60: refresh()
        try:
            with open(path, 'rb') as f:
                req = urllib.request.Request(BASE + '?name=' + urllib.parse.quote(name, safe=''), data=f, method='POST',
                    headers={'Authorization': 'Firebase ' + tok['id'], 'Content-Type': 'video/mp4', 'Content-Length': str(size)})
                r = json.load(urllib.request.urlopen(req, timeout=600))
            if int(r.get('size', -1)) != size: raise RuntimeError('size mismatch %s' % r.get('size'))
            out.write('\t'.join([vid, name, str(size), url]) + '\n'); out.flush(); ok += 1
            print('OK', vid, '%.1fMB' % (size / 1e6), flush=True); break
        except Exception as e:
            print('RETRY', vid, attempt, str(e)[:200], flush=True); time.sleep(5 * (attempt + 1))
    else:
        fail += 1; print('FAILED', vid, rel, flush=True)
print('DONE ok', ok, 'fail', fail, flush=True)
