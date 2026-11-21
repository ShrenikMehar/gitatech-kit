"""Dialogue voices -> <episode>/data/narration.wav + <episode>/timeline.json
(lines with start/end, real per-word times, and a per-frame mouth track 0/1/2).

  python3 voices.py <episode_dir>

Default engine: Microsoft neural voices through edge-tts (natural Hindi + English, real word timings).
The chosen voice: one Hindi male voice (hi-IN-MadhurNeural) for both, Arjun faster/higher, Krishna a bit deeper.
Per character in script.json "voices": {"engine": "edge", "name": "...", "rate": "+12%", "pitch": "+18Hz"}.
Per line overrides: "rate", "pitch". Write English tech words in Latin letters inside `say` so they're said as English.
Long pauses inside a line are shortened to "max_pause" seconds (script top level, default 0.32).
Fallback engine "kokoro" (offline) is kept for when the network is unavailable: {"engine": "kokoro", "name": "hm_omega", "speed": 0.92}.
"""
import asyncio, json, os, re, subprocess, sys, wave
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import clean_say, spread_words, tokens

E = Path(sys.argv[1]); (E / 'data').mkdir(parents=True, exist_ok=True)
S = json.loads((E / 'script.json').read_text()); SR = 24000; FPS = S['fps']
MAXP = S.get('max_pause', 0.32)
DEFAULT = {'krishna': {'engine': 'edge', 'name': 'hi-IN-MadhurNeural', 'rate': '+4%', 'pitch': '-6Hz'},
           'arjun': {'engine': 'edge', 'name': 'hi-IN-MadhurNeural', 'rate': '+12%', 'pitch': '+18Hz'}}


def decode(mp3_bytes):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'pipe:0', '-f', 'f32le', '-ac', '1', '-ar', str(SR), 'pipe:1'],
                       input=mp3_bytes, capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).astype(np.float64)


async def _edge(text, voice, rate, pitch):
    import edge_tts
    proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    for attempt in range(4):
        try:
            c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, proxy=proxy, boundary='WordBoundary')
            audio, words = b'', []
            async for ch in c.stream():
                if ch['type'] == 'audio':
                    audio += ch['data']
                elif ch['type'] == 'WordBoundary':
                    words.append({'w': ch['text'], 's': ch['offset']/1e7, 'e': (ch['offset'] + ch['duration'])/1e7})
            if len(audio) > 2000:
                return audio, words
        except Exception as ex:
            print('  edge-tts retry:', ex, flush=True)
        await asyncio.sleep(2 + attempt*2)
    raise RuntimeError('edge-tts gave no audio (network?). Set "engine": "kokoro" for an offline fallback.')


def squeeze(a, words):
    """Shorten silences longer than MAXP inside the clip; shift word times to match."""
    hop = SR // 100
    n = len(a) // hop
    env = np.sqrt(np.mean(a[:n*hop].reshape(n, hop)**2, axis=1))
    quiet = env < 0.012 * (env.max() + 1e-9) * 3
    keep = np.ones(len(a), bool)
    cuts = []  # (time_in_original, removed_seconds)
    i = 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            dur = (j - i)/100
            if dur > MAXP and i > 0 and j < n:
                rm = dur - MAXP
                a0 = int((i/100 + MAXP/2)*SR); a1 = a0 + int(rm*SR)
                keep[a0:a1] = False
                cuts.append((i/100 + MAXP/2, rm))
            i = j
        else:
            i += 1
    def shift(t):
        return t - sum(rm for (tc, rm) in cuts if tc < t)
    return a[keep], [{**w, 's': shift(w['s']), 'e': shift(w['e'])} for w in words]


def say_edge(text, v, ln):
    audio, words = asyncio.run(_edge(text, v['name'], ln.get('rate', v.get('rate', '+0%')), ln.get('pitch', v.get('pitch', '+0Hz'))))
    a = decode(audio)
    idx = np.where(np.abs(a) > 0.01*np.abs(a).max())[0]
    t0 = max(0, idx[0] - 120); a = a[t0: idx[-1] + 600]
    words = [{**w, 's': max(0.0, w['s'] - t0/SR), 'e': max(0.0, w['e'] - t0/SR)} for w in words]
    return squeeze(a, words)


_K = None


def say_kokoro(text, v, ln):
    global _K
    import urllib.request
    from kokoro_onnx import Kokoro
    KD = Path(os.environ.get('KOKORO_DIR', Path.home()/'.reelgen'/'kokoro')); KD.mkdir(parents=True, exist_ok=True)
    URL = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'
    for f in ('kokoro-v1.0.onnx', 'voices-v1.0.bin'):
        if not (KD/f).exists():
            print('downloading', f, '(once)...', flush=True)
            urllib.request.urlretrieve(URL + f, KD/(f + '.part')); (KD/(f + '.part')).rename(KD/f)
    if _K is None:
        _K = Kokoro(str(KD/'kokoro-v1.0.onnx'), str(KD/'voices-v1.0.bin'))
    ph = re.sub(r'\([a-z-]+\)', '', _K.tokenizer.phonemize(text, 'hi'))
    a, _ = _K.create(ph, voice=v['name'], speed=ln.get('speed', v.get('speed', 1.0)), lang='hi', is_phonemes=True)
    a = np.asarray(a, np.float64); idx = np.where(np.abs(a) > 0.01*np.abs(a).max())[0]
    a = a[max(0, idx[0] - 120): idx[-1] + 600]
    return a, None


out, t, lines, prev = [np.zeros(int(S['lead']*SR))], S['lead'], [], None
for ln in S['lines']:
    v = {**DEFAULT.get(ln['who'], DEFAULT['krishna']), **S.get('voices', {}).get(ln['who'], {})}
    if v.get('engine', 'edge') == 'edge' and str(v.get('name', '')).startswith(('hm_', 'am_', 'af_', 'bm_', 'bf_')):
        v = {**v, 'engine': 'kokoro'}
    if prev is not None:
        g = ln.get('gap_before', 0.5 if prev['who'] != ln['who'] else 0.24) + prev.get('gap', 0)
        out.append(np.zeros(int(g*SR))); t += g
    text = clean_say(ln['say'])
    a, ws = (say_edge if v.get('engine', 'edge') == 'edge' else say_kokoro)(text, v, ln)
    a = a/(np.abs(a).max() + 1e-9)*(0.92 if ln['who'] == 'arjun' else 0.88)
    s, e = t, t + len(a)/SR
    if ws:
        words = [{'w': w['w'], 's': round(s + w['s'], 3), 'e': round(s + w['e'], 3)} for w in ws]
    else:
        words = [{'w': w['w'], 's': w['s'], 'e': w['e']} for w in spread_words(tokens(ln['say']), 0, s, e)]
    hop = SR//FPS; n = len(a)//hop
    env = np.sqrt(np.mean(a[: n*hop].reshape(n, hop)**2, axis=1))
    lines.append({**ln, 's': round(s, 3), 'e': round(e, 3), 'env': env.tolist(), 'words': words})
    print(f"{ln['id']:4s} {ln['who']:8s} {s:6.2f}-{e:6.2f}  {ln['cap']}")
    print('      ' + ' '.join(f"{i}:{w['w']}@{w['s']:.2f}" for i, w in enumerate(words)))
    out.append(a); t = e; prev = ln
out.append(np.zeros(int(S['outro']*SR)))
y = np.concatenate(out); dur = len(y)/SR
with wave.open(str(E/'data/narration.wav'), 'wb') as wv:
    wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((np.clip(y, -1, 1)*32767).astype('<i2').tobytes())
# mouth track: 0 closed, 1 half, 2 open, per video frame, held >= 2 frames so it never flickers
nf = int(np.ceil(dur*FPS)); mouth = [0]*nf; who = [None]*nf
for Ln in lines:
    env = np.array(Ln['env']); ref = np.percentile(env[env > 1e-4], 92) + 1e-9; env = env/ref
    f0 = int(round(Ln['s']*FPS)); last, hold = 0, 9
    for i, val in enumerate(env):
        lvl = 0 if val < 0.13 else (1 if val < 0.5 else 2)
        if lvl != last and hold < 2:
            lvl = last
        hold = hold + 1 if lvl == last else 0; last = lvl
        if f0 + i < nf:
            mouth[f0 + i] = lvl; who[f0 + i] = Ln['who']
    del Ln['env']
json.dump({'fps': FPS, 'duration': round(dur, 3), 'lines': lines, 'mouth': mouth, 'who': who}, open(E/'timeline.json', 'w'), ensure_ascii=False)
print(f'duration {dur:.2f}s, {nf} frames')
