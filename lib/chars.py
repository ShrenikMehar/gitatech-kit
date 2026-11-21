"""Code-drawn flat-vector Krishna & Arjun (bust). SVG generated in Python, rendered with skia.SVGDOM.

Canvas 900x1100, face centre x=450. Light: warm key from upper-left, cyan rim from the right.
build(who, **expr) -> svg string.
expr: eye (openness), brow, mouth, gaze=(dx,dy), blink, serene, tilt (deg).
"""
import math

W, H = 900, 1100
CX = 450

PAL = {
    'krishna': dict(skin='#4A66D2', light='#8CA8F6', shadow='#2C389C', deep='#1A1F66', blush='#B87CEE',
                    lip='#B4305E', lip_l='#DE6488', hair='#120E2C', hair_m='#221C4C', hair_hl='#4A4894',
                    iris='#2A160C', brow='#110B24', lash='#0D091C', rim='#A8F0FF'),
    'arjun': dict(skin='#C98A5E', light='#EEBF92', shadow='#91543A', deep='#5E301C', blush='#D9705A',
                  lip='#94473F', lip_l='#B9685A', hair='#150F18', hair_m='#271D2C', hair_hl='#55465E',
                  iris='#28160B', brow='#160E12', lash='#120A0E', rim='#A8F0FF'),
}
GEO = {
    'krishna': dict(nose=536, mouth=588, chin=646, neck=66, mouth_w=28),
    'arjun': dict(nose=540, mouth=596, chin=656, neck=78, mouth_w=30),
}
BODY_UP = 48
GOLD = dict(l='#FFF1B8', m='#F3BE4E', d='#B8711C', dd='#6E3E0C')


# ---------------------------------------------------------------- helpers
def f(v):
    return f'{v:.1f}'.rstrip('0').rstrip('.')


def P(x, y):
    return f'{f(x)} {f(y)}'


def X(dx, s=1):
    return CX + s*dx


def cubic(p0, p1, p2, p3, t):
    u = 1 - t
    return (u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
            u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1])


def sample_cubic(seg, n=24):
    return [cubic(*seg, k/n) for k in range(n+1)]


def catmull(pts, n=10):
    out = []
    pts = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i-1], pts[i], pts[i+1], pts[i+2]
        for k in range(n):
            t = k / n
            t2, t3 = t*t, t*t*t
            out.append(tuple(0.5*((2*p1[j]) + (-p0[j]+p2[j])*t + (2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2 +
                                  (-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t3) for j in range(2)))
    out.append(pts[-2])
    return out


def poly(pts, close=True):
    s = 'M' + ' L'.join(P(*p) for p in pts)
    return s + (' Z' if close else '')


def normals(cl):
    out = []
    n = len(cl)
    for i in range(n):
        a, b = cl[max(0, i-1)], cl[min(n-1, i+1)]
        tx, ty = b[0]-a[0], b[1]-a[1]
        d = math.hypot(tx, ty) or 1
        out.append((-ty/d, tx/d))
    return out


def ribbon(cl, wfun, shift=0.0):
    L, R = [], []
    nm = normals(cl)
    n = len(cl)
    for i, p in enumerate(cl):
        nx, ny = nm[i]
        w = wfun(i/(n-1)) / 2
        o = shift * w
        L.append((p[0]+nx*(w+o), p[1]+ny*(w+o)))
        R.append((p[0]-nx*(w-o), p[1]-ny*(w-o)))
    return poly(L + R[::-1])


def spiral_tail(cl, r, turns=1.1, side=1, n=26):
    (x0, y0), (x1, y1) = cl[-2], cl[-1]
    tx, ty = x1-x0, y1-y0
    d = math.hypot(tx, ty) or 1
    tx, ty = tx/d, ty/d
    nx, ny = -ty*side, tx*side
    cx, cy = x1 + nx*r, y1 + ny*r
    a0 = math.atan2(y1-cy, x1-cx)
    out = []
    for k in range(1, n+1):
        t = k/n
        a = a0 - side*t*turns*2*math.pi
        rr = r*(1 - 0.6*t)
        out.append((cx + math.cos(a)*rr, cy + math.sin(a)*rr))
    return cl + out


def mirror_path(segs, close=True):
    p0 = segs[0][0]
    d = f'M{P(X(p0[0]), p0[1])}'
    for (_, c1, c2, p3) in segs:
        d += f' C{P(X(c1[0]), c1[1])} {P(X(c2[0]), c2[1])} {P(X(p3[0]), p3[1])}'
    for (q0, c1, c2, _) in reversed(segs):
        d += f' C{P(X(c2[0], -1), c2[1])} {P(X(c1[0], -1), c1[1])} {P(X(q0[0], -1), q0[1])}'
    return d + (' Z' if close else '')


def ell(cx, cy, rx, ry, rot=0):
    """Ellipse as a path (skia's <ellipse> drops gradient fills)."""
    pts = []
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for k in range(48):
        a = 2*math.pi*k/48
        x, y = rx*math.cos(a), ry*math.sin(a)
        pts.append((cx + x*cr - y*sr, cy + x*sr + y*cr))
    return poly(pts)


def blur(sd):
    return f'filter="url(#b{sd})"'


BLURS = (1, 2, 3, 4, 6, 8, 10, 14, 20, 28)
_uid = [0]


def uid(p):
    _uid[0] += 1
    return f'{p}{_uid[0]}'


def rim(path_d, c, x1, x2, width=7, op=0.9, extra=''):
    """Inner rim light on the right edge: stroke clipped inside the shape, faded in with a userSpace gradient."""
    gid, cid = uid('rg'), uid('rc')
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{f(x1)}" y1="0" x2="{f(x2)}" y2="0">'
            f'<stop offset="0" stop-color="{c["rim"]}" stop-opacity="0"/><stop offset="1" stop-color="{c["rim"]}" stop-opacity="{op}"/></linearGradient>'
            f'<clipPath id="{cid}"><path d="{path_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})"><path d="{path_d}" fill="none" stroke="url(#{gid})" stroke-width="{width}" {extra}/></g>')


def defs_common(c):
    out = []
    for sd in BLURS:
        out.append(f'<filter id="b{sd}" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="{sd}"/></filter>')
    out.append(f'''<linearGradient id="gold" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{GOLD['l']}"/><stop offset="0.3" stop-color="{GOLD['m']}"/>
      <stop offset="0.75" stop-color="{GOLD['d']}"/><stop offset="1" stop-color="{GOLD['dd']}"/></linearGradient>''')
    out.append(f'''<linearGradient id="goldv" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{GOLD['l']}"/><stop offset="0.45" stop-color="{GOLD['m']}"/>
      <stop offset="1" stop-color="{GOLD['d']}"/></linearGradient>''')
    out.append(f'''<radialGradient id="skinG" cx="0.34" cy="0.3" r="0.9">
      <stop offset="0" stop-color="{c['light']}"/><stop offset="0.5" stop-color="{c['skin']}"/>
      <stop offset="1" stop-color="{c['shadow']}"/></radialGradient>''')
    out.append(f'''<linearGradient id="hairG" gradientUnits="userSpaceOnUse" x1="150" y1="0" x2="760" y2="0">
      <stop offset="0" stop-color="{c['hair_m']}"/><stop offset="0.3" stop-color="{c['hair']}"/>
      <stop offset="0.7" stop-color="{c['hair']}"/><stop offset="1" stop-color="{c['hair_m']}"/></linearGradient>''')
    for k, (a, b, cc) in {'r': ('#FF9AA6', '#E0213F', '#6A0718'), 'g': ('#B6FFD0', '#1FA35C', '#064424'),
                          'b': ('#BFE0FF', '#2A6FE0', '#0A1F66'), 't': ('#C8FFF6', '#16B3A6', '#05504A'),
                          'pearl': ('#FFFFFF', '#EDE6DA', '#A89C8C')}.items():
        gid = 'pearl' if k == 'pearl' else f'gem_{k}'
        out.append(f'<radialGradient id="{gid}" cx="0.35" cy="0.3" r="0.8"><stop offset="0" stop-color="{a}"/>'
                   f'<stop offset="0.5" stop-color="{b}"/><stop offset="1" stop-color="{cc}"/></radialGradient>')
    return out


def gem(x, y, r, kind='r', setting=True):
    s = ''
    if setting:
        s += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r*1.38)}" fill="url(#goldv)" stroke="{GOLD["dd"]}" stroke-width="{f(max(1, r*0.14))}"/>'
    s += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="url(#gem_{kind})"/>'
    s += f'<circle cx="{f(x - r*0.35)}" cy="{f(y - r*0.38)}" r="{f(r*0.28)}" fill="#fff" opacity="0.85"/>'
    return s


def pearls_along(pts, r):
    return ''.join(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="url(#pearl)"/>' for (x, y) in pts)


# ---------------------------------------------------------------- face
FACE = {
    'krishna': [((0, 278), (82, 278), (140, 322), (142, 400)),
                ((142, 400), (143, 446), (139, 482), (132, 512)),
                ((132, 512), (122, 556), (102, 594), (74, 618)),
                ((74, 618), (52, 636), (26, 646), (0, 646))],
    'arjun': [((0, 274), (86, 274), (148, 318), (150, 400)),
              ((150, 400), (151, 452), (149, 490), (145, 524)),
              ((145, 524), (140, 562), (128, 594), (102, 620)),
              ((102, 620), (76, 644), (40, 656), (0, 656))],
}


def eye_shape(o_up, o_lo, who):
    if who == 'krishna':
        ic, oc = (18, 474), (112, 460)
        u1, u2, l1, l2 = (32, 448), (84, 438), (94, 488), (40, 492)
    else:
        ic, oc = (20, 474), (110, 464)
        u1, u2, l1, l2 = (34, 453), (84, 446), (92, 486), (42, 489)

    def base_y(dx):
        t = (dx - ic[0]) / (oc[0] - ic[0])
        return ic[1] + (oc[1] - ic[1]) * t

    def sc(p, o):
        b = base_y(p[0])
        return (p[0], b + (p[1] - b) * o)
    return (ic, sc(u1, o_up), sc(u2, o_up), oc), (oc, sc(l1, o_lo), sc(l2, o_lo), ic)


def seg_s(seg, s):
    return tuple((X(p[0], s), p[1]) for p in seg)


def eye(s, c, who, o=1.0, gaze=(0, 0), blink=False, serene=0.0, cheek=0.0, iris=1.0):
    out = []
    if blink or o < 0.08:
        up, _ = eye_shape(0, 0, who)
        ic, oc = up[0], up[3]
        closed = (ic, (42, ic[1] + 12), (88, oc[1] + 10), oc)
        pts = sample_cubic(seg_s(closed, s), 28)
        out.append(f'<path d="{ribbon(pts, lambda t: 2.2 + 4.6*math.sin(math.pi*min(1, t*1.1)))}" fill="{c["lash"]}"/>')
        out.append(f'<path d="M{P(X(oc[0], s), oc[1])} Q{P(X(oc[0]+9, s), oc[1]-2)} {P(X(oc[0]+15, s), oc[1]-9)}" stroke="{c["lash"]}" stroke-width="3.4" fill="none" stroke-linecap="round"/>')
        cr = [(x, y - 10) for (x, y) in sample_cubic(seg_s(closed, s), 20)][4:17]
        out.append(f'<path d="{poly(cr, False)}" stroke="{c["deep"]}" stroke-width="2" fill="none" opacity="0.35" stroke-linecap="round"/>')
        return ''.join(out)
    up, lo = eye_shape(o * (1 - serene), min(1.18, o) * (1 - cheek), who)
    ups, los = seg_s(up, s), seg_s(lo, s)
    d = f'M{P(*ups[0])} C{P(*ups[1])} {P(*ups[2])} {P(*ups[3])} C{P(*los[1])} {P(*los[2])} {P(*los[3])} Z'
    cid = uid('eye')
    out.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
    out.append(f'<path d="{d}" fill="#F3ECE6"/>')
    gx, gy = gaze
    ix, iy = X(64, s) + gx, 468 + gy
    r_ir = (20 if who == 'krishna' else 18.5) * iris
    out.append(f'<g clip-path="url(#{cid})">')
    out.append(f'<circle cx="{f(ix)}" cy="{f(iy)}" r="{f(r_ir)}" fill="{c["iris"]}"/>')
    out.append(f'<path d="{ell(ix, iy + 6, r_ir*0.78, r_ir*0.6)}" fill="#7A4A2A" opacity="0.55" {blur(2)}/>')
    out.append(f'<circle cx="{f(ix)}" cy="{f(iy)}" r="{f(r_ir*0.42)}" fill="#050203"/>')
    sh = sample_cubic(ups, 20)
    out.append(f'<path d="{poly(sh + [(x, y + 11) for (x, y) in sh[::-1]])}" fill="#2A1530" opacity="0.4" {blur(2)}/>')
    out.append(f'<circle cx="{f(ix + 7)}" cy="{f(iy - 6)}" r="5.2" fill="#fff"/>')
    out.append(f'<circle cx="{f(ix - 6)}" cy="{f(iy + 8)}" r="2.2" fill="#fff" opacity="0.75"/>')
    out.append('</g>')
    pts = sample_cubic(ups, 30)
    lw = 5.6 if who == 'krishna' else 4.0
    out.append(f'<path d="{ribbon(pts, lambda t: 2.4 + lw*math.sin(math.pi*(0.12 + 0.82*t))*(0.55 + 0.45*t), shift=0.6)}" fill="{c["lash"]}"/>')
    oc = ups[3]
    wl = 1.0 if who == 'krishna' else 0.45
    wing = (f'M{P(oc[0] - 4*s, oc[1] - 4)} Q{P(oc[0] + 10*wl*s, oc[1] - 5*wl)} {P(oc[0] + 18*wl*s, oc[1] - 13*wl)} '
            f'Q{P(oc[0] + 9*wl*s, oc[1] + 1)} {P(oc[0] - 2*s, oc[1] + 2)} Z')
    out.append(f'<path d="{wing}" fill="{c["lash"]}"/>')
    lpts = sample_cubic(los, 24)[3:-4]
    out.append(f'<path d="{poly(lpts, False)}" stroke="{c["lash"]}" stroke-width="1.8" fill="none" opacity="0.5" stroke-linecap="round"/>')
    base_up = seg_s(eye_shape(1, 1, who)[0], s)
    cpts = [(x, y - 12 - 3*math.sin(math.pi*i/20)) for i, (x, y) in enumerate(sample_cubic(base_up, 20))][4:18]
    out.append(f'<path d="{poly(cpts, False)}" stroke="{c["deep"]}" stroke-width="2.2" fill="none" opacity="0.4" stroke-linecap="round"/>')
    return ''.join(out)


BROWS = {
    'krishna': {'calm': [(24, 430), (80, 413), (126, 424)], 'neutral': [(22, 428), (78, 409), (126, 420)],
                'raise': [(22, 414), (78, 396), (126, 408)], 'soft': [(22, 424), (78, 410), (126, 424)]},
    'arjun': {'neutral': [(20, 425), (78, 413), (128, 421)], 'worry': [(20, 402), (70, 403), (128, 428)],
              'panic': [(20, 388), (70, 384), (128, 404)], 'relief': [(20, 424), (78, 412), (128, 424)],
              'raise': [(20, 414), (78, 400), (128, 408)], 'angry': [(20, 438), (74, 420), (128, 414)]},
}


def brow(s, c, who, kind):
    pts = [(X(dx, s), y) for dx, y in BROWS[who][kind]]
    cl = catmull(pts, 14)
    w0 = 11 if who == 'krishna' else 15
    return f'<path d="{ribbon(cl, lambda t: 2.2 + (w0-2.2)*(1-t)**0.75*(0.85 + 0.15*math.sin(math.pi*t)))}" fill="{c["brow"]}"/>'


MOUTHS = {  # open, smile, roundness, width scale
    'rest': (0, 0, 0, 1.0), 'smile': (0, 10, 0, 1.16), 'talk1': (8, 1, 0.1, 0.96), 'talk2': (16, 1, 0.2, 0.94),
    'smile_talk': (10, 6, 0.05, 1.04), 'panic': (30, -2, 0.6, 0.86), 'worry': (0, -3, 0, 0.94),
    'worry_talk': (11, -2, 0.25, 0.9), 'oh': (14, 0, 0.7, 0.72),
}


def mouth(c, who, kind, base_smile=0.0):
    y0 = GEO[who]['mouth']
    op, sm, rnd, ws = MOUTHS[kind]
    sm += base_smile if kind in ('rest', 'talk1', 'talk2') else 0
    w = GEO[who]['mouth_w'] * ws
    wi = w * (1 - 0.3*rnd)
    out = []
    lift = op * 0.25
    if rnd > 0.3:
        ue = [(CX - wi, y0 - sm + 2), (CX - wi*0.7, y0 - op*0.35), (CX + wi*0.7, y0 - op*0.35), (CX + wi, y0 - sm + 2)]
        le = [(CX + wi, y0 - sm + 2), (CX + wi*0.75, y0 + op), (CX - wi*0.75, y0 + op), (CX - wi, y0 - sm + 2)]
    else:
        ue = [(CX - wi, y0 - sm), (CX - wi*0.5, y0 - 2 - lift), (CX + wi*0.5, y0 - 2 - lift), (CX + wi, y0 - sm)]
        le = [(CX + wi, y0 - sm), (CX + wi*0.55, y0 + op), (CX - wi*0.55, y0 + op), (CX - wi, y0 - sm)]
    bow_y = y0 - 10 - lift - (op*0.35 if rnd > 0.3 else 0)
    thick = 1.0 if who == 'krishna' else 0.8
    ul = (f'M{P(CX - w - 2, y0 - sm)} C{P(CX - w*0.6, y0 - sm - 4*thick)} {P(CX - 15, bow_y - 2*thick)} {P(CX - 7, bow_y)} '
          f'Q{P(CX, bow_y + 4)} {P(CX + 7, bow_y)} C{P(CX + 15, bow_y - 2*thick)} {P(CX + w*0.6, y0 - sm - 4*thick)} {P(CX + w + 2, y0 - sm)} '
          f'L{P(*ue[3])} C{P(*ue[2])} {P(*ue[1])} {P(*ue[0])} Z')
    lb = y0 + op + 13*thick - (2 if rnd > 0.3 else 0)
    ll = (f'M{P(*le[3])} C{P(*le[2])} {P(*le[1])} {P(*le[0])} '
          f'L{P(CX + w - 1, y0 - sm + 1)} C{P(CX + w*0.55, lb)} {P(CX - w*0.55, lb)} {P(CX - w + 1, y0 - sm + 1)} Z')
    if op > 0:
        inner = f'M{P(*ue[0])} C{P(*ue[1])} {P(*ue[2])} {P(*ue[3])} C{P(*le[1])} {P(*le[2])} {P(*le[3])} Z'
        mid = uid('m')
        out.append(f'<clipPath id="{mid}"><path d="{inner}"/></clipPath>')
        out.append(f'<path d="{inner}" fill="#2A0A14"/>')
        out.append(f'<g clip-path="url(#{mid})">')
        out.append(f'<rect x="{f(CX - w)}" y="{f(y0 - 14 - lift)}" width="{f(2*w)}" height="{f(11 + min(4, op*0.25))}" rx="3" fill="#F3EEE6"/>')
        out.append(f'<path d="{ell(CX, y0 + op + 5, wi*0.62, max(4, op*0.45))}" fill="#B04862"/>')
        out.append('</g>')
    out.append(f'<path d="{ul}" fill="{c["lip"]}"/>')
    out.append(f'<path d="{ll}" fill="{c["lip_l"]}"/>')
    out.append(f'<path d="{ell(CX - 5, y0 + op + 6*thick, 9, 2.6)}" fill="#fff" opacity="0.26"/>')
    if op == 0:
        line = f'M{P(CX - w - 2, y0 - sm)} C{P(CX - w*0.5, y0 + 2)} {P(CX + w*0.5, y0 + 2)} {P(CX + w + 2, y0 - sm)}'
        out.append(f'<path d="{line}" stroke="{c["deep"]}" stroke-width="2.4" fill="none" stroke-linecap="round" opacity="0.85"/>')
    for s in (-1, 1):
        out.append(f'<path d="M{P(CX + s*(w+1), y0 - sm - 1)} q{f(s*4)} {f(-1 - sm*0.3)} {f(s*5)} {f(-3 - sm*0.35)}" stroke="{c["deep"]}" stroke-width="1.7" fill="none" opacity="0.5" stroke-linecap="round"/>')
    return ''.join(out)


def mustache(c, who, lift=0.0):
    y0 = GEO[who]['mouth']
    o = []
    lw = (0, 0.1, 0.35, 0.7, 1.0)
    for s in (-1, 1):
        pts = [(3, -15), (15, -18), (29, -16), (41, -11), (49, -11)]
        cl = catmull([(X(dx + 2*lift*lw[j]*0.3, s), y0 + dy - lift*0.9*lw[j]) for j, (dx, dy) in enumerate(pts)], 10)
        o.append(f'<path d="{ribbon(cl, lambda t: 2.5 + 9*math.sin(math.pi*min(1, 0.2 + t*0.85))*(1 - 0.6*t), shift=0.3*-1)}" fill="{c["hair_m"]}"/>')
        hl = cl[5:28]
        o.append(f'<path d="{ribbon(hl, lambda t: 2.2*math.sin(math.pi*t), shift=0.8*-1)}" fill="{c["hair_hl"]}" opacity="0.6"/>')
    return ''.join(o)


def nose(c, who):
    ny = GEO[who]['nose']
    o = []
    o.append(f'<path d="M{P(X(8), 470)} C{P(X(14), 496)} {P(X(22), ny - 18)} {P(X(26), ny + 2)} L{P(X(12), ny + 8)} C{P(X(10), ny - 18)} {P(X(5), 494)} {P(X(0), 470)} Z" fill="{c["shadow"]}" opacity="0.55" {blur(3)}/>')
    o.append(f'<path d="{ell(X(-4), 505, 4.5, 30)}" fill="{c["light"]}" opacity="0.35" {blur(3)}/>')
    o.append(f'<path d="{ell(X(-4), ny + 1, 7, 5)}" fill="{c["light"]}" opacity="0.6" {blur(2)}/>')
    # side line flowing into the nostril (shadow side), small nostril on light side
    o.append(f'<path d="M{P(X(14), ny - 30)} C{P(X(18), ny - 16)} {P(X(26), ny - 2)} {P(X(20), ny + 7)} C{P(X(16), ny + 11)} {P(X(10), ny + 10)} {P(X(6), ny + 8)}" stroke="{c["deep"]}" stroke-width="2.2" fill="none" opacity="0.55" stroke-linecap="round"/>')
    o.append(f'<path d="M{P(X(-6), ny + 8)} C{P(X(-10), ny + 10)} {P(X(-16), ny + 10)} {P(X(-19), ny + 6)}" stroke="{c["deep"]}" stroke-width="2" fill="none" opacity="0.4" stroke-linecap="round"/>')
    o.append(f'<path d="{ell(X(4), ny + 20, 18, 4)}" fill="{c["shadow"]}" opacity="0.35" {blur(3)}/>')
    return ''.join(o)


def face_shading(c, who):
    g = GEO[who]
    o = []
    sh = (f'M{P(X(98), 300)} C{P(X(114), 360)} {P(X(118), 420)} {P(X(106), 470)} C{P(X(98), 505)} {P(X(102), 540)} {P(X(94), 572)} '
          f'C{P(X(86), 606)} {P(X(56), g["chin"] - 14)} {P(X(4), g["chin"] + 8)} L{P(X(220), 700)} L{P(X(220), 260)} Z')
    o.append(f'<path d="{sh}" fill="{c["shadow"]}" opacity="0.6" {blur(4)}/>')
    o.append(f'<path d="{ell(CX, 380, 175, 28)}" fill="{c["deep"]}" opacity="0.55" {blur(10)}/>')
    for s in (-1, 1):
        o.append(f'<path d="{ell(X(62, s), 452, 56, 22)}" fill="{c["shadow"]}" opacity="{0.2 if s < 0 else 0.3}" {blur(8)}/>')
        o.append(f'<path d="{ell(X(82, s), g["nose"], 28, 14)}" fill="{c["blush"]}" opacity="0.32" {blur(8)}/>')
    o.append(f'<path d="{ell(X(-34), 404, 64, 16)}" fill="{c["light"]}" opacity="0.3" {blur(10)}/>')
    if who == 'arjun':
        for s in (-1, 1):
            o.append(f'<path d="{ell(X(112, s), 566, 20, 44, -12*s)}" fill="{c["shadow"]}" opacity="{0.22 if s < 0 else 0.3}" {blur(10)}/>')
        o.append(f'<path d="{ell(CX, g["chin"] - 6, 34, 10)}" fill="{c["shadow"]}" opacity="0.18" {blur(6)}/>')
    o.append(f'<path d="{ell(X(-90), 500, 26, 22)}" fill="{c["light"]}" opacity="0.3" {blur(10)}/>')
    o.append(f'<path d="{ell(X(-4), g["chin"] - 14, 20, 8)}" fill="{c["light"]}" opacity="0.18" {blur(6)}/>')
    o.append(f'<path d="{ell(CX, g["mouth"] + 26, 18, 5)}" fill="{c["shadow"]}" opacity="0.38" {blur(3)}/>')
    return ''.join(o)


def ear(s, c):
    d = f'M{P(X(136, s), 452)} C{P(X(156, s), 438)} {P(X(168, s), 462)} {P(X(164, s), 490)} C{P(X(161, s), 514)} {P(X(151, s), 532)} {P(X(136, s), 530)} Z'
    inner = f'M{P(X(142, s), 462)} C{P(X(156, s), 458)} {P(X(158, s), 482)} {P(X(152, s), 500)} C{P(X(150, s), 510)} {P(X(146, s), 512)} {P(X(143, s), 508)}'
    return (f'<path d="{d}" fill="{c["skin"] if s < 0 else c["shadow"]}"/>'
            f'<path d="{inner}" stroke="{c["deep"]}" stroke-width="3" fill="none" opacity="0.5" stroke-linecap="round"/>')


# ---------------------------------------------------------------- hair
def wavy_edge(pts, amp, period, phase=0.0):
    """Push points outward along their normals with a scalloped (curly) profile."""
    nm = normals(pts)
    out, acc = [], 0.0
    for i, p in enumerate(pts):
        if i:
            acc += math.hypot(p[0]-pts[i-1][0], p[1]-pts[i-1][1])
        k = abs(math.sin(math.pi*acc/period + phase))**0.6
        out.append((p[0] + nm[i][0]*amp*k, p[1] + nm[i][1]*amp*k))
    return out


def hair_back(c, who):
    if who == 'krishna':
        right = catmull([(X(0), 240), (X(110), 250), (X(180), 300), (X(198), 380), (X(204), 470), (X(222), 560), (X(250), 650), (X(270), 740), (X(266), 820)], 10)
        right = wavy_edge(right, -9, 46)
    else:
        right = catmull([(X(0), 238), (X(112), 248), (X(182), 300), (X(198), 380), (X(204), 480), (X(216), 600), (X(240), 720), (X(258), 860), (X(250), 960)], 10)
    left = [(2*CX - x, y) for (x, y) in right]
    d = poly(right + [(X(150), 1000), (X(-150), 1000)] + left[::-1])
    o = [f'<path d="{d}" fill="url(#hairG)"/>']
    # inner occlusion near the neck
    o.append(f'<path d="{ell(CX, 640, 120, 160)}" fill="#05030C" opacity="0.55" {blur(20)}/>')
    # strand highlight bands (soft shapes, not lines)
    for s in (-1, 1):
        for (dx, y1, y2, w) in ((172, 400, 720, 10), (204, 470, 790, 8)):
            cl = catmull([(X(dx, s), y1), (X(dx + 10, s), y1 + 100), (X(dx + 2, s), y1 + 200), (X(dx + 22, s), y2)], 10)
            o.append(f'<path d="{ribbon(cl, lambda t, w=w: w*math.sin(math.pi*t))}" fill="{c["hair_hl"]}" opacity="{0.4 if s < 0 else 0.2}" {blur(1)}/>')
    return ''.join(o)


def lock(c, pts, w0, s, hook=0.0, hook_r=16, end_w=0.55):
    """A shaped hair lock: widens, S-curves, ends in a soft inward hook (not a tight spiral)."""
    cl = catmull(pts, 12)
    n_main = len(cl)
    if hook:
        cl = spiral_tail(cl, hook_r, turns=hook, side=-s, n=18)
    N = len(cl)
    tm = n_main / N

    def wf(t):
        if t <= tm:
            u = t / tm
            return w0 * (0.4 + 0.6*math.sin(0.5*math.pi*min(1, u*2.6 + 0.08))) * (1 - (1 - end_w)*u**1.6)
        u = (t - tm) / max(1e-6, 1 - tm)
        return w0 * end_w * (1 - 0.7*u**1.3)
    o = [f'<path d="{ribbon(cl, wf)}" fill="{c["hair"]}"/>']
    body = cl[4:n_main - 2]
    for k, (sh, wk, op) in enumerate(((-0.55, 0.22, 0.8), (0.25, 0.12, 0.45))):
        o.append(f'<path d="{ribbon(body, lambda t, wk=wk: w0*wk*math.sin(math.pi*t), shift=sh*s*-1)}" fill="{c["hair_hl"]}" opacity="{op*(1 if s < 0 else 0.6)}"/>')
    return ''.join(o)


def hair_locks(c, who):
    o = []
    for s in (-1, 1):
        if who == 'krishna':
            o.append(lock(c, [(X(196, s), 470), (X(226, s), 570), (X(214, s), 670), (X(240, s), 770), (X(232, s), 840)], 50, s, end_w=0.12))
            o.append(lock(c, [(X(152, s), 456), (X(176, s), 546), (X(162, s), 636), (X(184, s), 724), (X(176, s), 796)], 46, s, end_w=0.12))
        else:
            o.append(lock(c, [(X(160, s), 460), (X(182, s), 560), (X(176, s), 660), (X(196, s), 760), (X(192, s), 860)], 54, s, end_w=0.15))
    return ''.join(o)


def hair_side(c, who):
    """Small temple curl / sideburn in front of the ear."""
    o = []
    for s in (-1, 1):
        if who == 'krishna':
            cl = catmull([(X(128, s), 384), (X(140, s), 420), (X(138, s), 448)], 10)
            cl = spiral_tail(cl, 7, turns=0.95, side=-s)
            o.append(f'<path d="{ribbon(cl, lambda t: 13*(1 - 0.75*t))}" fill="{c["hair"]}"/>')
        elif False:
            o.append(f'<path d="M{P(X(132, s), 392)} C{P(X(146, s), 420)} {P(X(148, s), 448)} {P(X(146, s), 474)} C{P(X(140, s), 456)} {P(X(134, s), 432)} {P(X(122, s), 398)} Z" fill="{c["hair"]}"/>')
    return ''.join(o)


# ---------------------------------------------------------------- crowns
def band(gemkind='r', flare=False):
    o = []
    d = (f'M{P(X(-156), 334)} C{P(X(-90), 356)} {P(X(90), 356)} {P(X(156), 334)} L{P(X(160), 368)} '
         f'C{P(X(92), 394)} {P(X(-92), 394)} {P(X(-160), 368)} Z')
    if flare:
        for s in (-1, 1):
            o.append(f'<path d="M{P(X(152, s), 338)} C{P(X(166, s), 334)} {P(X(176, s), 326)} {P(X(182, s), 316)} C{P(X(182, s), 336)} {P(X(174, s), 354)} {P(X(160, s), 366)} Z" fill="url(#goldv)" stroke="{GOLD["dd"]}" stroke-width="2"/>')
    o.append(f'<path d="{d}" fill="url(#goldv)" stroke="{GOLD["dd"]}" stroke-width="2.5"/>')
    o.append(f'<path d="M{P(X(-158), 362)} C{P(X(-92), 388)} {P(X(92), 388)} {P(X(158), 362)}" stroke="{GOLD["dd"]}" stroke-width="3" fill="none" opacity="0.55"/>')
    t_pts = sample_cubic(((X(-150), 340), (X(-88), 360), (X(88), 360), (X(150), 340)), 22)
    b_pts = sample_cubic(((X(-152), 369), (X(-88), 391), (X(88), 391), (X(152), 369)), 22)
    o.append(pearls_along(t_pts[1:-1], 3.2))
    o.append(pearls_along(b_pts[1:-1], 3.2))
    for k in (-2, -1, 1, 2):
        o.append(gem(X(k*54), 368 + (6 if abs(k) == 1 else 0), 5, 'g' if gemkind == 'r' else 'b'))
    o.append(gem(CX, 373, 10, gemkind))
    o.append(f'<path d="M{P(X(60), 344)} C{P(X(110), 348)} {P(X(140), 342)} {P(X(160), 336)} L{P(X(162), 368)} C{P(X(130), 380)} {P(X(100), 386)} {P(X(60), 390)} Z" fill="{GOLD["dd"]}" opacity="0.3" {blur(4)}/>')
    return ''.join(o)


def feather(x0, y0, x1, y1, sc=1.0):
    o = []
    mx, my = (x0 + x1)/2 + 34*sc, (y0 + y1)/2 + 12*sc
    pts = [((1-t)**2*x0 + 2*(1-t)*t*mx + t*t*x1, (1-t)**2*y0 + 2*(1-t)*t*my + t*t*y1) for t in [k/70 for k in range(71)]]
    for i in range(5, 68):
        t = i/70
        (ax, ay), (bx, by) = pts[i-1], pts[i+1]
        dx, dy = bx-ax, by-ay
        d = math.hypot(dx, dy)
        dx, dy = dx/d, dy/d
        nx, ny = -dy, dx
        L = (12 + 52*math.sin(math.pi*min(1, t*1.04))**0.75) * sc
        px, py = pts[i]
        for s in (-1, 1):
            ex, ey = px + (nx*s*0.88 + dx*0.5)*L, py + (ny*s*0.88 + dy*0.5)*L
            col = ('#86B83C', '#4E9A4A', '#C9B24E')[(i + (s > 0)) % 3]
            o.append(f'<path d="M{P(px, py)} Q{P(px + nx*s*L*0.55 + dx*L*0.05, py + ny*s*L*0.55 + dy*L*0.05)} {P(ex, ey)}" stroke="{col}" stroke-width="1.7" fill="none" opacity="0.85"/>')
    o.append(f'<path d="{poly(pts, False)}" stroke="#F4E9B8" stroke-width="3.2" fill="none"/>')
    ex, ey = pts[58]
    ang = math.degrees(math.atan2(pts[60][1]-pts[56][1], pts[60][0]-pts[56][0])) + 90
    for (rx, ry, col) in ((46, 58, '#C9A23A'), (39, 49, '#2C9C68'), (28, 36, '#1E6CC0'), (17, 22, '#121A50')):
        o.append(f'<path d="{ell(ex, ey, rx*sc, ry*sc, ang)}" fill="{col}"/>')
    o.append(f'<path d="{ell(ex - 5, ey - 9, 5*sc, 7*sc, ang)}" fill="#fff" opacity="0.35"/>')
    return ''.join(o)


def crown_krishna():
    o = [feather(X(46), 266, X(156), 92, 1.08)]
    dome = (f'M{P(X(-152), 344)} C{P(X(-158), 268)} {P(X(-104), 210)} {P(X(-44), 184)} C{P(X(-24), 158)} {P(X(-9), 126)} {P(CX, 98)} '
            f'C{P(X(9), 126)} {P(X(24), 158)} {P(X(44), 184)} C{P(X(104), 210)} {P(X(158), 268)} {P(X(152), 344)} Z')
    o.append(f'<path d="{dome}" fill="url(#gold)" stroke="{GOLD["dd"]}" stroke-width="2"/>')
    o.append(f'<clipPath id="domeC"><path d="{dome}"/></clipPath><g clip-path="url(#domeC)">')
    for y, rx in ((300, 160), (256, 140), (218, 104)):
        o.append(f'<path d="M{P(X(-rx), y + 14)} Q{P(CX, y - 16)} {P(X(rx), y + 14)}" stroke="{GOLD["dd"]}" stroke-width="3" fill="none" opacity="0.5"/>')
        o.append(f'<path d="M{P(X(-rx), y + 17)} Q{P(CX, y - 13)} {P(X(rx), y + 17)}" stroke="{GOLD["l"]}" stroke-width="1.6" fill="none" opacity="0.6"/>')
    for k in range(-5, 6):
        o.append(f'<circle cx="{f(X(k*24))}" cy="{f(292 + k*k*0.9)}" r="2.6" fill="{GOLD["l"]}" opacity="0.9"/>')
    for k in range(-4, 5):
        bx, by = X(k*34), 330 + k*k*0.6
        o.append(f'<path d="M{P(bx - 15, by)} Q{P(bx - 14, by - 26)} {P(bx, by - 38)} Q{P(bx + 14, by - 26)} {P(bx + 15, by)} Z" fill="{GOLD["m"]}" stroke="{GOLD["dd"]}" stroke-width="2"/>')
        o.append(f'<path d="M{P(bx - 6, by - 4)} Q{P(bx - 5, by - 20)} {P(bx, by - 28)}" stroke="{GOLD["l"]}" stroke-width="2" fill="none" opacity="0.8"/>')
    o.append(f'<path d="M{P(X(40), 90)} C{P(X(120), 200)} {P(X(140), 280)} {P(X(140), 360)} L{P(X(200), 360)} L{P(X(200), 90)} Z" fill="{GOLD["dd"]}" opacity="0.42" {blur(6)}/>')
    o.append('</g>')
    o.append(gem(CX, 228, 11, 'r'))
    o.append(gem(X(-62), 268, 7, 'g'))
    o.append(gem(X(62), 268, 7, 'g'))
    o.append(f'<path d="M{P(CX - 9, 106)} Q{P(CX, 64)} {P(CX + 9, 106)} Z" fill="url(#goldv)"/>')
    o.append(f'<circle cx="{CX}" cy="62" r="7" fill="url(#goldv)" stroke="{GOLD["dd"]}" stroke-width="1.5"/>')
    o.append(band('r'))
    return ''.join(o)


def crown_arjun():
    o = []
    tiers = [(340, 150, 296, 132), (300, 134, 258, 112), (262, 114, 222, 90), (226, 92, 190, 66), (194, 68, 160, 42)]
    shapes = []
    for (yb, wb, yt, wt) in tiers:
        d = (f'M{P(X(-wb), yb)} C{P(X(-wb + 4), yb - 18)} {P(X(-wt - 6), yt + 10)} {P(X(-wt), yt)} Q{P(CX, yt - 18)} {P(X(wt), yt)} '
             f'C{P(X(wt + 6), yt + 10)} {P(X(wb - 4), yb - 18)} {P(X(wb), yb)} Q{P(CX, yb + 14)} {P(X(-wb), yb)} Z')
        shapes.append(d)
        o.append(f'<path d="{d}" fill="url(#gold)" stroke="{GOLD["dd"]}" stroke-width="2.5"/>')
        o.append(f'<path d="M{P(X(-wb + 8), yb - 4)} Q{P(CX, yb + 9)} {P(X(wb - 8), yb - 4)}" stroke="{GOLD["l"]}" stroke-width="2" fill="none" opacity="0.7"/>')
        n = max(3, int(wb / 18))
        for k in range(-n, n + 1):
            o.append(f'<circle cx="{f(X(k*(wb - 12)/n))}" cy="{f(yb - 12 - (k/n)**2*6)}" r="2.4" fill="{GOLD["l"]}"/>')
    spire = f'M{P(X(-42), 162)} C{P(X(-30), 130)} {P(X(-8), 100)} {P(CX, 66)} C{P(X(8), 100)} {P(X(30), 130)} {P(X(42), 162)} Z'
    o.append(f'<path d="{spire}" fill="url(#gold)" stroke="{GOLD["dd"]}" stroke-width="2.5"/>')
    cid = uid('cr')
    o.append(f'<clipPath id="{cid}">' + ''.join(f'<path d="{d}"/>' for d in shapes + [spire]) + '</clipPath>')
    o.append(f'<g clip-path="url(#{cid})"><path d="M{P(X(40), 60)} C{P(X(120), 190)} {P(X(150), 280)} {P(X(156), 360)} L{P(X(220), 360)} L{P(X(220), 60)} Z" fill="{GOLD["dd"]}" opacity="0.4" {blur(6)}/></g>')
    o.append(gem(CX, 58, 9, 'b'))
    o.append(gem(CX, 268, 8, 'b'))
    o.append(gem(CX, 200, 6, 'r'))
    o.append(band('b', flare=False))
    return ''.join(o)


# ---------------------------------------------------------------- bodies
def torso_path(who):
    if who == 'krishna':
        return (f'M{P(CX, 728)} C{P(X(-40), 728)} {P(X(-66), 736)} {P(X(-92), 752)} C{P(X(-156), 786)} {P(X(-262), 796)} {P(X(-314), 846)} '
                f'C{P(X(-350), 882)} {P(X(-360), 960)} {P(X(-364), 1180)} L{P(X(364), 1180)} C{P(X(360), 960)} {P(X(350), 882)} {P(X(314), 846)} '
                f'C{P(X(262), 796)} {P(X(156), 786)} {P(X(92), 752)} C{P(X(66), 736)} {P(X(40), 728)} {P(CX, 728)} Z')
    return (f'M{P(CX, 732)} C{P(X(-46), 732)} {P(X(-78), 740)} {P(X(-106), 756)} C{P(X(-176), 790)} {P(X(-286), 798)} {P(X(-340), 852)} '
            f'C{P(X(-378), 890)} {P(X(-388), 970)} {P(X(-392), 1180)} L{P(X(392), 1180)} C{P(X(388), 970)} {P(X(378), 890)} {P(X(340), 852)} '
            f'C{P(X(286), 798)} {P(X(176), 790)} {P(X(106), 756)} C{P(X(78), 740)} {P(X(46), 732)} {P(CX, 732)} Z')


def neck(c, who):
    w = GEO[who]['neck']
    d = (f'M{P(X(-w + 8), 580)} C{P(X(-w + 4), 630)} {P(X(-w), 680)} {P(X(-w - 16), 740)} L{P(X(w + 16), 740)} '
         f'C{P(X(w), 680)} {P(X(w - 4), 630)} {P(X(w - 8), 580)} Z')
    o = [f'<path d="{d}" fill="{c["skin"]}"/>']
    cid = uid('neck')
    o.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">')
    ch = GEO[who]['chin']
    o.append(f'<path d="M{P(X(-100), 580)} C{P(X(-70), ch + 8)} {P(X(70), ch + 26)} {P(X(100), 580)} L{P(X(100), 540)} L{P(X(-100), 540)} Z" fill="{c["deep"]}" opacity="0.75" {blur(8)}/>')
    o.append(f'<rect x="{X(w*0.2)}" y="580" width="{w*1.2}" height="200" fill="{c["shadow"]}" opacity="0.55" {blur(8)}/>')
    o.append(f'<path d="{ell(X(-w*0.45), 704, 12, 46)}" fill="{c["light"]}" opacity="0.22" {blur(8)}/>')
    if who == 'arjun':
        o.append(f'<path d="M{P(X(-30), 700)} Q{P(CX, 724)} {P(X(30), 700)}" stroke="{c["deep"]}" stroke-width="3" fill="none" opacity="0.25" {blur(2)}/>')
    o.append('</g>')
    o.append(rim(d, c, X(w*0.2), X(w + 10), 7, 0.75))
    return ''.join(o)


def body_krishna(c):
    o = []
    t = torso_path('krishna')
    o.append(f'<path d="{t}" fill="url(#skinG)"/>')
    cid = uid('torso')
    o.append(f'<clipPath id="{cid}"><path d="{t}"/></clipPath><g clip-path="url(#{cid})">')
    o.append(f'<path d="M{P(X(60), 760)} C{P(X(140), 840)} {P(X(170), 960)} {P(X(160), 1180)} L{P(X(400), 1180)} L{P(X(400), 740)} Z" fill="{c["shadow"]}" opacity="0.5" {blur(14)}/>')
    for s in (-1, 1):
        o.append(f'<path d="M{P(X(30, s), 772)} C{P(X(70, s), 766)} {P(X(120, s), 770)} {P(X(160, s), 784)}" stroke="{c["light"] if s < 0 else c["deep"]}" stroke-width="4" fill="none" opacity="0.32" {blur(2)}/>')
    o.append('</g>')
    o.append(rim(t, c, X(80), X(140), 8, 0.7))
    # vaijayanti garland
    g_pts = sample_cubic(((X(-112), 786), (X(-120), 960), (X(-40), 1060), (CX, 1062)), 18) + \
        sample_cubic(((CX, 1062), (X(40), 1060), (X(120), 960), (X(112), 786)), 18)[1:]
    cols = ['#E8384F', '#F8F3EA', '#F5B52E', '#E8384F', '#F8F3EA', '#B13BD0']
    for i, (x, y) in enumerate(g_pts):
        if i % 4 == 2:
            for s in (-1, 1):
                o.append(f'<path d="{ell(x + 11*s, y, 10, 4.5, 35*s)}" fill="#2E9A4E"/>')
    for i, (x, y) in enumerate(g_pts):
        o.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="11" fill="{cols[i % len(cols)]}" stroke="#00000030" stroke-width="1"/>')
        for a in range(5):
            ang = math.radians(a*72 + i*17)
            o.append(f'<circle cx="{f(x + 6*math.cos(ang))}" cy="{f(y + 6*math.sin(ang))}" r="4" fill="#ffffff" opacity="0.16"/>')
        o.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="3.3" fill="#F7C33C"/>')
    # pitambar shawl
    for s in (-1, 1):
        d = (f'M{P(X(98, s), 756)} C{P(X(166, s), 786)} {P(X(266, s), 796)} {P(X(316, s), 848)} C{P(X(352, s), 884)} {P(X(362, s), 960)} {P(X(366, s), 1180)} '
             f'L{P(X(190, s), 1180)} C{P(X(188, s), 1000)} {P(X(168, s), 900)} {P(X(128, s), 834)} C{P(X(112, s), 806)} {P(X(102, s), 782)} {P(X(98, s), 756)} Z')
        o.append(f'<path d="{d}" fill="url(#silk{"R" if s > 0 else "L"})"/>')
        sid = uid('shawl')
        o.append(f'<clipPath id="{sid}"><path d="{d}"/></clipPath><g clip-path="url(#{sid})">')
        for k in range(2):
            o.append(f'<path d="M{P(X(170 + k*70, s), 830 + k*14)} C{P(X(200 + k*70, s), 910)} {P(X(216 + k*64, s), 1000)} {P(X(222 + k*66, s), 1180)}" stroke="#A35E0A" stroke-width="12" fill="none" opacity="0.22" {blur(6)}/>')
            o.append(f'<path d="M{P(X(190 + k*70, s), 836 + k*14)} C{P(X(220 + k*70, s), 916)} {P(X(234 + k*64, s), 1000)} {P(X(240 + k*66, s), 1180)}" stroke="#FFE694" stroke-width="5" fill="none" opacity="0.3" {blur(3)}/>')
        if s > 0:
            o.append(f'<path d="M{P(X(200), 800)} C{P(X(300), 820)} {P(X(360), 900)} {P(X(370), 1180)} L{P(X(420), 1180)} L{P(X(420), 780)} Z" fill="#7A3E06" opacity="0.35" {blur(14)}/>')
        o.append('</g>')
        edge = f'M{P(X(98, s), 756)} C{P(X(102, s), 782)} {P(X(112, s), 806)} {P(X(128, s), 834)} C{P(X(168, s), 900)} {P(X(188, s), 1000)} {P(X(190, s), 1180)}'
        o.append(f'<path d="{edge}" stroke="#7A3A06" stroke-width="16" fill="none"/>')
        o.append(f'<path d="{edge}" stroke="#D8304E" stroke-width="10" fill="none"/>')
        o.append(f'<path d="{edge}" stroke="#FFE7A0" stroke-width="2.5" fill="none" stroke-dasharray="3 7"/>')
    o.append(rim(t, c, X(250), X(330), 8, 0.6))
    # choker + necklace
    o.append(f'<path d="M{P(X(-62), 738)} Q{P(CX, 794)} {P(X(62), 738)}" stroke="{GOLD["dd"]}" stroke-width="16" fill="none" stroke-linecap="round"/>')
    o.append(f'<path d="M{P(X(-62), 738)} Q{P(CX, 794)} {P(X(62), 738)}" stroke="url(#goldv)" stroke-width="11" fill="none" stroke-linecap="round"/>')
    for (x, y) in sample_cubic(((X(-62), 738), (X(-31), 766), (X(31), 766), (X(62), 738)), 10)[1:-1]:
        o.append(f'<path d="M{P(x - 3, y + 4)} L{P(x, y + 13)} L{P(x + 3, y + 4)} Z" fill="url(#goldv)"/><circle cx="{f(x)}" cy="{f(y + 14)}" r="2.6" fill="#E0213F"/>')
    neck_l = f'M{P(X(-86), 756)} C{P(X(-82), 856)} {P(X(82), 856)} {P(X(86), 756)}'
    o.append(f'<path d="{neck_l}" stroke="{GOLD["dd"]}" stroke-width="7" fill="none"/>')
    o.append(f'<path d="{neck_l}" stroke="url(#goldv)" stroke-width="4.5" fill="none"/>')
    o.append(f'<path d="M{P(CX - 16, 830)} L{P(CX, 824)} L{P(CX + 16, 830)} L{P(CX, 868)} Z" fill="url(#goldv)" stroke="{GOLD["dd"]}" stroke-width="2"/>')
    o.append(gem(CX, 842, 9, 'b', setting=False))
    return ''.join(o)


def body_arjun(c):
    o = []
    # Gandiva slung behind the viewer-left shoulder
    bow = f'M{P(X(-236), 268)} C{P(X(-330), 420)} {P(X(-360), 640)} {P(X(-320), 900)}'
    o.append(f'<path d="M{P(X(-236), 268)} L{P(X(-320), 900)}" stroke="#EDE4CC" stroke-width="2" opacity="0.7"/>')
    o.append(f'<path d="{bow}" stroke="#40220E" stroke-width="17" fill="none" stroke-linecap="round"/>')
    o.append(f'<path d="{bow}" stroke="#94592C" stroke-width="11" fill="none" stroke-linecap="round"/>')
    o.append(f'<path d="{bow}" stroke="#D69E60" stroke-width="3" fill="none" opacity="0.7" transform="translate(-3 0)"/>')
    o.append(f'<path d="M{P(X(-240), 262)} Q{P(X(-234), 244)} {P(X(-218), 238)}" stroke="url(#goldv)" stroke-width="10" fill="none" stroke-linecap="round"/>')
    for (x, y) in (cubic((X(-236), 268), (X(-330), 420), (X(-360), 640), (X(-320), 900), t) for t in (0.3, 0.55)):
        o.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="10" fill="url(#goldv)" stroke="{GOLD["dd"]}" stroke-width="2"/>')
    t = torso_path('arjun')
    o.append(f'<path d="{t}" fill="#6A1C28"/>')
    cid = uid('torso')
    o.append(f'<clipPath id="{cid}"><path d="{t}"/></clipPath><g clip-path="url(#{cid})">')
    plate = (f'M{P(X(-150), 808)} C{P(X(-90), 786)} {P(X(90), 786)} {P(X(150), 808)} C{P(X(170), 900)} {P(X(176), 1000)} {P(X(170), 1180)} '
             f'L{P(X(-170), 1180)} C{P(X(-176), 1000)} {P(X(-170), 900)} {P(X(-150), 808)} Z')
    o.append(f'<path d="{plate}" fill="url(#armor)" stroke="#5A3410" stroke-width="3"/>')
    for k in range(3):
        y = 900 + k*60
        o.append(f'<path d="M{P(X(-160), y)} Q{P(CX, y + 22)} {P(X(160), y)}" stroke="#7A4A16" stroke-width="3" fill="none" opacity="0.7"/>')
        o.append(f'<path d="M{P(X(-160), y + 4)} Q{P(CX, y + 26)} {P(X(160), y + 4)}" stroke="{GOLD["l"]}" stroke-width="1.6" fill="none" opacity="0.6"/>')
    o.append(f'<g transform="translate({CX} 904)">')
    for a in range(16):
        o.append(f'<path d="M-6 -38 L0 -58 L6 -38 Z" fill="url(#goldv)" transform="rotate({a*22.5})"/>')
    o.append(f'<circle r="38" fill="url(#gold)" stroke="#5A3410" stroke-width="3"/><circle r="27" fill="none" stroke="{GOLD["l"]}" stroke-width="2" opacity="0.8"/>')
    o.append('</g>')
    o.append(gem(CX, 904, 14, 'b', setting=False))
    o.append(f'<path d="M{P(X(-190), 800)} C{P(X(-120), 820)} {P(X(120), 1000)} {P(X(220), 1180)} L{P(X(120), 1180)} C{P(X(40), 1020)} {P(X(-120), 880)} {P(X(-220), 850)} Z" fill="#8A2232"/>')
    o.append(f'<path d="M{P(X(-190), 800)} C{P(X(-120), 820)} {P(X(120), 1000)} {P(X(220), 1180)}" stroke="{GOLD["m"]}" stroke-width="4" fill="none"/>')
    o.append(f'<path d="M{P(X(-220), 850)} C{P(X(-120), 880)} {P(X(40), 1020)} {P(X(120), 1180)}" stroke="{GOLD["m"]}" stroke-width="4" fill="none"/>')
    o.append(f'<path d="M{P(X(80), 800)} C{P(X(150), 880)} {P(X(180), 980)} {P(X(170), 1180)} L{P(X(420), 1180)} L{P(X(420), 760)} Z" fill="#1A0A10" opacity="0.4" {blur(14)}/>')
    o.append('</g>')
    for s in (-1, 1):
        d = (f'M{P(X(124, s), 796)} C{P(X(194, s), 766)} {P(X(304, s), 786)} {P(X(346, s), 856)} C{P(X(364, s), 896)} {P(X(356, s), 936)} {P(X(334, s), 956)} '
             f'C{P(X(284, s), 926)} {P(X(204, s), 896)} {P(X(144, s), 896)} C{P(X(130, s), 866)} {P(X(122, s), 826)} {P(X(124, s), 796)} Z')
        o.append(f'<path d="{d}" fill="url(#armor)" stroke="#5A3410" stroke-width="3"/>')
        for k in range(1, 3):
            o.append(f'<path d="M{P(X(134 + k*8, s), 826 + k*24)} C{P(X(204, s), 816 + k*26)} {P(X(294, s), 836 + k*26)} {P(X(342 - k*4, s), 876 + k*22)}" stroke="#7A4A16" stroke-width="3" fill="none" opacity="0.8"/>')
        for k in range(5):
            o.append(f'<circle cx="{f(X(164 + k*38, s))}" cy="{f(814 + k*k*3.2)}" r="4" fill="{GOLD["l"]}" stroke="#7A4A16" stroke-width="1"/>')
        if s > 0:
            o.append(rim(d, c, X(260), X(350), 8, 0.6))
    o.append(rim(t, c, X(300), X(380), 8, 0.5))
    o.append(f'<path d="M{P(X(-88), 752)} Q{P(CX, 826)} {P(X(88), 752)}" stroke="#5A3410" stroke-width="30" fill="none" stroke-linecap="round"/>')
    o.append(f'<path d="M{P(X(-88), 752)} Q{P(CX, 826)} {P(X(88), 752)}" stroke="url(#goldv)" stroke-width="24" fill="none" stroke-linecap="round"/>')
    pts = sample_cubic(((X(-82), 756), (X(-41), 790), (X(41), 790), (X(82), 756)), 12)
    o.append(pearls_along(pts[1:-1], 3))
    o.append(gem(CX, 788, 9, 'b'))
    return ''.join(o)


def body_defs(who):
    if who == 'krishna':
        return [f'<linearGradient id="silk{k}" x1="{a}" y1="0" x2="{b}" y2="1"><stop offset="0" stop-color="#FFDA6A"/>'
                f'<stop offset="0.5" stop-color="#F2AE2A"/><stop offset="1" stop-color="#C97A10"/></linearGradient>'
                for k, a, b in (('L', 0, 1), ('R', 1, 0))]
    return ['''<linearGradient id="armor" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F6CF78"/>
      <stop offset="0.45" stop-color="#C8913A"/><stop offset="1" stop-color="#7A4A16"/></linearGradient>''']


# ---------------------------------------------------------------- expression presets
EXPR = {
    'krishna': {
        'serene': {},
        'talk': dict(mouth='talk2'),
        'smile': dict(mouth='smile', serene=0.32, cheek=0.35, eye=0.95),
        'knowing': dict(mouth='smile_talk', brow='raise', serene=0.12, cheek=0.2, gaze=(5, 0)),
        'blink': dict(blink=True),
    },
    'arjun': {
        'neutral': {},
        'panic': dict(eye=1.32, brow='panic', mouth='panic', serene=0.0, gaze=(0, -1), iris=0.82),
        'worried': dict(eye=1.06, brow='worry', mouth='worry_talk', serene=0.0),
        'curious': dict(eye=1.1, brow='raise', mouth='oh', serene=0.0, gaze=(-5, -2)),
        'relief': dict(mouth='smile', brow='relief', serene=0.22, cheek=0.38, eye=0.95),
        'frustrated': dict(eye=1.04, brow='angry', mouth='worry_talk', serene=0.1, gaze=(-4, 0)),
        'sheepish': dict(eye=0.9, brow='worry', mouth='worry', serene=0.3, gaze=(-7, 4), cheek=0.15),
        'determined': dict(eye=1.12, brow='angry', mouth='talk1', serene=0.0, gaze=(4, -1)),
        'blink': dict(blink=True),
    },
}


# ---------------------------------------------------------------- assemble
DEFAULTS = {
    'krishna': dict(eye=1.0, brow='calm', mouth='rest', gaze=(0, 0), blink=False, serene=0.2, smile=4, tilt=-2.5, cheek=0.0),
    'arjun': dict(eye=1.0, brow='neutral', mouth='rest', gaze=(0, 0), blink=False, serene=0.08, smile=0, tilt=0, cheek=0.0),
}


def build(who, **expr):
    _uid[0] = 0
    e = dict(DEFAULTS[who]); e.update(expr)
    c = PAL[who]
    defs = defs_common(c) + body_defs(who)
    face_d = mirror_path(FACE[who])
    b = []
    b.append(f'<g transform="rotate({f(e["tilt"]*0.5)} {CX} 760)">' + hair_back(c, who) + '</g>')
    b.append(neck(c, who))
    b.append(f'<g transform="translate(0 {-BODY_UP})">')
    b.append(body_krishna(c) if who == 'krishna' else body_arjun(c))
    b.append('</g>')
    b.append(f'<g transform="rotate({f(e["tilt"])} {CX} 700)">')
    for s in (-1, 1):
        b.append(ear(s, c))
    b.append(f'<path d="{face_d}" fill="url(#skinG)"/>')
    b.append(f'<clipPath id="faceC"><path d="{face_d}"/></clipPath><g clip-path="url(#faceC)">')
    b.append(face_shading(c, who))
    b.append(nose(c, who))
    b.append('</g>')
    b.append(rim(face_d, c, X(90), X(142), 8, 0.9))
    if who == 'krishna':
        b.append(f'<path d="M{P(X(-12), 452)} C{P(X(-14), 420)} {P(X(-17), 390)} {P(X(-19), 360)} M{P(X(12), 452)} C{P(X(14), 420)} {P(X(17), 390)} {P(X(19), 360)} '
                 f'M{P(X(-12), 452)} Q{P(CX, 466)} {P(X(12), 452)}" stroke="#F6F2E8" stroke-width="5.5" fill="none" stroke-linecap="round"/>')
        b.append(f'<path d="M{P(CX, 370)} L{P(CX, 444)}" stroke="#E2283C" stroke-width="5" stroke-linecap="round"/>')
    else:
        b.append(f'<path d="M{P(CX, 394)} L{P(CX, 428)}" stroke="#D2263A" stroke-width="5.5" stroke-linecap="round"/>')
    for s in (-1, 1):
        b.append(eye(s, c, who, o=e['eye'], gaze=e['gaze'], blink=e['blink'], serene=e['serene'], cheek=e['cheek'], iris=e.get('iris', 1.0)))
        b.append(brow(s, c, who, e['brow']))
    b.append(mouth(c, who, e['mouth'], base_smile=e['smile']))
    if who == 'arjun':
        b.append(mustache(c, who, lift=MOUTHS[e['mouth']][1]))
    b.append(hair_side(c, who))
    b.append(hair_locks(c, who))
    for s in (-1, 1):
        if who == 'krishna':
            b.append(f'<path d="M{P(X(150, s), 528)} L{P(X(150, s), 538)}" stroke="{GOLD["m"]}" stroke-width="3"/>')
            b.append(f'<path d="M{P(X(150, s), 536)} C{P(X(170, s), 540)} {P(X(172, s), 566)} {P(X(150, s), 578)} C{P(X(128, s), 566)} {P(X(130, s), 540)} {P(X(150, s), 536)} Z" fill="url(#goldv)" stroke="{GOLD["dd"]}" stroke-width="2"/>')
            b.append(gem(X(150, s), 556, 7, 't', setting=False))
            b.append(f'<circle cx="{X(150, s)}" cy="588" r="5.5" fill="url(#pearl)"/>')
        else:
            b.append(f'<circle cx="{X(152, s)}" cy="548" r="13" fill="none" stroke="{GOLD["dd"]}" stroke-width="6"/>')
            b.append(f'<circle cx="{X(152, s)}" cy="548" r="13" fill="none" stroke="url(#goldv)" stroke-width="3.5"/>')
    b.append('<g transform="translate(0 -18)">' + (crown_krishna() if who == 'krishna' else crown_arjun()) + '</g>')
    b.append('</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs>{"".join(defs)}</defs>{"".join(b)}</svg>')


def render(svg, scale=1.0):
    import skia
    data = svg.encode()
    d = None
    for _ in range(4):   # MakeFromStream can return None transiently under worker load; retry
        stream = skia.MemoryStream(data)
        d = skia.SVGDOM.MakeFromStream(stream)
        if d is not None:
            break
    if d is None:
        raise RuntimeError('SVG parse failed')
    w, h = int(W*scale), int(H*scale)
    surf = skia.Surface(w, h)
    cv = surf.getCanvas()
    cv.clear(skia.ColorTRANSPARENT)
    cv.scale(scale, scale)
    d.setContainerSize(skia.Size(W, H))
    d.render(cv)
    return surf.makeImageSnapshot()


if __name__ == '__main__':
    for who in ('krishna', 'arjun'):
        render(build(who), 1.0).save(f'{who}_test.png')
    print('ok')
