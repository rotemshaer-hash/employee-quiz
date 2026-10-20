# תמלול סרטוני הדרכה לעברית: וידאו -> אודיו 16k מונו -> טקסט עם חותמות זמן
import sys, subprocess, numpy as np
from faster_whisper import WhisperModel

path, size = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'medium')
raw = subprocess.run(['ffmpeg','-v','quiet','-i',path,'-f','s16le','-ac','1','-ar','16000','-'],
                     capture_output=True).stdout
audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
print('# %s — %.1f דקות אודיו' % (path.split('/')[-1], len(audio)/16000/60), flush=True)

m = WhisperModel(size, device='cpu', compute_type='int8')
segs, info = m.transcribe(audio, language='he', vad_filter=True, beam_size=5,
                          condition_on_previous_text=False)
for s in segs:
    mm, ss = divmod(int(s.start), 60)
    # avg_logprob נמוך = המכונה לא בטוחה. מסמנים, כדי שלא נבנה שאלה על טעות תמלול.
    flag = ' «?»' if s.avg_logprob < -0.9 else ''
    print('[%02d:%02d]%s %s' % (mm, ss, flag, s.text.strip()), flush=True)
