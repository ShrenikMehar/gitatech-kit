"""Fix one part of a finished episode without re-rendering the whole video.

  python3 splice.py <episode_dir> A B --name GitaTech_Topic [--driver ep.py]

Re-renders only frames in [A, B) seconds with the (edited) driver, splices them into <episode>/silent.mp4,
then re-muxes the existing data/mix.wav into <name>.mp4. If the dialogue/voices changed, run finish.py instead
(the audio would no longer match). Pick A and B at shot cuts when possible so the seam is invisible.
"""
import argparse
import glob
import os
import subprocess
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent


def run(cmd, **kw):
    print('$', ' '.join(map(str, cmd)), flush=True)
    subprocess.run(list(map(str, cmd)), check=True, **kw)


ap = argparse.ArgumentParser()
ap.add_argument('episode')
ap.add_argument('a', type=float)
ap.add_argument('b', type=float)
ap.add_argument('--name', required=True)
ap.add_argument('--driver')
ap.add_argument('--fps', type=int, default=30)
x = ap.parse_args()
E = Path(x.episode).resolve()
drv = Path(x.driver) if x.driver else Path(sorted(glob.glob(str(E / 'ep*.py')))[0])
env = dict(os.environ, GT_EP=str(E), GT=str(LIB.parent))
fa, fb = int(round(x.a*x.fps)), int(round(x.b*x.fps))
seg, src, tmp = E / 'seg.mp4', E / 'silent.mp4', E / 'silent_spliced.mp4'
run([sys.executable, drv, '--range', x.a, x.b, '--out', seg], env=env)
fc = (f'[0:v]trim=end_frame={fa},setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];'
      f'[0:v]trim=start_frame={fb},setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[v]')
run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-i', seg, '-filter_complex', fc, '-map', '[v]', '-c:v', 'libx264',
     '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', tmp])
os.replace(tmp, src)
out = E / f'{x.name}.mp4'
run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-i', E / 'data/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
     '-c:a', 'aac', '-b:a', '192k', '-shortest', out])
print('done', out)
