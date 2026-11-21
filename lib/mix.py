"""Final audio: narration + music bed + sound effects, ducked and loudness-normalised -> data/mix.wav

  python tools/mix.py <project>
  python tools/mix.py --demo out_folder      write every built-in bed and effect as WAVs to listen to

script.json "music": {"bed": "tanpura" | "pad" | "none" | "input/your_track.mp3", "gain": -21}
Effects come from data/cues.json (run `node tools/render.mjs <project> cues` first): [{t, name, gain}].
Built-in effects: whoosh, swell, pop, hit, glitch, tick, bowl, riser, chime, train. Everything is synthesised here, so there is
nothing to license. Music ducks about 8 dB under the voice; the mix is normalised to -14 LUFS for Reels/Shorts.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import die, load_audio, load_json, project, write_wav  # noqa: E402

SR = 48000
RNG = np.random.default_rng(7)


def db(g):
    return 10 ** (g / 20)


def env_ad(n, a, d_curve):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    return e * d_curve


def onepole_lp(x, fc):
    """One-pole low-pass with a cutoff that may change per sample (fc array or scalar)."""
    fc = np.broadcast_to(np.asarray(fc, dtype=np.float64), x.shape)
    k = 1 - np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s += k[i] * (x[i] - s)
        y[i] = s
    return y


# ---------------- music beds ----------------
def tanpura_pluck(f0, dur=4.6, seed=0):
    r = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros_like(t)
    for n in range(1, 26):
        f = n * f0 * (1 + 0.00025 * n * n)
        if f > 9000:
            break
        amp = n ** -0.85
        # jawari: upper partials swell after the pluck and shimmer, which is what makes a tanpura buzz
        if 5 <= n <= 18:
            amp *= 0.35 + 0.9 * (1 - np.exp(-t / 0.35)) * np.exp(-t / 2.4) * (1 + 0.25 * np.sin(2 * np.pi * (0.8 + 0.07 * n) * t))
        decay = np.exp(-t * (0.32 + 0.045 * n))
        y += amp * decay * np.sin(2 * np.pi * f * t + r.uniform(0, 2 * np.pi))
    y *= np.minimum(1, t / 0.006)
    return y / (np.abs(y).max() + 1e-9)


def bed_tanpura(dur, sa=138.59):
    """Pa (lower), Sa, Sa, Sa (lower octave), one pluck a second, looping: the classic drone."""
    n = int(dur * SR) + SR * 5
    L, R = np.zeros(n), np.zeros(n)
    notes = [sa * 0.749, sa, sa, sa / 2]
    plucks = [tanpura_pluck(f, seed=k) for k, f in enumerate(notes)]
    t, k = 0.0, 0
    while t < dur + 1:
        p = plucks[k % 4] * (0.9 if k % 4 != 3 else 1.0)
        i = int(t * SR)
        pan = [-0.25, 0.15, 0.3, -0.1][k % 4]
        L[i:i + len(p)] += p[: n - i] * (1 - pan) * 0.5
        R[i:i + len(p)] += p[: n - i] * (1 + pan) * 0.5
        t += 1.05 if k % 4 != 3 else 1.6
        k += 1
    tt = np.arange(n) / SR  # a soft low pad under the plucks
    pad = 0.18 * (np.sin(2 * np.pi * sa / 2 * tt) + 0.6 * np.sin(2 * np.pi * sa * 0.749 * tt + 1)) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * tt))
    out = np.stack([L + pad, R + pad * 0.97], axis=1)[: int(dur * SR)]
    return out / (np.abs(out).max() + 1e-9)


def bed_pad(dur, root=110.0):
    """Warm, slow two-chord pad for non-devotional videos."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    chords = [[1, 1.26, 1.5, 2], [0.89, 1.12, 1.33, 1.78]]
    y = np.zeros((n, 2))
    seg = 6.0
    for ci in range(int(dur / seg) + 2):
        ch = chords[ci % 2]
        a, b = int(ci * seg * SR), int((ci * seg + seg + 2) * SR)
        if a >= n:
            break
        b = min(b, n)
        tt = t[a:b] - ci * seg
        e = np.minimum(1, tt / 1.5) * np.minimum(1, np.maximum(0, (seg + 2 - tt) / 2))
        for k, r in enumerate(ch):
            for det, side in ((0.997, 0), (1.003, 1)):
                y[a:b, side] += e * np.sin(2 * np.pi * root * r * det * tt + k) * (0.5 if k else 0.8)
    return y / (np.abs(y).max() + 1e-9)


# ---------------- effects ----------------
def fx(name, seed=0):
    r = np.random.default_rng(seed)
    if name == "whoosh":
        n = int(0.5 * SR); t = np.arange(n) / SR
        e = np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 2
        y = onepole_lp(r.standard_normal(n), 300 + 4500 * e) - onepole_lp(r.standard_normal(n), 120) * 0.3
        return y * e
    if name == "swell":
        n = int(0.7 * SR); t = np.arange(n) / SR
        e = (t / 0.7) ** 2
        return onepole_lp(r.standard_normal(n), 200 + 2500 * e) * e + 0.3 * np.sin(2 * np.pi * (90 + 60 * t) * t) * e
    if name == "pop":
        n = int(0.12 * SR); t = np.arange(n) / SR
        f = 520 * np.exp(-t * 18) + 240
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32)
    if name == "hit":
        n = int(0.5 * SR); t = np.arange(n) / SR
        f = 45 + 70 * np.exp(-t * 25)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) + onepole_lp(r.standard_normal(n), 900) * np.exp(-t * 40) * 0.6
    if name == "glitch":
        n = int(0.35 * SR); t = np.arange(n) / SR
        gate = (np.floor(t * 38) % 3 != 0).astype(float)
        sq = np.sign(np.sin(2 * np.pi * (110 + 400 * r.random()) * t))
        crush = np.round(r.standard_normal(n) * 3) / 3
        return (0.6 * sq + 0.4 * onepole_lp(crush, 2500)) * gate * np.exp(-t * 4)
    if name == "tick":
        n = int(0.03 * SR); t = np.arange(n) / SR
        return onepole_lp(r.standard_normal(n), 3000) * np.exp(-t * 300)
    if name == "bowl":
        n = int(3.5 * SR); t = np.arange(n) / SR; f = 196.0
        y = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * d) for m, a, d in ((1, 1, 0.9), (1.004, 0.8, 0.9), (2.71, 0.35, 1.6), (5.2, 0.12, 2.6)))
        return y * np.minimum(1, t / 0.01)
    if name == "chime":
        # station announcement jingle: three soft bell notes rising, then a fourth
        n = int(2.4 * SR); t = np.arange(n) / SR; y = np.zeros(n)
        for t0, f in ((0.0, 659.25), (0.26, 830.61), (0.52, 987.77), (0.92, 1318.5)):
            tt = np.clip(t - t0, 0, None); on = (t >= t0).astype(float)
            y += on * sum(a * np.sin(2 * np.pi * f * m * tt) * np.exp(-tt * d) for m, a, d in ((1, 1, 2.2), (2.0, 0.28, 4.5), (3.01, 0.1, 7)))
        return y * np.minimum(1, t / 0.005)
    if name == "train":
        # train pulling in: rumble with wheel clacks that slow down, then brakes; a two-tone horn at the start
        n = int(3.6 * SR); t = np.arange(n) / SR
        env = np.minimum(1, t / 0.6) * np.clip((3.6 - t) / 0.8, 0, 1)
        y = onepole_lp(r.standard_normal(n), 160) * 2.2 * env
        tc, period = 0.15, 0.16
        while tc < 3.0:
            for dt in (0.0, 0.07):
                i = int((tc + dt) * SR); m = min(n - i, int(0.06 * SR))
                if m > 0:
                    tt = np.arange(m) / SR
                    y[i:i + m] += 0.9 * np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 60) * env[i]
            tc += period; period *= 1.09
        hn = int(0.9 * SR); th = np.arange(hn) / SR
        he = np.minimum(1, th / 0.05) * np.clip((0.9 - th) / 0.25, 0, 1)
        horn = sum(a * np.sign(np.sin(2 * np.pi * f * th)) for f, a in ((311.1, 0.5), (370.0, 0.4)))
        y[:hn] += onepole_lp(horn, 1400) * he * 0.9
        br = np.clip((t - 2.3) / 0.3, 0, 1) * np.clip((3.4 - t) / 0.4, 0, 1)
        y += np.sin(2 * np.pi * (2100 + 80 * np.sin(t * 9)) * t) * 0.05 * br
        return y
    if name == "riser":
        n = int(1.2 * SR); t = np.arange(n) / SR
        e = (t / 1.2) ** 2.2
        return (onepole_lp(r.standard_normal(n), 300 + 5000 * e) * 0.7 + 0.4 * np.sin(2 * np.pi * np.cumsum(200 + 500 * e) / SR)) * e
    return None


def normalise(x):
    return x / (np.abs(x).max() + 1e-9)


def demo(folder):
    out = Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    write_wav(out / "bed_tanpura.wav", bed_tanpura(12) * 0.8, SR)
    write_wav(out / "bed_pad.wav", bed_pad(12) * 0.8, SR)
    for name in ["whoosh", "swell", "pop", "hit", "glitch", "tick", "bowl", "riser", "chime", "train"]:
        write_wav(out / f"fx_{name}.wav", normalise(fx(name)) * 0.8, SR)
    print(f"wrote beds and effects to {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?")
    ap.add_argument("--demo")
    a = ap.parse_args()
    if a.demo:
        return demo(a.demo)
    if not a.project:
        ap.error("project folder missing")
    P, S = project(a.project)
    voice = load_audio(P / "data/narration.wav", SR)
    n = len(voice)
    dur = n / SR
    mix = np.stack([voice, voice], axis=1)

    m = S.get("music", {"bed": "none"})
    bed = m.get("bed", "none")
    if bed != "none":
        if bed == "tanpura":
            music = bed_tanpura(dur, float(m.get("sa", 138.59)))
        elif bed == "pad":
            music = bed_pad(dur)
        else:
            f = (P / bed) if not Path(bed).is_absolute() else Path(bed)
            if not f.exists():
                die(f"music file not found: {f}")
            music = load_audio(f, SR, 2)
            reps = int(np.ceil(n / len(music)))
            music = np.tile(music, (reps, 1))[:n]
            music = music / (np.abs(music).max() + 1e-9)
        music = music[:n]
        if len(music) < n:   # beds can come out a sample short of the narration
            music = np.pad(music, ((0, n - len(music)), (0, 0)))
        # duck under the voice: smoothed voice envelope pushes the music down ~8 dB
        hop = SR // 100
        r = np.sqrt(np.mean(voice[: (n // hop) * hop].reshape(-1, hop) ** 2, axis=1))
        sp = (r > np.percentile(r, 95) * 0.1).astype(float)
        sm, prev = np.empty_like(sp), 0.0
        for i, v in enumerate(sp):
            prev = prev + (v - prev) * (0.35 if v > prev else 0.04)
            sm[i] = prev
        duck = np.interp(np.arange(n) / hop, np.arange(len(sm)), sm)
        g = db(float(m.get("gain", -21))) * (1 - 0.6 * duck)
        fade = np.minimum(1, np.arange(n) / (0.8 * SR)) * np.minimum(1, (n - np.arange(n)) / (1.5 * SR))
        mix += music * (g * fade)[:, None]

    cues = load_json(P / "data/cues.json", [])
    for k, c in enumerate(cues):
        y = fx(c["name"], seed=k)
        if y is None:
            f = P / c["name"]
            if not f.exists():
                print(f"warning: unknown effect {c['name']}")
                continue
            y = load_audio(f, SR)
        y = normalise(y) * db(float(c.get("gain", -10)))
        i = int(float(c["t"]) * SR)
        if i >= n:
            continue
        seg = y[: n - i]
        mix[i:i + len(seg)] += seg[:, None]

    raw = P / "data/mix_raw.wav"
    write_wav(raw, mix / (np.abs(mix).max() + 1e-9) * 0.9, SR)
    lufs = float(S.get("loudness", -14))
    p = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11", "-ar", str(SR), str(P / "data/mix.wav")],
                       capture_output=True, text=True)
    if p.returncode:
        die(p.stderr[-500:])
    raw.unlink(missing_ok=True)
    print(f"data/mix.wav ({dur:.2f} s, music: {bed}, {len(cues)} effects, {lufs} LUFS)")


if __name__ == "__main__":
    main()
