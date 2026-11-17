# Same logic as tools/transcribe.py, but loads the model once for many files.
import sys, os, subprocess, numpy as np
from faster_whisper import WhisperModel
root, outdir, size = sys.argv[1], sys.argv[2], sys.argv[3]
m = WhisperModel(size, device='cpu', compute_type='int8', cpu_threads=3)
files = sorted(os.path.join(d, f) for d, _, fs in os.walk(root) for f in fs)
for path in files:
    rel = os.path.relpath(path, root)
    out = os.path.join(outdir, os.path.splitext(rel)[0] + '.txt')
    if os.path.exists(out): continue
    os.makedirs(os.path.dirname(out), exist_ok=True)
    raw = subprocess.run(['ffmpeg','-v','quiet','-i',path,'-f','s16le','-ac','1','-ar','16000','-'], capture_output=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    segs, info = m.transcribe(audio, language='he', vad_filter=True, beam_size=5, condition_on_previous_text=False)
    lines = []
    for s in segs:
        mm, ss = divmod(int(s.start), 60)
        flag = ' «?»' if s.avg_logprob < -0.9 else ''
        lines.append('[%02d:%02d]%s %s' % (mm, ss, flag, s.text.strip()))
    with open(out + '.tmp', 'w') as f: f.write('\n'.join(lines) + '\n')
    os.rename(out + '.tmp', out)
    print('done', rel, flush=True)
print('ALL DONE', flush=True)
