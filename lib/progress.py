"""Turn Claude Code's stream-json output into short progress lines, so a batch run shows it's working.

  claude -p "..." --output-format stream-json --verbose | python3 progress.py [--log FILE]

Prints one line per step (Claude's own short status lines, commands it runs, files it writes), with elapsed time.
--log keeps the full raw stream for debugging. Exit code 0 if the session reported success, 1 otherwise.
"""
import json
import os
import sys
import time

log = None
if '--log' in sys.argv:
    log = open(sys.argv[sys.argv.index('--log') + 1], 'w')
T0 = time.time()
ok = False
last = ''


def say(icon, text):
    global last
    text = ' '.join(str(text).split())
    if not text or text == last:
        return
    last = text
    m, s = divmod(int(time.time() - T0), 60)
    print(f'  {m:02d}:{s:02d} {icon} {text[:110]}', flush=True)


def tool_line(name, inp):
    base = lambda p: os.path.basename(str(p or ''))
    if name == 'Bash':
        return '$', inp.get('description') or inp.get('command', '').split('\n')[0]
    if name == 'Write':
        return '+', f'Writing {base(inp.get("file_path"))}'
    if name == 'Edit':
        return '~', f'Editing {base(inp.get("file_path"))}'
    if name == 'Read':
        f = base(inp.get('file_path'))
        return '?', (f'Looking at {f}' if f.endswith(('.png', '.jpg')) else f'Reading {f}')
    if name == 'Skill':
        return '*', f'Loading skill {inp.get("skill", "")}'
    return None


for raw in iter(sys.stdin.readline, ""):   # readline, not iteration: iteration buffers and delays progress
    if log:
        log.write(raw)
        log.flush()
    try:
        ev = json.loads(raw)
    except ValueError:
        continue
    kind = ev.get('type')
    if kind == 'assistant':
        for part in ev.get('message', {}).get('content', []):
            if part.get('type') == 'text':
                first = part.get('text', '').strip().split('\n')[0]
                if first:
                    say('»', first)
            elif part.get('type') == 'tool_use':
                tl = tool_line(part.get('name'), part.get('input') or {})
                if tl:
                    say(*tl)
    elif kind == 'result':
        ok = ev.get('subtype') == 'success' and not ev.get('is_error')
        mins = ev.get('duration_ms', 0)/60000
        say('✓' if ok else '✗', f'session {"finished" if ok else "failed"} in {mins:.1f} min, {ev.get("num_turns", "?")} turns')
        res = (ev.get('result') or '').strip().split('\n')
        if res and res[-1]:
            say('»', res[-1])
sys.exit(0 if ok else 1)
