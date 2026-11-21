"""Starter world: a deliberately plain flat 2D stage, here only to show the mechanics.
Replace all of it with whatever world the scenario needs (flat 2D, isometric via iso.Cam, full-screen diagram, ...).

scene(c, t, st) draws everything from a state dict built by the driver and returns screen anchors for labels.
Keep it a pure function of (t, st): no globals that change between frames.
"""
import skia

import world as Wd
from iso import P, SP, glow, hexc, mixc

W, H = 1080, 1920
FLOOR_Y = 1180
HERO = (540, 1000, 260, 300)        # x, y (centre), w, h of the one hero object, in world coords
ARJ = (250, FLOOR_Y + 40, 0.42)     # standing bust: x, bottom y, scale
KRI = (830, FLOOR_Y + 40, 0.42)


def to_screen(cam, x, y):
    s, fx, fy, cy = cam
    return 540 + (x - fx)*s, cy + (y - fy)*s


def backdrop(c):
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, FLOOR_Y)], [hexc('#141a33').toColor(), hexc('#2a2f4f').toColor()])
    c.drawRect(skia.Rect(-600, -600, W + 600, FLOOR_Y), skia.Paint(Shader=sh))
    c.drawRect(skia.Rect(-600, FLOOR_Y, W + 600, H + 600), P(hexc('#1b1c2c')))
    c.drawLine(-600, FLOOR_Y, W + 600, FLOOR_Y, SP(hexc('#4a4f72'), 3))


def hero(c, k_fixed, pulse):
    x, y, w, h = HERO
    col = mixc(Wd.DEAD_C, Wd.RUN_C, k_fixed)
    glow(c, x, y, w, col, 0.18 + 0.25*pulse)
    rr = skia.RRect.MakeRectXY(skia.Rect(x - w/2, y - h/2, x + w/2, y + h/2), 24, 24)
    c.drawRRect(rr, P(hexc('#22253d')))
    c.drawRRect(rr, SP(col, 4))


def scene(c, t, st):
    """st: cam (s, fx, fy, cy), fixed 0..1, pulse 0..1, chars [callable(c)], overlay callable(c) | None."""
    cam = st['cam']
    s, fx, fy, cy = cam
    c.save()
    c.translate(540, cy)
    c.scale(s, s)
    c.translate(-fx, -fy)
    backdrop(c)
    hero(c, st.get('fixed', 0.0), st.get('pulse', 0.0))
    for draw in st.get('chars', []):
        draw(c)
    if st.get('overlay'):
        st['overlay'](c)
    c.restore()
    return {'hero': to_screen(cam, HERO[0], HERO[1] - HERO[3]/2)}
