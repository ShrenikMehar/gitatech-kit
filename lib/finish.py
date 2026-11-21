"""Finish an episode: cues -> audio mix -> full render -> mux -> QA contact sheet.

  python3 finish.py <episode_dir> [--driver epN.py] [--workers N (default: all cores)] [--name GitaTech_EpN_Topic]

Writes <episode>/data/cues.json, <episode>/data/mix.wav, <episode>/silent.mp4, <episode>/<name>.mp4, <episode>/qa.png.
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('episode')
    ap.add_argument('--driver')
    ap.add_argument('--workers', type=int, default=os.cpu_count() or 2)
    ap.add_argument('--name', default='final')
    ap.add_argument('--skip-render', action='store_true')
    a = ap.parse_args()
    E = Path(a.episode).resolve()
    drv = Path(a.driver) if a.driver else Path(sorted(glob.glob(str(E / 'ep*.py')))[0])
    env = dict(os.environ, GT_EP=str(E), GT=str(LIB.parent))
    run([sys.executable, drv, '--cues'], env=env)
    run([sys.executable, LIB / 'mix.py', E])   # no -I: on a Mac numpy may live in user site-packages
    if not a.skip_render:
        run([sys.executable, drv, '--workers', a.workers, '--out', E / 'silent.mp4'], env=env)
    out = E / f'{a.name}.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-i', E / 'silent.mp4', '-i', E / 'data/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
         '-c:a', 'aac', '-b:a', '192k', '-shortest', out])
    run(['ffmpeg', '-v', 'error', '-y', '-i', out, '-vf', 'fps=1/2,scale=216:384,tile=8x3', '-frames:v', '1', E / 'qa.png'])
    print('done', out)


if __name__ == '__main__':
    main()
