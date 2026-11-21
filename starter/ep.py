"""Starter driver: the mechanics of an episode, with no story worth keeping. Copy starter/ to ~/reels/<name>/, then
replace the beats, shots, world state and cues with the new episode's. Plumbing lives in lib/episode.py.

  python3 ep.py --still 1 4 8 12      # stills + stills/sheet.png
  python3 $GT/lib/finish.py <dir> --name <Name>    # cues, mix, full render, mux, qa.png

Rules that keep it working: frame(t) is a pure function of t (parallel workers render frames out of order);
all beat times come from word times (E.w), never hard-coded seconds, so they survive re-voicing.
"""
import os
import sys

GT = os.environ.get('GT', os.path.expanduser('~/gitatech-kit'))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, f'{GT}/lib']
import skia

import episode as E
import scene as S                      # this episode's world (scene.py next to this file)
import world as Wd
from gt import clamp, concept_tag, ease, ramp

W, H = 1080, 1920
# Word indices come from what voices.py prints (index:word@time). Audio words can differ from caption tokens.
E.setup(page_at={'L2': 8, 'L3': 5, 'L4': 5}, emph={'L1': [2], 'L2': [4], 'L3': [11], 'L4': [2, 10]})

# ----------------------------------------------------------------------------- beats (all from word times)
T_CU1 = E.cut('L1', 'L2')             # close-up on Krishna as he answers
T_TAG = E.w('L2', 4)                  # 'single point of failure' -> concept tag
T_CARD = E.w('L3', 0) + 0.15          # verse card
T_FIX = E.cut('L3', 'L4')
T_OK = E.w('L4', 10)                  # 'app chalegi': the fix lands

SHOTS = [(0.0, 'world', None), (T_CU1, 'cu', 'krishna'), (T_FIX, 'world', None)]
CAM_WIDE = (1.0, 540, 1000, 980)      # s, focus x, focus y, screen y of focus
CAM_PUSH = (1.25, 540, 1000, 900)


def cam_at(t):
    if t < T_CU1:
        k = ease(clamp(t/max(0.1, T_CU1)))
        return tuple(a + (b - a)*k for a, b in zip(CAM_WIDE, CAM_PUSH))
    return CAM_WIDE


def world_state(t, with_chars=True):
    chars = []
    if with_chars:
        ax, ay, asc = S.ARJ
        kx, ky, ksc = S.KRI
        akey = 'arjun_frustrated' if t < T_FIX else 'arjun_relief'
        chars = [lambda c: E.standing_bust(c, akey, t, 0.0 if t < T_FIX else T_FIX, ax, ay, asc),
                 lambda c: E.standing_bust(c, 'krishna_smile', t, 0.0, kx, ky, ksc, flip=True)]
    return dict(cam=cam_at(t), fixed=ramp(t, T_OK, 0.4), pulse=E.plate(t, 0.0, T_CU1, 0.3), chars=chars)


def draw_scene(c, t):
    """Background for close-ups: the same world without the characters."""
    S.scene(c, t, world_state(t, with_chars=False))


# ----------------------------------------------------------------------------- shots
def world_shot(c, t):
    anchors = S.scene(c, t, world_state(t))
    if t >= T_FIX:
        hx, hy = anchors['hero']
        E.pill(c, hx, hy - 60, 'replicas: 3', Wd.RUN_C, ramp(t, T_OK, 0.2), size=26, k=clamp((t - T_OK)/0.35))


def closeup(c, t, key, t0, t1):
    E.closeup(c, key, t, t0, t1, backdrop=lambda cc, tt: E.blur_backdrop(cc, draw_scene, tt))
    concept_tag(c, 540, 380, 'single point of failure', 'ek dhaaga', E.plate(t, T_TAG, T_CARD - 0.2, 0.2), clamp((t - T_TAG)/0.35))
    E.verse_card(c, t, T_CARD, ['मयि सर्वमिदं प्रोतं', 'सूत्रे मणिगणा इव'], 'GITA 7.7', a_out=1 - ramp(t, T_FIX - 0.3, 0.25))


def frame(t):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    (t0, kind, key), t1 = E.shot_at(t, SHOTS)
    if kind == 'cu':
        closeup(c, t, key, t0, t1)
    else:
        world_shot(c, t)
    up = t >= T_OK
    E.hud(c, t, 'APP STATUS', '200' if up else '503', Wd.RUN_C if up else Wd.DEAD_C, T_OK if up else 0.0, a=ramp(t, 0.3, 0.3))
    E.finish_frame(c, t, SHOTS)
    return surf.makeImageSnapshot()


def cues():
    out = [(s_[0] - 0.1, 'whoosh', -20) for s_ in SHOTS[1:]]
    out += [(0.4, 'glitch', -18), (T_TAG, 'pop', -17), (T_CARD, 'bowl', -14), (T_OK, 'pop', -14), (T_OK + 0.05, 'swell', -20)]
    return out


if __name__ == '__main__':
    E.run(frame, cues)
