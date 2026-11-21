"""Check generated voices before building: cut-off lines and total length.

  python3 check.py <episode_dir> [--target 50]

A line is flagged when the voice returned clearly fewer words than `say` has, or its audio ends well before the
next line starts being expected. A truncated Krishna line once broke the voice ~15 s into a delivered reel; this
catches that. Regenerate only the flagged line (edit nothing, re-run voices.py; edge-tts cut-offs are transient).
Exit code 1 if anything is flagged.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import norm, tokens

args = sys.argv[1:]
E = Path(args[0])
target = float(args[args.index('--target') + 1]) if '--target' in args else None
S = json.loads((E / 'script.json').read_text())
T = json.loads((E / 'timeline.json').read_text())
say = {l['id']: l['say'] for l in S['lines']}
bad = 0
print(f"{'line':5} {'who':8} {'words':>9} {'start':>7} {'end':>7}  last word")
for l in T['lines']:
    exp = len([x for x in tokens(say.get(l['id'], l.get('say', ''))) if norm(x)])
    got = len(l['words'])
    last = l['words'][-1]['w'] if l['words'] else '-'
    flag = ''
    if got == 0 or got < 0.75*exp - 0.5:
        flag = '  <-- CUT OFF? fewer words than the script'
    elif l['words'] and l['e'] - l['words'][-1]['e'] > 1.2:
        flag = '  <-- long silence after the last word'
    bad += bool(flag)
    print(f"{l['id']:5} {l['who']:8} {got:>4}/{exp:<4} {l['s']:7.2f} {l['e']:7.2f}  {last}{flag}")
gaps = [(b['s'] - a['e'], a['id'], b['id']) for a, b in zip(T['lines'], T['lines'][1:])]
long_gaps = [g for g in gaps if g[0] > 3.2]
for g, a, b in long_gaps:
    print(f'NOTE: {g:.1f}s with no voice between {a} and {b} (he dislikes long silences; keep under ~3 s unless deliberate)')
print(f"duration {T['duration']:.1f}s" + (f" (target {target:.0f}s, {T['duration'] - target:+.1f}s)" if target else ''))
if target and T['duration'] > target + 10:
    print('NOTE: well over target: tighten gaps or a line now, before building.')
sys.exit(1 if bad else 0)
