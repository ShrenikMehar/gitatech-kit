"""Episode runtime: everything a driver needs that is not the story.

Every past episode copied ~300 lines of the same plumbing (timeline loading, busts with life motion, close-ups,
captions, the render loop). It lives here now, so a driver only holds its beats, shots, world state and cues.

    import episode as E                  # after putting $GT/lib on sys.path (see starter/ep.py)
    E.setup(page_at={'L2': 5}, emph={'L1': [2]})
    T_X = E.w('L3', 4)                   # start time of word 4 of line L3
    ...
    E.run(frame, cues)                   # CLI: --still t.. | --cues | --range a b | --workers n | --out f

Timeline: $GT_EP/timeline.json (written by voices.py). Every frame must be a pure function of t.
"""
import argparse
import json
import math
import os
import re
import subprocess
from collections import OrderedDict
import multiprocessing as mp

import skia

import chars
import gt as K
import world as Wd
from gt import back_out, bottom_fade, bump, card, draw_deva, ease_out, ramp
from iso import P, SP, blurred, ca, glow, hexc

W, H = 1080, 1920
EP = os.environ.get('GT_EP', os.getcwd())
TL = json.load(open(f'{EP}/timeline.json'))
for _l in TL['lines']:
    _l['cap'] = re.sub(r'\*([^*]+)\*([,.…!?]+)', r'*\1\2*', _l['cap'])   # keep trailing punctuation inside emphasis
L = {l['id']: l for l in TL['lines']}
ORDER = [l['id'] for l in TL['lines']]
DUR = TL['duration']
FPS = TL['fps']
EMPH_T = []
GAPS = []
for _l in TL['lines']:
    for _a, _b in zip(_l['words'], _l['words'][1:]):
        if _b['s'] - _a['e'] > 0.2:
            GAPS.append((_a['e'] + 0.04, _b['s'] + 0.08))


def setup(page_at=None, emph=None):
    """page_at: {line_id: audio word index where caption page 2 starts} (lines whose cap has a '|').
    emph: {line_id: [word indices]} that get a nod + brow lift in close-ups and standing busts."""
    K.PAGE_AT = dict(page_at or {})
    EMPH_T[:] = sorted(w(lid, i) for lid, ix in (emph or {}).items() for i in ix)


# ----------------------------------------------------------------------------- timing
def w(lid, i):
    """Start time of audio word i in line lid (indices as printed by voices.py)."""
    return L[lid]['words'][i]['s']


def we(lid, i):
    return L[lid]['words'][i]['e']


def cut(a, b):
    """A shot boundary between line a and the next line b."""
    return max(L[a]['e'] + 0.05, L[b]['s'] - 0.18)


def plate(t, a, b, f=0.12):
    """1 between a and b, with f-second fades: for things that appear and leave."""
    return ramp(t, a, f)*(1 - ramp(t, b - f, f))


def lerp_cam(a, b, k):
    """Blend two flat 2D camera tuples (scale, focus_x, focus_y, screen_y), or any equal-length number tuples.
    For isometric iso.Cam keyframes use gt.cam_lerp instead."""
    return tuple(x + (y - x)*k for x, y in zip(a, b))


def shot_at(t, shots):
    """shots: [(start, kind, key)] sorted. Returns ((start, kind, key), next_start)."""
    cur, nxt = shots[0], DUR
    for i, s_ in enumerate(shots):
        if t >= s_[0]:
            cur, nxt = s_, (shots[i + 1][0] if i + 1 < len(shots) else DUR)
    return cur, nxt


# ----------------------------------------------------------------------------- characters
EB = {'krishna': 'raise', 'krishna_knowing': 'raise', 'krishna_smile': 'raise', 'arjun_curious': 'raise', 'arjun_worried': 'panic',
      'arjun_relief': 'raise', 'arjun_panic': 'panic', 'arjun_determined': 'angry', 'arjun_sheepish': 'raise', 'arjun_frustrated': 'angry'}
_BC = OrderedDict()


def bust(key, mouth_i=0, blink=0, brow_on=False, gaze=None):
    """Rendered bust image for an expression key in gt.BASE (krishna, krishna_smile, krishna_knowing, arjun_panic/worried/
    curious/relief/frustrated/sheepish/determined). LRU-cached. Add new keys to gt.BASE/MOUTHS (and chars.EXPR) first."""
    k = (key, mouth_i, blink, brow_on, gaze)
    if k in _BC:
        _BC.move_to_end(k)
        return _BC[k]
    who, base = K.BASE[key]
    e = dict(base)
    e['mouth'] = K.MOUTHS[key][mouth_i]
    if brow_on and EB.get(key):
        e['brow'] = EB[key]
        e['eye'] = e.get('eye', 1.0)*1.07
    if gaze:
        e['gaze'] = gaze
    if blink == 2:
        e['blink'] = True
    elif blink == 1:
        e['eye'] = 0.42
    _BC[k] = chars.render(chars.build(who, **e), K.BUST_SCALE)
    if len(_BC) > 160:
        _BC.popitem(last=False)
    return _BC[k]


def who_of(key):
    return 'arjun' if key.startswith('arjun') else 'krishna'


def speaking(t, who):
    """(is this character speaking at t, mouth 0/1/2)."""
    i = max(0, min(len(TL['mouth']) - 1, int(round(t*FPS))))
    talk = TL['who'][i] == who
    return talk, (TL['mouth'][i] or 0) if talk else 0


def life(t, t0, t1, seed=0.0):
    """Head motion for a bust shown from t0 to t1: nods + brow lifts on emphasised words, slow sway, gaze away in pauses.
    Returns rot (deg), dy (px), brow_on, gaze."""
    rot, dy, brow = 0.0, 0.0, False
    for j, te in enumerate(EMPH_T):
        if not (t0 <= te < t1):
            continue
        d = t - te
        if -0.1 < d < 0.5:
            n = math.sin(math.pi*(d + 0.1)/0.6)
            dy += 9*n
            rot += 0.8*n*(1 if j % 2 else -1)
        if -0.06 < d < 0.42:
            brow = True
    rot += 0.55*math.sin(2*math.pi*t/4.3 + t0 + seed) + 0.3*math.sin(2*math.pi*t/2.2 + 1.1 + seed)
    gaze = (7, -2) if any(a <= t < b for a, b in GAPS if t0 <= a < t1) else None
    return rot, dy, brow, gaze


def standing_bust(c, key, t, t0, x, y_bottom, s, t1=None, flip=False):
    """A character inside the world (talking, blinking, nodding), bottom-centre at (x, y_bottom), scale s.
    Call from a world's scene() so depth order is right. Busts face right by default; flip=True mirrors."""
    t1 = t1 if t1 is not None else t0 + 60
    who = who_of(key)
    talk, m = speaking(t, who)
    rot, dy, brow, gaze = life(t, t0, t1, seed=1.7 if who == 'arjun' else 0.0)
    if not talk and gaze is None:
        gaze = (8, 2)
    img = bust(key, m, K.blink_at(t, t0, t1, key), brow, gaze)
    c.save()
    c.translate(x, y_bottom - 300 + dy - 1.5*m)
    c.rotate(rot)
    c.translate(0, 300)
    c.scale(-s if flip else s, s)
    c.drawImage(img, -img.width()/2, -img.height(), skia.SamplingOptions(skia.FilterMode.kLinear))
    c.restore()


def blur_backdrop(c, draw_scene, t, tint=0.45):
    """Half-res render of draw_scene(canvas, t), blurred, as a close-up background."""
    small = skia.Surface(W//2, H//2)
    sc = small.getCanvas()
    sc.scale(0.5, 0.5)
    draw_scene(sc, t)
    img = small.makeImageSnapshot()
    c.clear(skia.ColorBLACK)
    c.drawImageRect(img, skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear),
                    skia.Paint(ImageFilter=skia.ImageFilters.Blur(14, 14)))
    c.drawRect(skia.Rect(0, 0, W, H), P(hexc('#0a0716'), tint))


def plain_backdrop(c, top='#1a2440', bottom='#070a16'):
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeRadial(
        skia.Point(540, 760), 1200, [hexc(top).toColor(), hexc(bottom).toColor()])))


def closeup(c, key, t, t0, t1, backdrop=None, glow_col=None, py=1250, scale=0.86):
    """Bust close-up from t0 to t1. backdrop(c, t) draws the background (e.g. lambda c, t: E.blur_backdrop(c, scene, t));
    default is a plain gradient. Draw cards or pills after calling this."""
    if backdrop:
        backdrop(c, t)
    else:
        plain_backdrop(c)
    who = who_of(key)
    glow(c, W/2, 980, 520, glow_col or (hexc('#7fa0ff') if who == 'krishna' else hexc('#ffb36b')), 0.16)
    talk, m = speaking(t, who)
    rot, dy, brow, gaze = life(t, t0, t1)
    img = bust(key, m, K.blink_at(t, t0, t1, key), brow, gaze)
    s = scale*(1 + 0.03*(1 - ease_out((t - t0)/0.6)))*(1 + 0.004*math.sin(2*math.pi*t/3.2))
    c.save()
    c.translate(W/2, py + dy + 2.5*math.sin(2*math.pi*t/3.2) - 1.5*m)
    c.rotate(rot)
    c.translate(0, 1600 - py)
    c.scale(s, s)
    c.drawImage(img, -img.width()/2, -img.height(), skia.SamplingOptions(skia.FilterMode.kLinear))
    c.restore()
    bottom_fade(c)


# ----------------------------------------------------------------------------- on-screen elements
def verse_card(c, t, t_in, lines, ref, y0=250, a_out=1.0):
    """Small shloka card: Devanagari lines (shaped via raqm) + 'GITA x.yy'. Slides in at t_in.
    Tiro Devanagari has no Latin punctuation: use '।' inside lines, write the ref in Latin."""
    a = ramp(t, t_in, 0.3)*a_out
    if a <= 0.01:
        return
    dy = 18*(1 - ease_out((t - t_in)/0.4))
    h = 90 + 70*len(lines)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, y0 - 50), skia.Point(0, y0 + h + 80)],
                                        [ca(hexc('#0b0716'), 0.8).toColor(), ca(hexc('#0b0716'), 0).toColor()])
    c.saveLayerAlpha(None, int(255*a)); c.drawRect(skia.Rect(0, y0 - 50, W, y0 + h + 80), skia.Paint(Shader=sh)); c.restore()
    card(c, 110, y0 + dy, 970, y0 + h + dy, a, fill=0.9)
    for i, ln in enumerate(lines):
        draw_deva(c, ln, 540, y0 + 72 + 70*i + dy, 50, (255, 221, 150), a)
    Wd.text(c, ref, 540, y0 + h - 26 + dy, 'semi', 20, hexc('#d8c8d8'), 0.85*a, align='center', spacing=3)


def hud(c, t, label, value, col, t_change, a=1.0, sub='', plate=False):
    """Top-right label + big value that pops when it changes at t_change. Keep the HUD area (y < ~190) free otherwise.
    plate=True draws a dark rounded backing, needed over bright scenes (daytime walls, white kitchens)."""
    if a <= 0.01:
        return
    if plate:
        w_ = max(230, 48 + 40*len(str(value)) + (18*len(sub) if sub else 0), 14*len(label) + 60)
        rr = skia.RRect.MakeRectXY(skia.Rect(W - 30 - w_, 40, W - 30, 170), 22, 22)
        blurred(c, skia.Path().addRRect(rr), hexc('#000000'), 0.35*a, 14)
        c.drawRRect(rr, P(hexc('#120c1e'), 0.82*a))
    Wd.text(c, label, W - 52, 74, 'semi', 19, Wd.TXT2, a, align='right', spacing=2.5)
    pop = max(0.0, 1 - (t - t_change)/0.4)**2 if t >= t_change else 0.0
    c.save(); s = 1 + 0.3*pop
    c.translate(W - 52, 128); c.scale(s, s); c.translate(-(W - 52), -128)
    Wd.text(c, str(value), W - 52, 148, 'xb', 66, col, a, align='right')
    c.restore()
    if sub:
        Wd.text(c, sub, W - 52 - 30 - 18*len(str(value)), 146, 'bold', 24, col, a, align='right')
    if pop > 0:
        glow(c, W - 80, 124, 150, col, 0.4*pop)


SYN = {'kw': '#c792ea', 'cls': '#ffcb6b', 'fn': '#82aaff', 'fn2': '#89ddff', 'str': '#c3e88d', 'p': '#cfd3e6', 'id': '#f07178',
       'cm': '#7f7aa8', 'ok': '#38e58f', 'err': '#ff5470', 'dim': '#8a86b0'}


def code_line(c, toks, x, y, a=1.0, size=32, nchars=None):
    """One line of syntax-coloured mono code. toks: [(text, kind)] with kind in SYN. nchars types it out.
    Returns (x_end, chars_drawn). JetBrains Mono here is a latin subset: no arrows, use '›'."""
    fm = Wd.font('mono', size)
    cw = fm.measureText('M')
    n = 0
    for txt, kind in toks:
        col = hexc(SYN[kind])
        for ch in txt:
            if nchars is not None and n >= nchars:
                return x, n
            if ch != ' ':
                c.drawString(ch, x, y, fm, P(col, a))
            x += cw
            n += 1
    return x, n


def panel(c, x0, y0, x1, y1, a, title=None, border=None):
    """Dark rounded panel (code editor / terminal / browser). title adds a window bar with traffic lights."""
    rr = skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), 18, 18)
    blurred(c, skia.Path().addRRect(rr), hexc('#000000'), 0.55*a, 18)
    c.drawRRect(rr, P(hexc('#141026'), 0.96*a))
    c.drawRRect(rr, SP(border or hexc('#3a3462'), 2.2, a))
    if title is not None:
        c.save(); c.clipRRect(rr, doAntiAlias=True)
        c.drawRect(skia.Rect(x0, y0, x1, y0 + 50), P(hexc('#1d1836'), a))
        c.restore()
        for i, col in enumerate(('#ff5f57', '#febc2e', '#28c840')):
            c.drawCircle(x0 + 30 + 24*i, y0 + 25, 7, P(hexc(col), a))
        Wd.text(c, title, (x0 + x1)/2, y0 + 33, 'semi', 22, Wd.TXT2, a, align='center')


def pill(c, x, y, txt, col, a, size=20, k=1.0):
    """Small rounded label centred at (x, y); k < 1 pops it in."""
    if a <= 0.01:
        return
    f = Wd.font('bold', size)
    tw = f.measureText(txt) + 28
    s = back_out(k) if k < 1 else 1.0
    c.save(); c.translate(x, y); c.scale(s, s)
    rr = skia.RRect.MakeRectXY(skia.Rect(-tw/2, -size*0.95, tw/2, size*0.75), size, size)
    c.drawRRect(rr, P(hexc('#120c1e'), 0.92*a))
    c.drawRRect(rr, SP(col, 2.2, a))
    Wd.text(c, txt, 0, size*0.32, 'bold', size, col, a, align='center', spacing=1)
    c.restore()


# ----------------------------------------------------------------------------- frame finishing
_VIG = [None]


def caption_line(t):
    cur = None
    for i in ORDER:
        if t >= L[i]['s'] - 0.1:
            cur = L[i]
    return cur


def finish_frame(c, t, shots=None, flash=True, top_shade=True, end_fade=True):
    """Vignette, top shade, a soft flash at each shot cut, karaoke caption, fade to black at the end.
    Call last in frame(t), after the HUD."""
    if _VIG[0] is None:
        _VIG[0] = Wd.vignette()
    c.drawImage(_VIG[0], 0, 0)
    if top_shade:
        sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 200)],
                                            [ca(hexc('#0a0612'), 0.5).toColor(), ca(hexc('#0a0612'), 0).toColor()])
        c.drawRect(skia.Rect(0, 0, W, 200), skia.Paint(Shader=sh))
    if flash and shots and len(shots) > 1:
        fl = max(bump(t, s_[0] - 0.08, s_[0] + 0.12) for s_ in shots[1:])
        if fl > 0:
            c.drawRect(skia.Rect(0, 0, W, H), P(hexc('#ffe8c0'), 0.16*fl))
    ln = caption_line(t)
    if ln:
        fade = 1 - ramp(t, ln['e'] + 1.1, 0.35)
        if fade > 0.01:
            K.caption_k(c, ln, t, fade)
    if end_fade:
        end = ramp(t, DUR - 0.7, 0.65)
        if end > 0:
            c.drawRect(skia.Rect(0, 0, W, H), P(hexc('#000000'), end))


# ----------------------------------------------------------------------------- CLI / render
_FRAME = [None]


def _init_worker(frame):
    # macOS starts workers with 'spawn': they re-import the driver without running run(), so hand them frame() here.
    _FRAME[0] = frame


def _work(args):
    i, fps = args
    return _FRAME[0](i/fps).toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].tobytes()


def _sheet(paths, out, cols=6):
    from PIL import Image
    ims = [Image.open(p).resize((270, 480)) for p in paths]
    rows = (len(ims) + cols - 1)//cols
    sh = Image.new('RGB', (270*cols, 480*rows))
    for i, im in enumerate(ims):
        sh.paste(im, ((i % cols)*270, (i//cols)*480))
    sh.save(out)


def run(frame, cues):
    """frame(t) -> skia.Image; cues() -> [(t, name, gain_db)] with names whoosh, swell, pop, hit, glitch, tick, bowl, riser,
    chime, train (see mix.py)."""
    _FRAME[0] = frame
    ap = argparse.ArgumentParser()
    ap.add_argument('--fps', type=int, default=FPS)
    ap.add_argument('--out', default=f'{EP}/silent.mp4')
    ap.add_argument('--still', type=float, nargs='*', help='render these times to stills/ and a contact sheet stills/sheet.png')
    ap.add_argument('--cues', action='store_true')
    ap.add_argument('--range', type=float, nargs=2, metavar=('A', 'B'), help='render only frames in [A, B) seconds (for splicing)')
    ap.add_argument('--workers', type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    if a.cues:
        os.makedirs(f'{EP}/data', exist_ok=True)
        cs = sorted(cues())
        json.dump([dict(t=round(t, 3), name=n, gain=g) for t, n, g in cs], open(f'{EP}/data/cues.json', 'w'), indent=1)
        print('cues', len(cs))
        return
    if a.still is not None:
        os.makedirs(f'{EP}/stills', exist_ok=True)
        paths = []
        for t in a.still:
            p = f'{EP}/stills/s_{t:05.2f}.png'
            frame(t).save(p)
            paths.append(p)
        if len(paths) > 1:
            _sheet(paths, f'{EP}/stills/sheet.png')
            print('sheet', f'{EP}/stills/sheet.png')
        return
    n_all = int(round(DUR*a.fps))
    i0, i1 = (int(round(a.range[0]*a.fps)), min(n_all, int(round(a.range[1]*a.fps)))) if a.range else (0, n_all)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(a.fps),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', a.out],
                          stdin=subprocess.PIPE)
    ctx = mp.get_context(os.environ.get('GT_MP_START') or None)   # GT_MP_START=spawn reproduces macOS on Linux
    with ctx.Pool(a.workers, initializer=_init_worker, initargs=(frame,)) as pool:
        for k, buf in enumerate(pool.imap(_work, [(i, a.fps) for i in range(i0, i1)], chunksize=2)):
            ff.stdin.write(buf)
            if k % 150 == 0:
                print(f'{k}/{i1 - i0}', flush=True)
    ff.stdin.close()
    ff.wait()
    print('done', a.out, f'{(i1 - i0)/a.fps:.2f}s')
