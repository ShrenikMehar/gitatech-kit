"""Gita x Tech cluster world (Ep1 style, upgraded). Isometric skia renderer.

One coherent place: a raised control-plane dais (API server, scheduler, ReplicaSet controller, etcd + diya)
floating above a lower worker tier with three node slabs, wired together, over a Kurukshetra dusk.
"""
import math
import random

import numpy as np
import skia

from iso import (C30, H, S30, U, W, Cam, P, SP, arc_path, blurred, box, ca, cylinder, glow, hexc, lerp, mixc, point_on,
                 poly, polyline, rd, shade, shadow, tint, top_matrix, wire_box)

# ----------------------------------------------------------------------------- fonts / text
from pathlib import Path as _Path
FD = str(_Path(__file__).resolve().parent.parent / 'fonts') + '/'
IN = FD
GF = FD
TF = dict(bold=skia.Typeface.MakeFromFile(IN + 'Inter-Bold.otf'), semi=skia.Typeface.MakeFromFile(IN + 'Inter-SemiBold.otf'),
          med=skia.Typeface.MakeFromFile(IN + 'Inter-Medium.otf'), xb=skia.Typeface.MakeFromFile(IN + 'InterDisplay-ExtraBold.otf'),
          mono=skia.Typeface.MakeFromFile(FD + 'jetbrains-mono-latin-700-normal.woff'),
          monom=skia.Typeface.MakeFromFile(FD + 'jetbrains-mono-latin-500-normal.woff'),
          cinzel=skia.Typeface.MakeFromFile(FD + 'Cinzel-Bold.woff'),
          pop=skia.Typeface.MakeFromFile(GF + 'Poppins-Bold.ttf'), popm=skia.Typeface.MakeFromFile(GF + 'Poppins-Medium.ttf'))
_F = {}


def font(k, s):
    key = (k, round(s, 1))
    if key not in _F:
        f = skia.Font(TF[k], s)
        f.setSubpixel(True)
        f.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
        _F[key] = f
    return _F[key]


def text(c, s, x, y, k, size, col, a=1.0, align='left', spacing=0.0):
    f = font(k, size)
    if spacing:
        w = sum(f.measureText(ch) for ch in s) + spacing*(len(s) - 1)
        x0 = x - (w/2 if align == 'center' else w if align == 'right' else 0)
        for ch in s:
            c.drawString(ch, x0, y, f, P(col, a))
            x0 += f.measureText(ch) + spacing
        return w
    w = f.measureText(s)
    if align == 'center':
        x -= w/2
    elif align == 'right':
        x -= w
    if a > 0.003:
        c.drawString(s, x, y, f, P(col, a))
    return w


# ----------------------------------------------------------------------------- palette
API_C, ETCD_C, CTRL_C, SCHED_C = hexc('#9a86ff'), hexc('#ffb547'), hexc('#ff6fa5'), hexc('#3fd3ff')
RUN_C, PEND_C, DEAD_C, NODE_C, KUBELET_C = hexc('#38e58f'), hexc('#ffb547'), hexc('#ff5470'), hexc('#5b6fd0'), hexc('#46e3c4')
GOLD, GOLD_L = hexc('#d9a441'), hexc('#ffe1a0')
TXT1, TXT2, TXT3 = hexc('#f2f0ff'), hexc('#a9a3d6'), hexc('#6e6a9c')
CHIP_BG = hexc('#0e0a24')

# ----------------------------------------------------------------------------- layout (world units)
CP_C = (0.0, 0.0)              # control-plane dais centre
CP_HALF = 3.1
CP_Z = 0.0                     # top surface of the dais
API = dict(p=(0.0, 0.0), w=2.0, h=1.25)
SCHED = dict(p=rd(-2.7, -0.6), w=1.2, h=0.85)
CTRL = dict(p=rd(2.7, -0.6), w=1.2, h=0.85)
ETCD = dict(p=rd(0.0, 3.3), r=0.68, h=1.15)

WC = (7.9, 7.9)                # worker tier centre
WZ = -1.4                      # top surface of the worker tier
W_LO, W_HI = -4.15, 3.15       # tier extent relative to WC
NODE_W, NODE_H = 2.9, 0.35
NODES = [(WC[0] + o[0], WC[1] + o[1]) for o in (rd(-3.4, -1.2), rd(3.4, -1.2), rd(0, 2.6))]
POD = 0.72


def node_corner(i):
    x, y = NODES[i]
    return x - NODE_W/2, y - NODE_W/2


def slot_xy(i, s):
    x0, y0 = node_corner(i)
    return x0 + 0.3 + s*0.92, y0 + 1.95


def kubelet_xy(i):
    x0, y0 = node_corner(i)
    return x0 + 1.85, y0 + 0.3


NODE_TOP = WZ + NODE_H


# ----------------------------------------------------------------------------- environment
def sky(c, horizon=360, seed=7):
    """Kurukshetra dusk: gradient sky, warm horizon, distant army banners, dark plain below."""
    if horizon < -40:
        sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                            [hexc('#24102f').toColor(), hexc('#160c26').toColor(), hexc('#0b0716').toColor()], [0, 0.4, 1])
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
        return
    stops = [(0, '#120b28'), (0.55, '#2a1442'), (0.85, '#5a2550'), (1.0, '#a8475a')]
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, horizon)],
                                        [hexc(cc).toColor() for _, cc in stops], [k for k, _ in stops])
    c.drawRect(skia.Rect(0, 0, W, horizon), skia.Paint(Shader=sh))
    sh = skia.GradientShader.MakeLinear([skia.Point(0, horizon), skia.Point(0, H)],
                                        [hexc('#2a1236').toColor(), hexc('#160c26').toColor(), hexc('#0b0716').toColor()], [0, 0.35, 1])
    c.drawRect(skia.Rect(0, horizon, W, H), skia.Paint(Shader=sh))
    rnd = random.Random(seed)
    for _ in range(140):
        x, y = rnd.uniform(0, W), rnd.uniform(0, horizon*0.8)
        c.drawCircle(x, y, rnd.choice((0.8, 1.0, 1.3, 1.7)), P(hexc('#ffffff'), rnd.uniform(0.15, 0.6)*(1 - y/horizon)))
    # far hills
    for layer, (col, amp, base, a) in enumerate((('#3a1a4a', 26, 10, 0.9), ('#2a1238', 18, 0, 1.0))):
        p = skia.Path()
        p.moveTo(0, horizon + 2)
        for i in range(0, W + 40, 40):
            p.lineTo(i, horizon - base - amp*(0.5 + 0.5*math.sin(i*0.011 + layer*2.1)) * (0.6 + 0.4*math.sin(i*0.031 + layer)))
        p.lineTo(W, horizon + 2)
        p.close()
        c.drawPath(p, P(hexc(col), a))
    # army banners on the horizon (both sides of the field)
    for side in (-1, 1):
        for k in range(26):
            x = W/2 + side*(90 + k*rnd.uniform(14, 22))
            if x < 8 or x > W - 8:
                continue
            hgt = rnd.uniform(14, 30)
            y0 = horizon - rnd.uniform(0, 6)
            c.drawLine(x, y0, x, y0 - hgt, SP(hexc('#1a0c22'), 1.4, 0.9))
            fl = skia.Path()
            fl.moveTo(x, y0 - hgt)
            fl.lineTo(x + side*-1*0 + 9, y0 - hgt + 3.5)
            fl.lineTo(x, y0 - hgt + 7)
            fl.close()
            c.drawPath(fl, P(hexc('#e0782e' if side < 0 else '#b8304a'), 0.55))
    # horizon glow line + haze
    blurred(c, skia.Path().addRect(skia.Rect(0, horizon - 6, W, horizon + 6)), hexc('#ff9a5a'), 0.35, 10, skia.BlendMode.kPlus)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, horizon - 60), skia.Point(0, horizon + 140)],
                                        [ca(hexc('#c0507a'), 0).toColor(), ca(hexc('#c0507a'), 0.22).toColor(), ca(hexc('#c0507a'), 0).toColor()], [0, 0.35, 1])
    c.drawRect(skia.Rect(0, horizon - 60, W, horizon + 140), skia.Paint(Shader=sh))


def horizon_for(cam):
    """Distant horizon drifts up as the camera moves down the cluster / zooms in (parallax)."""
    d = cam.x + cam.y
    return 360 - (d - 8.4)*0.5*U*cam.zoom*0.6 - (cam.zoom - 0.7)*400


def ground_grid(c, cam, z=-6.0, horizon=360):
    span = int(16/cam.zoom) + 4
    gx, gy = round(cam.x), round(cam.y)
    c.save()
    c.clipRect(skia.Rect(0, horizon + 4, W, H))
    for i in range(-span, span + 1):
        for a3, b3 in (((gx + i, gy - span, z), (gx + i, gy + span, z)), ((gx - span, gy + i, z), (gx + span, gy + i, z))):
            (x1, y1), (x2, y2) = cam.p(*a3), cam.p(*b3)
            sh = skia.GradientShader.MakeLinear([skia.Point(0, horizon), skia.Point(0, horizon + 520)],
                                                [ca(hexc('#5a3a8a'), 0).toColor(), ca(hexc('#5a3a8a'), 0.32).toColor()])
            c.drawLine(x1, y1, x2, y2, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.1, Shader=sh))
    c.restore()


def particles(c, t, seed=3, n=46):
    rnd = random.Random(seed)
    for _ in range(n):
        x0, y0 = rnd.uniform(0, W), rnd.uniform(200, H - 300)
        sp, ph = rnd.uniform(6, 16), rnd.uniform(0, 6.28)
        y = (y0 - t*sp) % (H - 300)
        x = x0 + 10*math.sin(t*0.4 + ph)
        col = hexc('#ffc27a') if rnd.random() < 0.6 else hexc('#8fe6ff')
        r = rnd.uniform(1.2, 2.6)
        glow(c, x, y, r*4, col, 0.18)
        c.drawCircle(x, y, r*0.6, P(col, 0.7))


# ----------------------------------------------------------------------------- platforms
def plinth(c, cam, x0, y0, w, d, ztop, tiers=((0.32, 0.0), (0.34, 0.32)), engrave=None):
    """Two-tier stone dais with gold trim. tiers: (height, inset) from the top down."""
    z = ztop
    boxes = []
    for (h, inset) in tiers:
        boxes.append((x0 - inset, y0 - inset, z - h, w + 2*inset, d + 2*inset, h))
        z -= h
    # soft glow underneath + far shadow
    bx, by, bz, bw, bd, bh = boxes[-1]
    shadow(c, cam, bx, by, bw, bd, a=0.45, spread=0.6, z=-6.0)
    sil = cam.pts([(bx, by + bd, bz), (bx + bw, by + bd, bz), (bx + bw, by, bz)])
    p = skia.Path()
    p.moveTo(sil[0]); p.lineTo(sil[1]); p.lineTo(sil[2])
    c.drawPath(p, SP(hexc('#9a6bff'), 26*cam.zoom, 0.10, blend=skia.BlendMode.kPlus))
    for i, (bx, by, bz, bw, bd, bh) in enumerate(reversed(boxes)):
        last = i == len(boxes) - 1
        box(c, cam, bx, by, bz, bw, bd, bh, GOLD if last else hexc('#8a6a3a'),
            top=hexc('#2a2c5e') if last else hexc('#1e1f46'), left=hexc('#1a1b40') if last else hexc('#141532'),
            right=hexc('#11122c') if last else hexc('#0d0e24'), edge_w=1.5 if last else 1.0)
    # tile lines on the top surface
    c.save()
    c.concat(top_matrix(cam, x0, y0, ztop + 0.002))
    tp = SP(hexc('#3a3d7a'), 0.018, 0.55)
    for k in range(1, int(w)):
        c.drawLine(k, 0, k, d, tp)
    for k in range(1, int(d)):
        c.drawLine(0, k, w, k, tp)
    if engrave:
        engrave(c)
    c.restore()


def chakra(cx, cy):
    def draw(c):
        g = SP(GOLD, 0.03, 0.32)
        c.drawCircle(cx, cy, 2.55, g)
        c.drawCircle(cx, cy, 2.85, SP(GOLD, 0.02, 0.24))
        c.drawCircle(cx, cy, 1.55, SP(GOLD, 0.02, 0.2))
        for k in range(24):
            a = 2*math.pi*k/24
            c.drawLine(cx + 1.55*math.cos(a), cy + 1.55*math.sin(a), cx + 2.55*math.cos(a), cy + 2.55*math.sin(a), SP(GOLD, 0.016, 0.18))
        for k in range(48):
            a = 2*math.pi*(k + 0.5)/48
            c.drawCircle(cx + 2.7*math.cos(a), cy + 2.7*math.sin(a), 0.035, P(GOLD_L, 0.35))
    return draw


# ----------------------------------------------------------------------------- icons on box tops
def icon_wheel(c, col, a=1.0):
    c.drawCircle(0, 0, 0.42, SP(col, 0.07, a))
    c.drawCircle(0, 0, 0.11, P(col, a))
    for k in range(7):
        ang = 2*math.pi*k/7 - math.pi/2
        c.drawLine(0.13*math.cos(ang), 0.13*math.sin(ang), 0.42*math.cos(ang), 0.42*math.sin(ang), SP(col, 0.06, a))
        c.drawCircle(0.52*math.cos(ang), 0.52*math.sin(ang), 0.05, P(col, a))


def icon_target(c, col, a=1.0):
    for r in (0.12, 0.26, 0.4):
        c.drawCircle(0, 0, r, SP(col, 0.05, a))
    c.drawCircle(0, 0, 0.05, P(col, a))


def icon_loop(c, col, a=1.0):
    p = skia.Path()
    p.addArc(skia.Rect(-0.36, -0.36, 0.36, 0.36), 30, 290)
    c.drawPath(p, SP(col, 0.07, a))
    ang = math.radians(320)
    hx, hy = 0.36*math.cos(ang), 0.36*math.sin(ang)
    hp = skia.Path()
    hp.moveTo(hx + 0.14, hy - 0.02); hp.lineTo(hx - 0.04, hy - 0.16); hp.lineTo(hx - 0.06, hy + 0.1); hp.close()
    c.drawPath(hp, P(col, a))


def top_icon(c, cam, cx, cy, z, fn, col, a=1.0, scale=1.0):
    c.save()
    m = top_matrix(cam, cx, cy, z + 0.003)
    c.concat(m)
    c.scale(scale, scale)
    blurred(c, skia.Path().addCircle(0, 0, 0.5), col, 0.25*a, 0.08)
    fn(c, col, a)
    c.restore()


# ----------------------------------------------------------------------------- components
def comp_box(c, cam, spec, col, z, icon=None, glow_a=0.5, a=1.0):
    (cx, cy), w, h = spec['p'], spec['w'], spec['h']
    shadow(c, cam, cx - w/2, cy - w/2, w, w, a=0.5, spread=0.15, z=z)
    box(c, cam, cx - w/2, cy - w/2, z, w, w, h, col, a=a, glow_a=glow_a)
    if icon:
        top_icon(c, cam, cx, cy, z + h, icon, col, a, scale=w/1.6)
    return cam.p(cx, cy, z + h)


def diya(c, cam, x, y, z, t=0.0, a=1.0, fs=1.0):
    k = U*cam.zoom
    bx, by = cam.p(x, y, z)
    w = 0.42*k
    bowl = skia.Path()
    bowl.moveTo(bx - w, by - 0.02*k)
    bowl.cubicTo(bx - w*0.8, by + 0.2*k, bx + w*0.8, by + 0.2*k, bx + w, by - 0.02*k)
    bowl.lineTo(bx + w*1.25, by - 0.09*k)
    bowl.cubicTo(bx + w*0.6, by - 0.02*k, bx - w*0.6, by - 0.02*k, bx - w, by - 0.02*k)
    bowl.close()
    sh = skia.GradientShader.MakeLinear([skia.Point(bx - w, 0), skia.Point(bx + w, 0)], [hexc('#e08a4a').toColor(), hexc('#a8481e').toColor(), hexc('#6a2a10').toColor()], [0, 0.5, 1])
    c.drawPath(bowl, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawOval(skia.Rect(bx - w, by - 0.08*k, bx + w*0.95, by + 0.04*k), P(hexc('#3a1606'), a))
    if fs <= 0.02:
        for j in range(4):
            u = (t*0.6 + j*0.25) % 1.0
            sx_, sy_ = bx + 6*math.sin(t*3 + j)*u*cam.zoom, by - 0.1*k - u*0.9*k
            glow(c, sx_, sy_, (10 + 30*u)*cam.zoom, hexc('#b8a8c8'), 0.25*(1 - u)*a)
        return
    fl = (1 + 0.06*math.sin(t*11) + 0.04*math.sin(t*17.3))*fs
    fh = 0.62*k*fl
    fx, fy = bx + 0.02*k, by - 0.04*k
    glow(c, fx, fy - fh*0.45, 1.6*k, hexc('#ff9a3a'), 0.42*a*fs)
    glow(c, fx, fy - fh*0.45, 0.55*k, hexc('#ffd27a'), 0.6*a*fs)
    flame = skia.Path()
    flame.moveTo(fx, fy - fh)
    flame.cubicTo(fx + 0.2*k, fy - fh*0.55, fx + 0.16*k, fy - 0.02*k, fx, fy)
    flame.cubicTo(fx - 0.16*k, fy - 0.02*k, fx - 0.2*k, fy - fh*0.55, fx, fy - fh)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, fy - fh), skia.Point(0, fy)],
                                        [hexc('#ff7a1a').toColor(), hexc('#ffc24a').toColor(), hexc('#fff6d8').toColor()], [0, 0.45, 1])
    c.drawPath(flame, skia.Paint(AntiAlias=True, Shader=sh))
    inner = skia.Path()
    inner.addOval(skia.Rect(fx - 0.05*k, fy - fh*0.42, fx + 0.05*k, fy - 0.03*k))
    c.drawPath(inner, P(hexc('#ffffff'), 0.9*a))


def _shards(c, cam, cx, cy, spread, a, n=11, seed=5):
    rnd = random.Random(seed)
    for k in range(n):
        ang = rnd.uniform(-2.9, -0.2)
        dist = rnd.uniform(0.35, 1.0)*spread*U*cam.zoom
        sx, sy = cx + math.cos(ang)*dist, cy + math.sin(ang)*dist*0.8 + (spread**2)*14*cam.zoom
        r = rnd.uniform(5, 12)*cam.zoom/0.7
        rot = rnd.uniform(0, 6.28) + spread*3
        sh = skia.Path()
        for j in range(3):
            aa = rot + j*2.1
            (sh.moveTo if j == 0 else sh.lineTo)(sx + math.cos(aa)*r, sy + math.sin(aa)*r*0.8)
        sh.close()
        c.drawPath(sh, P(hexc('#ff8a9a'), 0.85*a))


def pod(c, cam, i_node, slot, state='run', a=1.0, t=0.0, k=1.0, pulse=0.0):
    """states: run | pending | ghost | dying (k = crack progress) | shatter (k = 0..1 blow-out) | husk."""
    x, y = slot_xy(i_node, slot)
    z = NODE_TOP
    top3 = cam.p(x + POD/2, y + POD/2, z + POD)
    cx, cy = cam.p(x + POD/2, y + POD/2, z + POD/2)
    if state == 'ghost':
        wire_box(c, cam, x, y, z, POD, POD, POD, PEND_C, a=0.8*a, phase=-t*30)
        return top3
    if state == 'husk':
        wire_box(c, cam, x, y, z, POD, POD, POD, DEAD_C, a=0.42*a*k, phase=0)
        glow(c, cx, cy, 60*cam.zoom, DEAD_C, 0.12*a*k)
        return top3
    if state == 'born':
        kk = 1 - (1 - min(1.0, k))**3
        bx0, by0 = cam.p(x + POD/2, y + POD/2, z)
        bw = 46*cam.zoom/0.7
        sh = skia.GradientShader.MakeLinear([skia.Point(0, by0 - 520*cam.zoom), skia.Point(0, by0)],
                                            [ca(RUN_C, 0).toColor(), ca(RUN_C, 0.7*(1 - 0.8*k)*a).toColor()])
        c.drawRect(skia.Rect(bx0 - bw/2, by0 - 520*cam.zoom, bx0 + bw/2, by0), skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kPlus))
        glow(c, cx, cy, 150*cam.zoom, RUN_C, 0.6*(1 - 0.6*k)*a)
        shadow(c, cam, x, y, POD, POD, a=0.45*kk, spread=0.08, z=z)
        box(c, cam, x, y, z, POD, POD, POD*max(0.04, kk), RUN_C, a=a, glow_a=1.4 - 0.8*k, solid=True, edge_w=1.6)
        return top3
    if state == 'shatter':
        glow(c, cx, cy, (120 + 160*k)*cam.zoom, DEAD_C, 0.55*(1 - k)*a)
        ring = skia.Path()
        rr = (0.4 + 1.6*k)*U*cam.zoom
        ring.addOval(skia.Rect(cx - rr, cy - rr*0.58, cx + rr, cy + rr*0.58))
        c.drawPath(ring, SP(DEAD_C, 5*cam.zoom*(1 - k) + 0.5, 0.8*(1 - k)*a, blend=skia.BlendMode.kPlus))
        if k < 0.35:
            box(c, cam, x, y, z, POD, POD, POD, DEAD_C, a=(1 - k/0.35)*a, glow_a=1.0, solid=True,
                top=hexc('#ffd0d6'), left=hexc('#e04a62'), right=hexc('#a02038'))
        _shards(c, cam, cx, cy, 1.1 + 1.6*k, (1 - k)*a, n=16)
        return top3
    if state == 'fade':  # graceful scale-down
        kk = min(1.0, k)
        shadow(c, cam, x, y, POD, POD, a=0.45*(1 - kk), spread=0.08, z=z)
        box(c, cam, x, y, z, POD, POD, POD*max(0.03, 1 - kk), mixc(RUN_C, TXT3, kk), a=a*(1 - 0.6*kk), glow_a=0.4, solid=True)
        return top3
    if state == 'crash':  # CrashLoopBackOff: red, blinking restarts
        ph = (t*1.5 + k) % 1.0
        on = 0.35 + 0.65*abs(math.sin(ph*math.pi))
        shadow(c, cam, x, y, POD, POD, a=0.45, spread=0.08, z=z)
        glow(c, cx, cy, 110*cam.zoom, DEAD_C, 0.45*on*a)
        box(c, cam, x, y, z, POD, POD, POD, DEAD_C, a=a*(0.55 + 0.45*on), glow_a=1.1*on, solid=True, edge_w=1.6,
            top=hexc('#ff8a9a'), left=hexc('#c2304a'), right=hexc('#8a1a30'))
        if ph < 0.18:
            r = (0.5 + 2.2*ph)*U*cam.zoom
            ring = skia.Path(); ring.addOval(skia.Rect(cx - r, cy - r*0.58, cx + r, cy + r*0.58))
            c.drawPath(ring, SP(DEAD_C, 3, 0.8*(1 - ph/0.18), blend=skia.BlendMode.kPlus))
        return top3
    if state == 'drift':
        state = 'pending'
    col = {'run': RUN_C, 'dying': DEAD_C, 'pending': PEND_C}[state]
    shadow(c, cam, x, y, POD, POD, a=0.45, spread=0.08, z=z)
    if state == 'dying':
        glow(c, cx, cy, 120*cam.zoom, DEAD_C, (0.3 + 0.25*k)*a)
        box(c, cam, x, y, z, POD, POD, POD, col, a=0.9*a, glow_a=1.0, solid=True, edge_w=1.6,
            top=hexc('#ff8a9a'), left=hexc('#c2304a'), right=hexc('#8a1a30'))
        L = [(0.1, 0.9), (0.35, 0.62), (0.28, 0.45), (0.55, 0.3), (0.5, 0.12)]
        R = [(0.85, 0.95), (0.6, 0.7), (0.7, 0.5), (0.4, 0.35)]
        T = [(0.15, 0.95), (0.4, 0.6), (0.35, 0.4), (0.7, 0.2)]
        faces = ([cam.p(x + u*POD, y + POD, z + POD*v) for u, v in L], [cam.p(x + POD, y + POD*u, z + POD*v) for u, v in R],
                 [cam.p(x + POD*u, y + POD*v, z + POD) for u, v in T])
        for pts in faces:
            m = max(2, int(round(len(pts)*min(1, k*1.4))))
            if k > 0.02:
                c.drawPath(polyline(pts[:m]), SP(hexc('#fff0f2'), 3.2*cam.zoom/0.7, 0.95*a))
                c.drawPath(polyline(pts[:m]), SP(DEAD_C, 9*cam.zoom/0.7, 0.35*a, blend=skia.BlendMode.kPlus))
        if k > 0.4:
            _shards(c, cam, cx, cy, 0.5 + 0.6*(k - 0.4), min(1, (k - 0.4)*3)*a, n=7)
        return top3
    if pulse > 0:
        glow(c, cx, cy, 130*cam.zoom, col, 0.55*pulse*a)
    box(c, cam, x, y, z, POD, POD, POD, col, a=a, glow_a=0.6 + 0.8*pulse, solid=True, edge_w=1.6)
    c.save()
    c.concat(top_matrix(cam, x, y, z + POD + 0.003))
    for kk in (0.24, 0.48):
        c.drawLine(0.12, kk, POD - 0.12, kk, SP(tint(col, 0.5), 0.03, 0.6*a))
    c.restore()
    return top3


def node(c, cam, i, state='ready', a=1.0):
    x0, y0 = node_corner(i)
    col = NODE_C if state == 'ready' else DEAD_C
    shadow(c, cam, x0, y0, NODE_W, NODE_W, a=0.55, spread=0.2, z=WZ)
    box(c, cam, x0, y0, WZ, NODE_W, NODE_W, NODE_H, col, a=a, glow_a=0.25 if state == 'ready' else 0.6,
        top=hexc('#2b3570') if state == 'ready' else hexc('#3a1a34'))
    # empty pod slots
    for s in range(3):
        sx, sy = slot_xy(i, s)
        c.save()
        c.concat(top_matrix(cam, sx, sy, NODE_TOP + 0.002))
        c.drawRect(skia.Rect(0, 0, POD, POD), SP(tint(col, 0.2), 0.025, 0.45*a, dash=[0.08, 0.06]))
        c.restore()
    kx, ky = kubelet_xy(i)
    box(c, cam, kx, ky, NODE_TOP, 0.75, 0.75, 0.55, KUBELET_C if state == 'ready' else DEAD_C, a=a, glow_a=0.2)
    lx, ly = cam.p(kx + 0.375, ky + 0.375, NODE_TOP + 0.55)
    glow(c, lx, ly, 22*cam.zoom, KUBELET_C if state == 'ready' else DEAD_C, 0.7*a)
    c.drawCircle(lx, ly, 5*cam.zoom, P(hexc('#ffffff'), a))


NODE_LABEL_AT = {0: 'left', 1: 'right', 2: 'front'}


def node_label(c, cam, i, name, status, col, a=1.0):
    x0, y0 = node_corner(i)
    s = 30
    w1 = font('bold', s).measureText(name)
    w2 = font('semi', 22).measureText(status)
    tw = w1 + 18 + 14 + w2
    where = NODE_LABEL_AT[i]
    if not (60 < cam.p(x0 + NODE_W/2, y0 + NODE_W/2, WZ)[0] < W - 60):
        return
    if cam.p(x0 + NODE_W, y0 + NODE_W, WZ)[1] + 60 > 1470 and NODE_LABEL_AT[i] == 'front':
        return
    if where == 'left':
        lx, ly = cam.p(x0, y0 + NODE_W, WZ)
        x, y = lx + 10, ly + 52
        if x < 16:
            return
    elif where == 'right':
        lx, ly = cam.p(x0 + NODE_W, y0, WZ)
        x, y = lx - tw - 10, ly + 52
    else:
        lx, ly = cam.p(x0 + NODE_W, y0 + NODE_W, WZ)
        x, y = lx - tw/2, ly + 50
    text(c, name, x, y, 'bold', s, TXT1, a)
    c.drawCircle(x + w1 + 18, y - 10, 6, P(col, a))
    glow(c, x + w1 + 18, y - 10, 16, col, 0.5*a)
    text(c, status, x + w1 + 32, y - 1, 'semi', 22, col, a)


# ----------------------------------------------------------------------------- wires
def wire(c, cam, pts3, col, a=0.5, t=0.0, pulses=2, width=2.4):
    pts = [cam.p(*q) for q in pts3]
    path = polyline(pts)
    c.drawPath(path, SP(col, width*3.2*cam.zoom/0.7, 0.10*a, blend=skia.BlendMode.kPlus))
    c.drawPath(path, SP(col, width*cam.zoom/0.7, 0.55*a))
    for k in range(pulses):
        u = ((t*0.35 + k/pulses) % 1.0)
        x, y = point_on(pts, u)
        glow(c, x, y, 16*cam.zoom/0.7, col, 0.7*a)
        c.drawCircle(x, y, 3.2*cam.zoom/0.7, P(hexc('#ffffff'), 0.9*a))


def floor_route(a, b, z):
    """Manhattan route on a floor: a -> corner -> b."""
    return [(a[0], a[1], z), (a[0], b[1], z), (b[0], b[1], z)]


def kube_cable(i, n=40):
    """API server -> kubelet on node i: leaves the dais front, drops through the gap, lands on the kubelet."""
    s = (0.75, 0.75, 0.35)
    kx, ky = kubelet_xy(i)
    e = (kx + 0.375, ky + 0.375, NODE_TOP + 0.55)
    mid = ((s[0] + e[0])/2 + (0.6 if i == 1 else -0.6 if i == 0 else 0), (s[1] + e[1])/2 + (-0.6 if i == 1 else 0.6 if i == 0 else 0), max(s[2], e[2]) + 1.6)
    out = []
    for k in range(n + 1):
        u = k/n
        out.append(tuple((1-u)**2*s[j] + 2*(1-u)*u*mid[j] + u*u*e[j] for j in range(3)))
    return out


# ----------------------------------------------------------------------------- chips
def chip(c, cam, anchor3, s, col, a=1.0, dx=0, dy=-110, size=32, sub=None, anchor_xy=None):
    if a <= 0.003:
        return
    ax, ay = anchor_xy if anchor_xy else cam.p(*anchor3)
    f = font('bold', size)
    w = f.measureText(s) + 44
    if sub:
        w = max(w, font('monom', 21).measureText(sub) + 40)
    h = size + 24 + (30 if sub else 0)
    cx, cy = ax + dx, ay + dy
    x0 = min(max(cx - w/2, 24), W - 24 - w)
    y0 = cy - h/2
    if y0 < 40 or (y0 < 175 and x0 + w > W - 260) or y0 + h > 1470 or ax < 0 or ax > W:
        return  # keep chips out of the HUD and caption safe zones
    # leader
    ex = min(max(ax, x0 + 16), x0 + w - 16) if abs(dx) < 1 else (x0 + w if dx < 0 else x0)
    ey = y0 + h if (abs(dx) < 1 and dy < 0) else y0 if abs(dx) < 1 else cy
    c.drawLine(ax, ay, ex, ey, SP(col, 2.2, 0.75*a))
    c.drawCircle(ax, ay, 5.5, P(col, a))
    glow(c, ax, ay, 14, col, 0.6*a)
    rr = skia.RRect.MakeRectXY(skia.Rect(x0, y0, x0 + w, y0 + h), 18, 18)
    blurred(c, skia.Path().addRRect(rr), hexc('#000000'), 0.5*a, 10)
    c.drawRRect(rr, P(CHIP_BG, 0.92*a))
    c.drawRRect(rr, SP(col, 2.4, a))
    text(c, s, x0 + w/2, y0 + size + 5, 'bold', size, TXT1, a, align='center')
    if sub:
        text(c, sub, x0 + w/2, y0 + size + 36, 'monom', 21, col, a, align='center')


# ----------------------------------------------------------------------------- HUD + captions
def hud(c, running, desired=3, a=1.0, pop=0.0, title=None):
    if title:  # optional series/episode header (off by default: episodes are standalone)
        text(c, title[0], 56, 104, 'cinzel', 38, GOLD_L, a, spacing=2)
        text(c, title[1], 58, 142, 'med', 25, TXT2, a)
    text(c, 'RUNNING', W - 56, 80, 'semi', 19, TXT2, a, align='right', spacing=2.5)
    col = TXT3 if desired == 0 else RUN_C if running >= desired else DEAD_C
    c.save()
    s = 1 + 0.35*pop
    c.translate(W - 56, 122); c.scale(s, s); c.translate(-(W - 56), -122)
    if pop > 0.01:
        glow(c, W - 110, 118, 90, col, 0.5*pop)
    text(c, f'{running}/{desired}', W - 56, 140, 'xb', 58, col, a, align='right')
    c.restore()


def caption(c, who, cap, a=1.0):
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 1440), skia.Point(0, H)],
                                        [ca(hexc('#07040f'), 0).toColor(), ca(hexc('#07040f'), 0.85).toColor(), ca(hexc('#07040f'), 0.95).toColor()], [0, 0.45, 1])
    c.drawRect(skia.Rect(0, 1440, W, H), skia.Paint(Shader=sh))
    text(c, who.upper(), W/2, 1604, 'cinzel', 26, GOLD_L, a, align='center', spacing=3)
    # *word* -> highlighted
    parts, hl = [], False
    for chunk in cap.split('*'):
        if chunk:
            parts.append((chunk, hl))
        hl = not hl
    f = font('pop', 54)
    total = sum(f.measureText(s) for s, _ in parts)
    x = W/2 - total/2
    for s, h in parts:
        x += text(c, s, x, 1684, 'pop', 54, GOLD_L if h else TXT1, a)


def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W/2)/(W/2))**2*0.55 + ((yy - 820)/(H/2))**2*1.0)
    a = np.clip((r - 0.55)/0.7, 0, 1)**1.6*0.75
    v = np.zeros((H, W, 4), np.uint8)
    v[..., :3] = (np.array([6, 3, 14], np.float32)[None, None, :]*a[..., None]).astype(np.uint8)
    v[..., 3] = (a*255).astype(np.uint8)
    return skia.Image.fromarray(v, colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kPremul_AlphaType)


_VIG = None


# ----------------------------------------------------------------------------- frame
def draw_world(c, cam, st, t=0.0):
    """st: dict(pods={(node,slot): state}, nodes=[state...], labels=bool, running, rs_ready)"""
    hz = horizon_for(cam)
    sky(c, horizon=hz)
    ground_grid(c, cam, horizon=hz)
    if st.get('pre_cp'):
        st['pre_cp'](c, cam, t)
    # --- control plane dais
    plinth(c, cam, CP_C[0] - CP_HALF, CP_C[1] - CP_HALF, 2*CP_HALF, 2*CP_HALF, CP_Z, engrave=chakra(CP_HALF, CP_HALF))
    zf = CP_Z + 0.004
    for spec, col in ((SCHED, SCHED_C), (CTRL, CTRL_C)):
        wire(c, cam, floor_route(spec['p'], API['p'], zf), col, a=0.8, t=t + hash(id(spec)) % 7, pulses=1)
    wire(c, cam, floor_route(ETCD['p'], API['p'], zf), ETCD_C, a=0.8, t=t, pulses=1)
    comp_box(c, cam, CTRL, CTRL_C, CP_Z, icon_loop, glow_a=0.5 if st.get('rs_ready', 3) >= 3 else 0.9 + 0.5*math.sin(t*9))
    comp_box(c, cam, SCHED, SCHED_C, CP_Z, icon_target)
    api_top = comp_box(c, cam, API, API_C, CP_Z, icon_wheel, glow_a=0.7)
    ex, ey = ETCD['p']
    shadow(c, cam, ex - ETCD['r'], ey - ETCD['r'], 2*ETCD['r'], 2*ETCD['r'], a=0.5, spread=0.1, z=CP_Z)
    cylinder(c, cam, ex, ey, CP_Z, ETCD['r'], ETCD['h'], ETCD_C, glow_a=st.get('etcd_glow', 0.6), bands=3)
    diya(c, cam, ex, ey, CP_Z + ETCD['h'], t, fs=st.get('diya', 1.0))
    # --- worker tier
    wx0, wy0 = WC[0] + W_LO, WC[1] + W_LO
    plinth(c, cam, wx0, wy0, W_HI - W_LO, W_HI - W_LO, WZ, tiers=((0.3, 0.0), (0.3, 0.3)))
    for i in range(3):
        wire(c, cam, kube_cable(i), API_C, a=0.55, t=t + i*0.31, pulses=1, width=2.2)
    order = [0, 1, 2]
    for i in order:
        node(c, cam, i, st['nodes'][i])
        for s in range(3):
            stt = st['pods'].get((i, s))
            if stt:
                stt, kk = stt if isinstance(stt, tuple) else (stt, 1.0)
                pod(c, cam, i, s, stt, t=t, k=kk, pulse=st.get('pulse', {}).get((i, s), 0.0))
    # --- labels
    LA = st.get('label_a', 1.0)
    if st.get('labels', True) and LA > 0.01:
        k = cam.zoom
        chip(c, cam, None, 'API server', API_C, anchor_xy=(api_top[0], api_top[1] - 0.5*U*k), dy=-92, a=LA*st.get('api_a', 1.0))
        sx, sy = SCHED['p']
        chip(c, cam, (sx - 0.6, sy + 0.6, CP_Z + SCHED['h']*0.5), 'scheduler', SCHED_C, dx=-150, dy=-30, a=LA)
        cx_, cy_ = CTRL['p']
        chip(c, cam, (cx_ + 0.6, cy_ - 0.6, CP_Z + CTRL['h']*0.5), 'ReplicaSet', CTRL_C, dx=170, dy=-30,
             sub=st.get('rs_sub', f'ready {st.get("rs_ready", 3)}/3'), a=LA*st.get('rs_a', 1.0))
        chip(c, cam, (ex + ETCD['r']*0.9, ey - ETCD['r']*0.9, CP_Z + ETCD['h']*0.55), 'etcd', ETCD_C, dx=210, dy=10,
             sub=st.get('etcd_sub', 'replicas: 3'), a=LA*st.get('etcd_a', 1.0))
        names = ['node-1', 'node-2', 'node-3']
        for i in range(3):
            ready = st['nodes'][i] == 'ready'
            node_label(c, cam, i, names[i], 'Ready' if ready else 'NotReady', RUN_C if ready else DEAD_C, a=LA)
        for (i, s), stt in (st['pods'].items() if st.get('pod_chips', True) else []):
            stt, kk = stt if isinstance(stt, tuple) else (stt, 1.0)
            ca_ = {'run': 1.0, 'dying': 1.0, 'shatter': 1 - kk, 'ghost': 1.0, 'born': 1.0}.get(stt, 0.0)
            colc = {'run': RUN_C, 'born': RUN_C, 'ghost': PEND_C}.get(stt, DEAD_C)
            if ca_ > 0.01:
                x, y = slot_xy(i, s)
                p3 = (x + POD/2, y + POD/2, NODE_TOP + POD)
                chip(c, cam, p3, st['pod_names'][(i, s)], colc, dy=-64, size=24, a=ca_*LA)
    if st.get('post'):
        st['post'](c, cam, t)
    particles(c, t)


def render_closeup(who_img, cam, st, t=0.0, cap=None, out=None, scale=1.12):
    """Dialogue close-up: the world, defocused, behind a character bust."""
    global _VIG
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    draw_world(c, cam, dict(st, labels=False), t)
    world = surf.makeImageSnapshot()
    c.clear(skia.ColorBLACK)
    p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(18, 18))
    c.drawImage(world, 0, 0, skia.SamplingOptions(), p)
    c.drawRect(skia.Rect(0, 0, W, H), P(hexc('#0b0618'), 0.35))
    glow(c, W/2, 860, 520, hexc('#8a5cd0'), 0.28)
    img = skia.Image.open(who_img)
    bw, bh = img.width()*scale, img.height()*scale
    c.drawImageRect(img, skia.Rect((W - bw)/2, 1560 - bh, (W + bw)/2, 1560), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 1380), skia.Point(0, 1570)],
                                        [ca(hexc('#07040f'), 0).toColor(), ca(hexc('#07040f'), 1).toColor()])
    c.drawRect(skia.Rect(0, 1380, W, 1570), skia.Paint(Shader=sh))
    c.drawRect(skia.Rect(0, 1569, W, H), P(hexc('#07040f')))
    if _VIG is None:
        _VIG = vignette()
    c.drawImage(_VIG, 0, 0)
    hud(c, st.get('running', 3))
    if cap:
        caption(c, *cap)
    out_img = surf.makeImageSnapshot()
    if out:
        out_img.save(out)
    return out_img


def render_frame(cam, st, t=0.0, cap=None, out=None):
    global _VIG
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    draw_world(c, cam, st, t)
    if _VIG is None:
        _VIG = vignette()
    c.drawImage(_VIG, 0, 0)
    hud(c, st.get('running', 3))
    if cap:
        caption(c, *cap)
    img = surf.makeImageSnapshot()
    if out:
        img.save(out)
    return img


