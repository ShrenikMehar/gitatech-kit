#!/usr/bin/env bash
# Make reels with Claude Code, one after another, one fresh session per video (so every video costs about the same).
#
#   ./batch.sh topics.txt
#
# topics.txt: one video per line,  NAME | topic, verse idea, anything else you'd type in chat
#   D1_Kubernetes | Kubernetes ← Gita 2.22: changing clothes = replacing pods
#   D2_Webhooks   | Webhooks ← Gita 4.7–8: whenever dharma declines, I come
# Blank lines and lines starting with # are skipped.
# Want two at once? Run a second terminal with a different topics file (the same file would make the same reels twice).
# Output: ~/reels/out/NAME.mp4 (the only folder you need to open). Progress prints live in the terminal.
# Hidden: working files ~/reels/.work/NAME/ (pruned after 7 days), full logs ~/reels/.logs/, notes ~/reels/.notes/.
# Model: Claude Code's default unless you set one, e.g.  REEL_MODEL=sonnet ./batch.sh topics.txt
# Needs: Claude Code logged in and the gita-tech-reels skill in ~/.claude/skills/.
set -u
TOPICS=${1:?usage: ./batch.sh topics.txt}
KIT=${GT:-$(cd "$(dirname "$0")" && pwd)}   # the kit = the folder this script is in
OUT=${REELS_OUT:-$HOME/reels/out}
LOGS=$HOME/reels/.logs
NOTES=$HOME/reels/.notes         # a note only when the kit broke; ./review.sh turns them into kit fixes
WORK=$HOME/reels/.work           # episode code, voices, stills; kept 7 days so a shot can still be fixed
mkdir -p "$OUT" "$LOGS" "$NOTES" "$WORK"
find "$WORK" -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} + 2>/dev/null

run_one() {
  local name="$1" topic="$2"
  mkdir -p "$WORK/$name"
  local prompt="Use the gita-tech-reels skill in batch mode: make exactly one video, don't ask me anything, decide everything yourself.
Topic: $topic
The kit is at $KIT (export GT=$KIT). Work in $WORK/$name.
Name the final file $name.mp4 and copy it to $OUT/.
Run every render in the foreground and wait for it to finish before you end.
Progress is shown to me from your messages: before each stage (choosing the format, writing the dialogue, voices, building the scene, stills, rendering) write one short line saying what you're doing, e.g. 'Writing the dialogue'.
Only if the kit itself broke or forced a workaround (a crash, a wrong result from a helper, something you had to patch), write $NOTES/$name.md with one short bullet per problem and its fix. Most videos need no note: skip layout choices, length, taste and tips.
End with one line: the output path, its length, and anything that deviates from the topic."
  # --strict-mcp-config: no MCP servers or claude.ai connectors. Reels don't need them, and each one's tool list
  # was re-sent on every turn (the first test reel loaded 60 tools instead of 25).
  (cd "$WORK/$name" && claude -p "$prompt" --allowedTools "Read,Write,Edit,Bash,Glob,Grep" --strict-mcp-config \
      ${REEL_MODEL:+--model "$REEL_MODEL"} --output-format stream-json --verbose </dev/null 2>"$LOGS/$name.err" \
    | python3 -u "$KIT/lib/progress.py" --log "$LOGS/$name.log")
  [ -f "$OUT/$name.mp4" ]
}

n=0; ok=0; failed=""
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in ''|\#*) continue ;; esac
  name=$(printf '%s' "${line%%|*}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  topic=$(printf '%s' "${line#*|}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  if [ "$name" = "$line" ] || [ -z "$name" ] || [ -z "$topic" ]; then
    echo "skipped (needs 'NAME | topic'): $line"; continue
  fi
  n=$((n + 1))
  echo ""
  echo "[$n] $name: $topic"
  if run_one "$name" "$topic"; then
    ok=$((ok + 1)); echo "  done -> $OUT/$name.mp4"
  else
    failed="$failed $name"; echo "  FAILED (full log: $LOGS/$name.log, errors: $LOGS/$name.err)"
  fi
done < "$TOPICS"
echo ""
echo "batch finished: $ok of $n made. Files in $OUT"
[ -n "$failed" ] && echo "failed:$failed (put just those lines in a new file to retry)"
exit 0
