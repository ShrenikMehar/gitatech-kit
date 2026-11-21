"""Shared helpers for the reelgen tools (standard library + numpy only)."""
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np

HOME = Path(os.environ.get("REELGEN_HOME", Path.home() / ".reelgen"))


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(p, default=None):
    p = Path(p)
    if not p.exists():
        if default is not None:
            return default
        die(f"missing {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p, obj, indent=1):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=indent), encoding="utf-8")


def clean_say(text):
    """Script text without the caption markup (| chunk breaks, *emphasis)."""
    return re.sub(r"\s+", " ", text.replace("|", " ").replace("*", "")).strip()


def tokens(text):
    return [w for w in clean_say(text).split(" ") if norm(w)]


def norm(w):
    """Comparable form of a word in any script: NFC, lowercase, no punctuation, no nukta, candrabindu -> anusvara."""
    w = unicodedata.normalize("NFC", w).lower().replace("़", "").replace("ँ", "ं")
    return "".join(ch for ch in w if unicodedata.category(ch)[0] in "LMN")


def weight(w):
    """Roughly how long a word takes to say. Devanagari letters count 1, vowel signs 0.5, the virama 0,
    Latin letters 0.55 (about half a syllable), digits 1.2, plus 1 per word. Same formula as engine/runtime.js."""
    n = 0.0
    for ch in w:
        cat = unicodedata.category(ch)
        if "ऀ" <= ch <= "ॿ":
            n += 0 if ch == "्" else (0.5 if cat[0] == "M" else 1.0)
        elif cat[0] == "L":
            n += 0.55
        elif cat[0] == "N":
            n += 1.2
    return n + 1.0


def pause_after(w):
    """Extra weight for the pause a punctuation mark adds after a word."""
    if re.search(r"[.?!।॥]$", w):
        return 2.5
    if re.search(r"[,;:—-]$", w):
        return 1.2
    return 0.0


def spread_words(toks, line_idx, s, e):
    """Place a line's words inside [s, e] by weight, with pauses at punctuation."""
    wts = [weight(w) for w in toks]
    gaps = [pause_after(w) if k < len(toks) - 1 else 0.0 for k, w in enumerate(toks)]
    tot = sum(wts) + sum(gaps)
    out, c = [], s
    for w, wt, g in zip(toks, wts, gaps):
        d = (e - s) * wt / tot
        out.append({"w": w, "line": line_idx, "s": round(c, 3), "e": round(c + d * 0.92, 3)})
        c += d + (e - s) * g / tot
    return out


def load_audio(path, sr=24000, ch=1):
    """Decode any audio file with ffmpeg into float32 [samples] (mono) or [samples, ch]."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", str(ch), "-ar", str(sr), "-"],
                       capture_output=True)
    if p.returncode:
        die(f"ffmpeg could not read {path}: {p.stderr.decode()[-400:]}")
    x = np.frombuffer(p.stdout, dtype=np.float32).copy()
    return x if ch == 1 else x.reshape(-1, ch)


def write_wav(path, x, sr):
    """Write float audio ([n] or [n, ch]) as 16-bit PCM WAV."""
    import wave
    x = np.asarray(x, dtype=np.float64)
    ch = 1 if x.ndim == 1 else x.shape[1]
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def rms_frames(x, sr, hop_s=0.01):
    hop = max(1, int(sr * hop_s))
    n = len(x) // hop
    if n == 0:
        return np.zeros(0)
    return np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))


def project(path):
    P = Path(path).resolve()
    if not (P / "script.json").exists():
        die(f"no script.json in {P}")
    return P, load_json(P / "script.json")
