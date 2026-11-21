"""Shared helpers for Gita x Tech reels: easing, camera lerp, characters (bust + blink), karaoke captions,
Devanagari text (Pillow + raqm shaping), cards, concept tags, mandala, orbs, bust drawing.
Drivers do `import gt as K` and set K.PAGE_AT = {line_id: word index where caption page 2 starts}.
"""
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
from PIL import Image, ImageDraw, ImageFont

import chars
import world as Wd
from iso import Cam, P, SP, glow, hexc, ca, blurred, polyline, arc_path, point_on, U

W, H = 1080, 1920
FONTS = Path(__file__).resolve().parent.parent / 'fonts'
PAGE_AT = {}


# ----------------------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(k):
    k = clamp(k)
    return k*k*(3 - 2*k)


def ease_out(k):
    k = clamp(k)
    return 1 - (1 - k)**3


def back_out(k, s=1.7):
    k = clamp(k) - 1
    return k*k*((s + 1)*k + s) + 1


def lerp(a, b, k):
    return a + (b - a)*k


def bump(t, a, b):
    if t < a or t > b:
        return 0.0
    return math.sin(math.pi*(t - a)/(b - a))**2


def ramp(t, a, d):
    return ease((t - a)/d) if d > 0 else float(t >= a)


def cam_lerp(A, B, k):
    k = ease(k)
    z = math.exp(lerp(math.log(A[2]), math.log(B[2]), k))
    return Cam(lerp(A[0], B[0], k), lerp(A[1], B[1], k), z, sy0=lerp(A[3], B[3], k))


def C(A):
    return Cam(A[0], A[1], A[2], sy0=A[3])




# ----------------------------------------------------------------------------- characters
MOUTHS = {'arjun_panic': ('worry', 'worry_talk', 'panic'), 'krishna': ('rest', 'talk1', 'talk2'),
          'arjun_worried': ('worry', 'talk1', 'worry_talk'), 'arjun_curious': ('rest', 'talk1', 'talk2'),
          'arjun_relief': ('smile', 'talk1', 'smile_talk'), 'krishna_smile': ('smile', 'talk1', 'smile_talk'),
          'krishna_knowing': ('smile', 'talk1', 'smile_talk')}
BASE = {'arjun_panic': ('arjun', chars.EXPR['arjun']['panic']), 'krishna': ('krishna', chars.EXPR['krishna']['serene']),
        'arjun_worried': ('arjun', chars.EXPR['arjun']['worried']), 'arjun_curious': ('arjun', chars.EXPR['arjun']['curious']),
        'arjun_relief': ('arjun', chars.EXPR['arjun']['relief']), 'krishna_smile': ('krishna', chars.EXPR['krishna']['smile']),
        'krishna_knowing': ('krishna', chars.EXPR['krishna']['knowing'])}
for _k, _ex, _mo in (('arjun_frustrated', 'frustrated', ('worry', 'talk1', 'worry_talk')), ('arjun_sheepish', 'sheepish', ('worry', 'talk1', 'worry_talk')),
                     ('arjun_determined', 'determined', ('rest', 'talk1', 'talk2'))):
    BASE[_k] = ('arjun', chars.EXPR['arjun'][_ex])
    MOUTHS[_k] = _mo
BUST_SCALE = 1.12
_CACHE = {}


def bust(key, mouth_i, blink):
    k = (key, mouth_i, blink)
    if k not in _CACHE:
        who, base = BASE[key]
        e = dict(base)
        e['mouth'] = MOUTHS[key][mouth_i]
        if blink == 2:
            e['blink'] = True
        elif blink == 1:
            e['eye'] = 0.42
        _CACHE[k] = chars.render(chars.build(who, **e), BUST_SCALE)
    return _CACHE[k]




def blink_at(t, t0, t1, key):
    if key == 'arjun_panic':
        times = [t0 + 1.4]
    else:
        times = [t0 + 0.9 + 3.3*k for k in range(6)]
    for b in times:
        if b > t1 - 0.25:
            break
        d = t - b
        if 0 <= d < 1/30 or 3/30 <= d < 4/30:
            return 1
        if 1/30 <= d < 3/30:
            return 2
    return 0




def caption_k(c, line, t, a_mul=1.0):
    pages = [p.strip() for p in line['cap'].split('|')]
    ws = line['words']
    if len(pages) > 1:
        k = PAGE_AT[line['id']]
        spans = [(line['s'], ws[k]['s'] - 0.02), (ws[k]['s'], line['e'])]
        pi = 1 if t >= ws[k]['s'] - 0.08 else 0
    else:
        spans, pi = [(line['s'], line['e'])], 0
    cap = pages[pi]
    ps, pe = spans[pi]
    t_in = line['s'] - 0.1 if pi == 0 else ps - 0.08
    a = ease((t - t_in)/0.16)*a_mul
    if a <= 0:
        return
    dy = 14*(1 - ease((t - t_in)/0.16))
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 1440), skia.Point(0, H)],
                                        [ca(hexc('#07040f'), 0).toColor(), ca(hexc('#07040f'), 0.85).toColor(), ca(hexc('#07040f'), 0.95).toColor()], [0, 0.45, 1])
    c.drawRect(skia.Rect(0, 1440, W, H), skia.Paint(Shader=sh))
    Wd.text(c, line['who'].upper(), W/2, 1604 + dy, 'cinzel', 26, Wd.GOLD_L, a, align='center', spacing=3)
    words, hl = [], False
    for chunk in cap.split('*'):
        for wd in chunk.split(' '):
            if wd:
                words.append((wd, hl))
        hl = not hl
    size, sp, widths, rows = _caption_layout(words)
    total = sum(len(x) for x, _ in words)
    prog = clamp((t - ps)/max(0.1, pe - ps))
    acc, start = 0, []
    for x, _ in words:
        start.append(acc/total)
        acc += len(x)
    lh = size*1.3
    y = {1: 1684, 2: 1664}.get(len(rows), 1650)
    for r in rows:
        rw = sum(widths[j] for j in r) + sp*(len(r) - 1)
        x = W/2 - rw/2
        for j in r:
            wd, h = words[j]
            spoken = prog >= start[j] - 0.01
            Wd.text(c, wd, x, y + dy, 'pop', size, Wd.GOLD_L if h else Wd.TXT1, a*(1.0 if spoken else 0.38))
            x += widths[j] + sp
        y += lh


CAP_W = 960


def _caption_layout(words):
    """Fit a caption page inside the frame: one row, else the most balanced two rows, shrinking the font from 54 down
    to 42 if needed; a page still too long wraps into three rows at 42 (long pages once ran off both screen edges)."""
    for size in (54, 50, 46, 42):
        f = Wd.font('pop', size)
        sp = f.measureText(' ')
        widths = [f.measureText(x) for x, _ in words]
        if sum(widths) + sp*(len(words) - 1) <= CAP_W:
            return size, sp, widths, [list(range(len(words)))]
        best, cutj = 1e9, 1
        for j in range(1, len(words)):
            l1 = sum(widths[:j]) + sp*(j - 1)
            l2 = sum(widths[j:]) + sp*(len(words) - j - 1)
            if max(l1, l2) < best:
                best, cutj = max(l1, l2), j
        if best <= CAP_W:
            return size, sp, widths, [list(range(cutj)), list(range(cutj, len(words)))]
    rows, cur, cw = [], [], 0.0
    for j, w_ in enumerate(widths):
        add = w_ if not cur else sp + w_
        if cur and cw + add > CAP_W:
            rows.append(cur); cur, cw = [j], w_
        else:
            cur.append(j); cw += add
    rows.append(cur)
    return size, sp, widths, rows



# ----------------------------------------------------------------------------- devanagari (shaped with raqm via Pillow)
TIRO = str(FONTS / 'Tiro-Deva.woff')
POPB = str(FONTS / 'Poppins-Bold.ttf')


@lru_cache(maxsize=64)
def deva(txt, size, rgb, hyphen=False):
    f = ImageFont.truetype(TIRO, size, layout_engine=ImageFont.Layout.RAQM)
    tw = int(f.getlength(txt)) + 40
    im = Image.new('RGBA', (tw + (30 if hyphen else 0), int(size*1.9)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((10, int(size*0.25)), txt, font=f, fill=rgb + (255,))
    if hyphen:
        d.text((tw - 26, int(size*0.25)), '-', font=ImageFont.truetype(POPB, int(size*0.8)), fill=rgb + (255,))
    a = np.array(im)
    a[..., :3] = (a[..., :3].astype(np.uint16)*a[..., 3:4]//255).astype(np.uint8)
    return skia.Image.fromarray(a, colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kPremul_AlphaType)


def draw_deva(c, txt, cx, y, size, rgb, a=1.0, hyphen=False):
    img = deva(txt, size, rgb, hyphen)
    c.drawImage(img, cx - img.width()/2, y - size*1.05, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=a))
    return img.width()


def card(c, x0, y0, x1, y1, a, border=Wd.GOLD, r=26, fill=0.82):
    rr = skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), r, r)
    blurred(c, skia.Path().addRRect(rr), hexc('#000000'), 0.55*a, 18)
    c.drawRRect(rr, P(hexc('#120a1e'), fill*a))
    c.drawRRect(rr, SP(border, 2.4, 0.9*a))




def concept_tag(c, x, y, left, right, a, k):
    if a <= 0.01:
        return
    s = back_out(k) if k < 1 else 1.0
    f = Wd.font('pop', 32)
    wl, wr, we = f.measureText(left), f.measureText(right), f.measureText('  =  ')
    tw = wl + wr + we + 56
    c.save()
    c.translate(x, y); c.scale(s, s)
    rr = skia.RRect.MakeRectXY(skia.Rect(-tw/2, -34, tw/2, 34), 34, 34)
    glow(c, 0, 0, tw*0.6, hexc('#ffb347'), 0.18*a)
    c.drawRRect(rr, P(hexc('#1a0f08'), 0.9*a))
    c.drawRRect(rr, SP(Wd.GOLD_L, 2.6, a))
    xx = -tw/2 + 28
    xx += Wd.text(c, left, xx, 11, 'pop', 32, Wd.TXT1, a)
    xx += Wd.text(c, '  =  ', xx, 11, 'pop', 32, Wd.GOLD, a)
    Wd.text(c, right, xx, 11, 'pop', 32, Wd.GOLD_L, a)
    c.restore()



def orb(c, x, y, col, a=1.0):
    glow(c, x, y, 70, col, 0.7*a)
    glow(c, x, y, 24, hexc('#ffffff'), 0.8*a)
    c.drawCircle(x, y, 7, P(hexc('#ffffff'), a))




def mandala(c, cx, cy, R, rot, a):
    if a <= 0.01:
        return
    glow(c, cx, cy, R*1.25, hexc('#ffb347'), 0.22*a)
    c.save()
    c.translate(cx, cy)
    for ring, (n, r0, r1, wdt, al, sp) in enumerate(((32, 0.78, 1.0, 2.0, 0.55, 1), (16, 0.52, 0.76, 2.4, 0.6, -1.4), (12, 0.3, 0.5, 2.2, 0.5, 2))):
        c.save()
        c.rotate(rot*sp)
        for i in range(n):
            ang = 360*i/n
            c.save()
            c.rotate(ang)
            pt = skia.Path()
            pt.moveTo(0, -r0*R)
            pt.cubicTo(R*(r1 - r0)*0.42, -R*(r0 + (r1 - r0)*0.35), R*(r1 - r0)*0.18, -R*(r1 - 0.05*(r1 - r0)), 0, -r1*R)
            pt.cubicTo(-R*(r1 - r0)*0.18, -R*(r1 - 0.05*(r1 - r0)), -R*(r1 - r0)*0.42, -R*(r0 + (r1 - r0)*0.35), 0, -r0*R)
            c.drawPath(pt, SP(hexc('#ffcf7a'), wdt, al*a, blend=skia.BlendMode.kPlus))
            c.drawCircle(0, -r1*R - 8, 2.6, P(hexc('#ffe1a0'), al*a))
            c.restore()
        c.restore()
    for rr, al in ((1.04, 0.4), (0.77, 0.35), (0.51, 0.3)):
        c.drawCircle(0, 0, rr*R, SP(hexc('#ffcf7a'), 1.6, al*a, blend=skia.BlendMode.kPlus))
    c.restore()




def draw_bust(c, img, s, dx=0.0, dy=0.0, bottom=1560):
    c.save()
    c.translate(W/2 + dx, bottom + dy)
    c.scale(s, s)
    c.drawImage(img, -img.width()/2, -img.height(), skia.SamplingOptions(skia.FilterMode.kLinear))
    c.restore()


def bottom_fade(c):
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 1380), skia.Point(0, 1570)],
                                        [ca(hexc('#07040f'), 0).toColor(), ca(hexc('#07040f'), 1).toColor()])
    c.drawRect(skia.Rect(0, 1380, W, 1570), skia.Paint(Shader=sh))
    c.drawRect(skia.Rect(0, 1569, W, H), P(hexc('#07040f')))

