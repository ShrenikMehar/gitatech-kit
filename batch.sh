#!/usr/bin/env bash
# Make many reels with Claude Code, one fresh session per video (so every video costs about the same).
#
#   ./batch.sh topics.txt [parallel]      parallel = videos at once (default 2)
#
# topics.txt: one video per line,  NAME | topic, verse idea, anything else you'd type in chat
#   D1_Kubernetes | Kubernetes ← Gita 2.22: changing clothes = replacing pods
#   D2_Webhooks   | Webhooks ← Gita 4.7–8: whenever dharma declines, I come
# Blank lines and lines starting with # are skipped.
# Output: ~/reels/out/NAME.mp4   Logs: ~/reels/logs/NAME.log   Notes: ~/reels/notes/NAME.md   Work: ~/reels/NAME/
# Needs: Claude Code logged in and the gita-tech-reels skill in ~/.claude/skills/. Run it from inside the kit.
set -u
TOPICS=${1:?usage: ./batch.sh topics.txt [parallel]}
PAR=${2:-2}
KIT=${GT:-$(cd "$(dirname "$0")" && pwd)}   # the kit = the folder this script is in
OUT=${REELS_OUT:-$HOME/reels/out}
LOGS=$HOME/reels/logs
NOTES=$HOME/reels/notes          # one short note per video; ./review.sh turns them into kit improvements
mkdir -p "$OUT" "$LOGS" "$NOTES"
git -C "$KIT" pull -q --ff-only 2>/dev/null || echo "note: could not update the kit, using the local copy"

run_one() {
  local name="$1" topic="$2"
  mkdir -p "$HOME/reels/$name"
  local prompt="Use the gita-tech-reels skill in batch mode: make exactly one video, don't ask me anything, decide everything yourself.
Topic: $topic
The kit is at $KIT (export GT=$KIT). Work in $HOME/reels/$name.
Name the final file $name.mp4 and copy it to $OUT/.
Run every render in the foreground and wait for it to finish before you end.
Before you end, write $NOTES/$name.md: a heading with the name and today's date, then 2-4 short factual bullets: what broke or needed a workaround (and the fix), which kit helper or pattern was missing or clumsy, and anything that worked notably well. Facts only, no praise. Skip a bullet rather than invent one.
End with one line: the output path, its length, and anything that deviates from the topic."
  if (cd "$HOME/reels/$name" && claude -p "$prompt" --allowedTools "Read,Write,Edit,Bash,Glob,Grep" >"$LOGS/$name.log" 2>&1) \
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
