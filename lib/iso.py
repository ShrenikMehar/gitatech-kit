"""Isometric 3D drawing toolkit (skia). World: x, y on the ground, z up. 1 unit = U px at zoom 1."""
import math

import skia

U = 100.0
C30, S30 = math.cos(math.radians(30)), 0.5
W, H = 1080, 1920


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, k):
    return a + (b - a) * k


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return skia.Color4f(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def ca(c, a):
    return skia.Color4f(c.fR, c.fG, c.fB, clamp(c.fA * a))


def mixc(a, b, k):
    return skia.Color4f(lerp(a.fR, b.fR, k), lerp(a.fG, b.fG, k), lerp(a.fB, b.fB, k), lerp(a.fA, b.fA, k))


def rd(r, d):
    """Screen-axis coords (r = right, d = down, in iso units) -> ground x, y."""
    return (d + r) / 2.0, (d - r) / 2.0


class Cam:
    """Camera looks at ground point (x, y) at height z, placed at screen (sx0, sy0)."""

    def __init__(self, x, y, zoom, sx0=W / 2, sy0=860, z=0.0):
        self.x, self.y, self.z, self.zoom, self.sx0, self.sy0 = x, y, z, zoom, sx0, sy0

    def p(self, x, y, z=0.0):
        k = U * self.zoom
        dx, dy, dz = x - self.x, y - self.y, z - self.z
        return (self.sx0 + (dx - dy) * C30 * k, self.sy0 + (dx + dy) * S30 * k - dz * k)

    def pts(self, ps):
        return [skia.Point(*self.p(*q)) for q in ps]

    def face_matrix(self, origin, u, v):
        """Affine matrix mapping local 2D (a, b) -> screen, where a runs along world vector u, b along v (unit = 1 world unit)."""
        o = self.p(*origin)
        pu = self.p(origin[0] + u[0], origin[1] + u[1], origin[2] + u[2])
        pv = self.p(origin[0] + v[0], origin[1] + v[1], origin[2] + v[2])
        m = skia.Matrix()
        m.setAll(pu[0] - o[0], pv[0] - o[0], o[0], pu[1] - o[1], pv[1] - o[1], o[1], 0, 0, 1)
        return m


def P(c, a=1.0, blend=None):
    p = skia.Paint(AntiAlias=True, Color4f=ca(c, a))
    if blend is not None:
        p.setBlendMode(blend)
    return p


def SP(c, w, a=1.0, dash=None, phase=0.0, blend=None):
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w, Color4f=ca(c, a),
                   StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make(dash, phase))
    if blend is not None:
        p.setBlendMode(blend)
    return p


def poly(pts):
    return skia.Path.Polygon(pts, True)


def glow(c, x, y, r, col, a):
    if a <= 0.003 or r <= 0.5:
        return
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [ca(col, a).toColor(), ca(col, 0).toColor()])
    c.drawCircle(x, y, r, skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kPlus))


def blurred(c, path, col, a, sigma, blend=None):
    p = skia.Paint(AntiAlias=True, Color4f=ca(col, a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(0.1, sigma)))
    if blend is not None:
        p.setBlendMode(blend)
    c.drawPath(path, p)


# ----------------------------------------------------------------------------- materials
BODY_TOP = hexc("#2a3566")
BODY_L = hexc("#1b2348")
BODY_R = hexc("#121834")
EDGE = hexc("#3a4a8a")


def shade(col, k):
    return mixc(col, hexc("#000000"), k)


def tint(col, k):
    return mixc(col, hexc("#ffffff"), k)


# ----------------------------------------------------------------------------- primitives
def shadow(c, cam, x, y, w, d, a=0.55, spread=0.25, z=0.0):
    pts = cam.pts([(x - spread, y - spread, z), (x + w + spread, y - spread, z), (x + w + spread, y + d + spread, z), (x - spread, y + d + spread, z)])
    blurred(c, poly(pts), hexc("#000000"), a, 18 * cam.zoom)


def box(c, cam, x, y, z, w, d, h, accent, a=1.0, glow_a=0.0, top=None, left=None, right=None, edge_w=2.2, solid=False):
    """Iso box: visible faces are top (z+h), front-left (y+d) and front-right (x+w)."""
    if a <= 0.003:
        return
    if solid:
        top = top or tint(accent, 0.18)
        left = left or shade(accent, 0.25)
        right = right or shade(accent, 0.5)
    else:
        top = top or BODY_TOP
        left = left or BODY_L
        right = right or BODY_R
    T = cam.pts([(x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)])
    L = cam.pts([(x, y + d, z + h), (x + w, y + d, z + h), (x + w, y + d, z), (x, y + d, z)])
    R = cam.pts([(x + w, y, z + h), (x + w, y + d, z + h), (x + w, y + d, z), (x + w, y, z)])
    if glow_a > 0.003:
        sil = cam.pts([(x, y, z + h), (x + w, y, z + h), (x + w, y, z), (x + w, y + d, z), (x, y + d, z), (x, y + d, z + h)])
        blurred(c, poly(sil), accent, 0.55 * glow_a * a, 22 * cam.zoom, skia.BlendMode.kPlus)
    c.drawPath(poly(L), P(left, a))
    c.drawPath(poly(R), P(right, a))
    c.drawPath(poly(T), P(top, a))
    # accent rim along the top edges + vertical front edge
    ew = edge_w * cam.zoom
    rim = skia.Path()
    rim.moveTo(*cam.p(x, y + d, z + h))
    rim.lineTo(*cam.p(x + w, y + d, z + h))
    rim.lineTo(*cam.p(x + w, y, z + h))
    c.drawPath(rim, SP(accent, ew * 1.2, a))
    back = skia.Path()
    back.moveTo(*cam.p(x + w, y, z + h))
    back.lineTo(*cam.p(x, y, z + h))
    back.lineTo(*cam.p(x, y + d, z + h))
    c.drawPath(back, SP(tint(accent, 0.3), ew * 0.8, a * 0.55))
    c.drawLine(*cam.p(x + w, y + d, z + h), *cam.p(x + w, y + d, z), SP(accent, ew * 0.8, a * 0.65))
    if glow_a > 0.003:
        c.drawPath(rim, SP(accent, ew * 4, 0.35 * glow_a * a, blend=skia.BlendMode.kPlus))


def wire_box(c, cam, x, y, z, w, d, h, col, a=1.0, phase=0.0):
    """Dashed wireframe cube (a Pod that doesn't exist yet)."""
    if a <= 0.003:
        return
    corners = {}
    for i, (dx, dy, dz) in enumerate([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]):
        corners[i] = cam.p(x + dx * w, y + dy * d, z + dz * h)
    T = poly([skia.Point(*corners[i]) for i in (4, 5, 6, 7)])
    c.drawPath(T, P(col, 0.10 * a))
    edges = [(4, 5), (5, 6), (6, 7), (7, 4), (6, 2), (5, 1), (7, 3), (2, 1), (2, 3)]
    for i, j in edges:
        c.drawLine(*corners[i], *corners[j], SP(col, 2.4 * cam.zoom, a, dash=[8 * cam.zoom, 6 * cam.zoom], phase=phase))


def cylinder(c, cam, x, y, z, r, h, accent, a=1.0, glow_a=0.0, bands=3, fill_k=1.0):
    """Upright cylinder centred at ground (x, y)."""
    if a <= 0.003:
        return
    k = U * cam.zoom
    rx, ry = r * math.sqrt(2) * C30 * k, r * math.sqrt(2) * S30 * k
    bx, by = cam.p(x, y, z)
    tx, ty = cam.p(x, y, z + h)
    if glow_a > 0.003:
        sil = skia.Path()
        sil.addRect(skia.Rect(tx - rx, ty, tx + rx, by))
        sil.addOval(skia.Rect(tx - rx, ty - ry, tx + rx, ty + ry))
        sil.addOval(skia.Rect(bx - rx, by - ry, bx + rx, by + ry))
        blurred(c, sil, accent, 0.5 * glow_a * a, 22 * cam.zoom, skia.BlendMode.kPlus)
    body = skia.Path()
    body.moveTo(tx - rx, ty)
    body.lineTo(bx - rx, by)
    body.arcTo(skia.Rect(bx - rx, by - ry, bx + rx, by + ry), 180, -180, False)
    body.lineTo(tx + rx, ty)
    body.close()
    sh = skia.GradientShader.MakeLinear([skia.Point(tx - rx, 0), skia.Point(tx + rx, 0)],
                                        [ca(BODY_L, a).toColor(), ca(tint(BODY_L, 0.12), a).toColor(), ca(BODY_R, a).toColor()], [0.0, 0.35, 1.0])
    c.drawPaint if False else None
    c.drawPath(body, skia.Paint(AntiAlias=True, Shader=sh))
    # bands (disk seams), lit in accent as the store fills
    for i in range(1, bands):
        yy = lerp(by, ty, i / bands)
        p = skia.Path()
        p.addArc(skia.Rect(tx - rx, yy - ry, tx + rx, yy + ry), 0, 180)
        c.drawPath(p, SP(accent, 2.0 * cam.zoom, a * 0.55))
    p = skia.Path()
    p.addArc(skia.Rect(bx - rx, by - ry, bx + rx, by + ry), 0, 180)
    c.drawPath(p, SP(accent, 2.2 * cam.zoom, a * 0.7))
    top = skia.Rect(tx - rx, ty - ry, tx + rx, ty + ry)
    c.drawOval(top, P(BODY_TOP, a))
    c.drawOval(top, SP(accent, 2.6 * cam.zoom, a))
    if glow_a > 0.003:
        c.drawOval(top, SP(accent, 9 * cam.zoom, 0.3 * glow_a * a, blend=skia.BlendMode.kPlus))
    return (tx, ty, rx, ry)


def top_matrix(cam, x, y, z):
    """Matrix for drawing on the top plane (z) with local a along +x and b along +y, unit = 1 world unit."""
    return cam.face_matrix((x, y, z), (1, 0, 0), (0, 1, 0))


def front_left_matrix(cam, x, y, z):
    """Plane y = const facing lower-left: a along +x, b along -z (down)."""
    return cam.face_matrix((x, y, z), (1, 0, 0), (0, 0, -1))


def front_right_matrix(cam, x, y, z):
    """Plane x = const facing lower-right: a along -y, b along -z."""
    return cam.face_matrix((x, y, z), (0, -1, 0), (0, 0, -1))


def arc_path(cam, a3, b3, lift, n=40):
    pts = []
    for i in range(n + 1):
        k = i / n
        x = lerp(a3[0], b3[0], k)
        y = lerp(a3[1], b3[1], k)
        z = lerp(a3[2], b3[2], k) + lift * 4 * k * (1 - k)
        pts.append(cam.p(x, y, z))
    return pts


def point_on(pts, k):
    if k <= 0:
        return pts[0]
    if k >= 1:
        return pts[-1]
    L = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    d = k * sum(L)
    for (a, b), l in zip(zip(pts, pts[1:]), L):
        if d <= l:
            f = d / l if l else 0
            return (lerp(a[0], b[0], f), lerp(a[1], b[1], f))
        d -= l
    return pts[-1]


def polyline(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    return p
