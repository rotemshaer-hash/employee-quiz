# Builds catalog.json: categories / sub-categories from the zip folder names,
# videos from map.tsv + durations.txt, questions from questions.json (written by hand from transcripts).
import json, os, sys
base, qfile, out = sys.argv[1], sys.argv[2], sys.argv[3]

dur = {}
for line in open(os.path.join(base, 'durations.txt'), encoding='utf-8'):
    d, _, path = line.rstrip('\n').split('|', 2)
    dur[path[len('raw/'):]] = round(float(d))

SKIP = {'v15'}  # same speech as v14 (the .mp4 copy of the .MOV)
rows = [r for r in (l.rstrip('\n').split('\t') for l in open(os.path.join(base, 'map.tsv'), encoding='utf-8') if l.strip()) if r[0] not in SKIP]
# questions.txt: "# v01" starts a video, "? text" choice, "* right", "- wrong", "?? text" open.
questions, cur, last = {}, None, None
for n, line in enumerate(open(qfile, encoding='utf-8'), 1):
    line = line.strip()
    if not line: continue
    if line.startswith('# '): cur = line[2:].strip(); questions[cur] = []; continue
    if line.startswith('?? '): questions[cur].append({'type': 'open', 'text': line[3:].strip()}); last = None; continue
    if line.startswith('? '):
        last = {'type': 'choice', 'text': line[2:].strip(), 'options': [], 'correct': 0}
        questions[cur].append(last); continue
    if line[:2] in ('* ', '- ') and last is not None:
        last['options'].append(line[2:].strip())
        if line[0] == '*': last['correct'] = len(last['options'])
        continue
    raise SystemExit('bad line %d: %s' % (n, line))
for v, lst in questions.items():
    for q in lst:
        if q['type'] == 'choice' and (q['correct'] == 0 or len(q['options']) < 3):
            raise SystemExit('bad choice question in %s: %s' % (v, q['text']))

cats, videos, qs = {}, {}, {}
cat_ids, sub_ids = {}, {}
seen_titles = {}
for vid, rel in rows:
    cat, sub, fname = rel.split('/')
    if cat not in cat_ids:
        cat_ids[cat] = 'c%02d' % (len(cat_ids) + 1)
        cats[cat_ids[cat]] = {'name': cat, 'order': len(cat_ids), 'subs': {}}
    cid = cat_ids[cat]
    if (cat, sub) not in sub_ids:
        sub_ids[(cat, sub)] = 's%02d' % (len(sub_ids) + 1)
        cats[cid]['subs'][sub_ids[(cat, sub)]] = {'name': sub, 'order': len(cats[cid]['subs']) + 1}
    sid = sub_ids[(cat, sub)]
    title = os.path.splitext(fname)[0]
    key = (cid, sid, title)
    seen_titles[key] = seen_titles.get(key, 0) + 1
    if seen_titles[key] > 1: title += ' (%d)' % seen_titles[key]
    videos[vid] = {'cat': cid, 'sub': sid, 'title': title, 'url': 'videos/%s.mp4' % vid,
                   'duration': dur[rel], 'order': int(vid[1:])}
    for i, q in enumerate(questions.get(vid, [])):
        o = {'video': vid, 'type': q['type'], 'text': q['text'], 'order': i + 1}
        if q['type'] == 'choice':
            o['options'] = q['options']; o['correct'] = q['correct']
            assert 1 <= q['correct'] <= len(q['options']), (vid, q)
        qs['%sq%d' % (vid, i + 1)] = o

json.dump({'cats': cats, 'videos': videos, 'questions': qs}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
missing = [v for v, _ in rows if v not in questions]
print('cats', len(cats), 'subs', len(sub_ids), 'videos', len(videos), 'questions', len(qs), 'videos without questions:', missing)
