# Builds the full catalog.json from the office Dropbox set.
# usage: python3 -I gen_catalog2.py <map2.tsv> <uploaded.tsv> <out.json> <questions files...>
#   map2.tsv     vid \t relative path \t seconds
#   uploaded.tsv vid \t storage object \t size \t public url
#   questions    "# vid" / "? choice" / "* right" / "- wrong" / "?? open"
# Folder layout → category/sub-category:
#   cat/sub/file → as is;  cat/file → sub "כללי";  file at root → category "כללי", sub "כללי".
#   The office's "to be sorted" folder goes to כללי / "לשיוך".
import json, os, sys
map_path, up_path, out = sys.argv[1:4]
qfiles = sys.argv[4:]
SKIP = {'n202', 'n204', 'n253', 'n281',   # no usable speech (owner approved removing them, 18.11)
        # removed in the owner's review of the flagged videos (18.11)
        'n001', 'n008', 'n017', 'n132', 'n278', 'n279', 'n306', 'n327'}
TITLES = {   # renamed in the owner's review (18.11)
    'n103': 'תריס הגלילה החשמלי אינו נפתח במלואו',
    'n149': 'הסבר כללי לחלקי הדלת',
    'n287': 'אף מים בקופינג 4',
    'n138': 'רוחב פתח מינימלי לדלתות 3',
    'n037': 'מאריך לקופסאות ביקורת',
}
GENERAL = 'כללי'
TO_SORT = 'מיום 9.11 סרטונים לשיוך בתיקיות'

rows = [l.rstrip('\n').split('\t') for l in open(map_path, encoding='utf-8') if l.strip()]
up = {p[0]: p for p in (l.rstrip('\n').split('\t') for l in open(up_path, encoding='utf-8') if l.strip())}

questions, cur, last = {}, None, None
for qf in qfiles:
    for n, line in enumerate(open(qf, encoding='utf-8'), 1):
        line = line.strip()
        if not line: continue
        if line.startswith('# '):
            cur = line[2:].strip()
            if cur in questions: raise SystemExit('duplicate video %s in %s' % (cur, qf))
            questions[cur] = []; last = None; continue
        if line.startswith('?? '): questions[cur].append({'type': 'open', 'text': line[3:].strip()}); last = None; continue
        if line.startswith('? '):
            last = {'type': 'choice', 'text': line[2:].strip(), 'options': [], 'correct': 0}
            questions[cur].append(last); continue
        if line[:2] in ('* ', '- ') and last is not None:
            last['options'].append(line[2:].strip())
            if line[0] == '*': last['correct'] = len(last['options'])
            continue
        raise SystemExit('bad line %s:%d: %s' % (qf, n, line))
for v, lst in questions.items():
    for q in lst:
        if q['type'] == 'choice' and (q['correct'] == 0 or len(q['options']) < 3):
            raise SystemExit('bad choice question in %s: %s' % (v, q['text']))

def place(rel):
    parts = rel.split('/')
    if len(parts) == 1: return GENERAL, GENERAL, parts[0]
    if len(parts) == 2:
        if parts[0] == TO_SORT: return GENERAL, 'לשיוך', parts[1]
        return parts[0], GENERAL, parts[1]
    return parts[0], parts[1], parts[-1]

items = []
for vid, rel, sec in rows:
    if vid in SKIP: continue
    if vid not in up: raise SystemExit('not uploaded: %s %s' % (vid, rel))
    cat, sub, fname = place(rel)
    items.append((cat, sub, TITLES.get(vid) or os.path.splitext(fname)[0], vid, float(sec)))

# Categories alphabetically, "כללי" last; inside a category the same, with its own "כללי" sub last.
key = lambda name: (name == GENERAL, name)
cat_names = sorted({c for c, *_ in items}, key=key)
cats, cat_id, sub_id = {}, {}, {}
for i, c in enumerate(cat_names, 1):
    cat_id[c] = 'c%02d' % i
    cats[cat_id[c]] = {'name': c, 'order': i, 'subs': {}}
for c in cat_names:
    for j, s in enumerate(sorted({s for cc, s, *_ in items if cc == c}, key=key), 1):
        sub_id[(c, s)] = 's%03d' % (len(sub_id) + 1)
        cats[cat_id[c]]['subs'][sub_id[(c, s)]] = {'name': s, 'order': j}

videos, qs, seen = {}, {}, {}
for order, (cat, sub, title, vid, sec) in enumerate(sorted(items, key=lambda t: (key(t[0]), key(t[1]), t[2])), 1):
    k = (cat, sub, title); seen[k] = seen.get(k, 0) + 1
    if seen[k] > 1: title += ' (%d)' % seen[k]
    _, obj, _, url = up[vid]
    videos[vid] = {'cat': cat_id[cat], 'sub': sub_id[(cat, sub)], 'title': title, 'url': url, 'path': obj,
                   'duration': round(sec), 'order': order}
    for i, q in enumerate(questions.get(vid, [])):
        o = {'video': vid, 'type': q['type'], 'text': q['text'], 'order': i + 1}
        if q['type'] == 'choice': o['options'] = q['options']; o['correct'] = q['correct']
        qs['%sq%d' % (vid, i + 1)] = o

json.dump({'cats': cats, 'videos': videos, 'questions': qs}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
missing = sorted(v for v in videos if v not in questions)
extra = sorted(v for v in questions if v not in videos)
print('cats', len(cats), 'subs', len(sub_id), 'videos', len(videos), 'questions', len(qs))
print('videos without questions:', len(missing))
if extra: print('questions for unknown videos:', extra)
