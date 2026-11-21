#!/usr/bin/env bash
# Make many reels with Claude Code, one fresh session per video (so every video costs about the same).
#
#   ./batch.sh topics.txt [parallel]      parallel = videos at once (default 2)
#
# topics.txt: one video per line,  NAME | topic, verse idea, anything else you'd type in chat
#   D1_Kubernetes | Kubernetes ← Gita 2.22: changing clothes = replacing pods
#   D2_Webhooks   | Webhooks ← Gita 4.7–8: whenever dharma declines, I come
# Blank lines and lines starting with # are skipped.
# Output: ~/reels/out/NAME.mp4 (the only folder you need to open).
# Hidden: working files ~/reels/.work/NAME/ (pruned after 7 days), logs ~/reels/.logs/, notes ~/reels/.notes/.
# Needs: Claude Code logged in and the gita-tech-reels skill in ~/.claude/skills/. Run it from inside the kit.
set -u
TOPICS=${1:?usage: ./batch.sh topics.txt [parallel]}
PAR=${2:-2}
KIT=${GT:-$(cd "$(dirname "$0")" && pwd)}   # the kit = the folder this script is in
OUT=${REELS_OUT:-$HOME/reels/out}
LOGS=$HOME/reels/.logs
NOTES=$HOME/reels/.notes         # one short note per video; ./review.sh turns them into kit improvements
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
Only if the kit itself broke or forced a workaround (a crash, a wrong result from a helper, something you had to patch), write $NOTES/$name.md with one short bullet per problem and its fix. Most videos need no note: skip layout choices, length, taste and tips.
End with one line: the output path, its length, and anything that deviates from the topic."
  if (cd "$WORK/$name" && claude -p "$prompt" --allowedTools "Read,Write,Edit,Bash,Glob,Grep" >"$LOGS/$name.log" 2>&1) \
     && [ -f "$OUT/$name.mp4" ]; then
    echo "done    $name  -> $OUT/$name.mp4"
  else
    echo "FAILED  $name  (see $LOGS/$name.log)"
  fi
}

n=0
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in ''|\#*) continue ;; esac
  name=$(printf '%s' "${line%%|*}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  topic=$(printf '%s' "${line#*|}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  if [ "$name" = "$line" ] || [ -z "$name" ] || [ -z "$topic" ]; then
    echo "skipped (needs 'NAME | topic'): $line"; continue
  fi
  while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do sleep 5; done   # works with macOS's bash 3.2 too
  echo "start   $name"
  run_one "$name" "$topic" &
  n=$((n + 1))
done < "$TOPICS"
wait
echo "batch finished: $n video(s). Files in $OUT"
