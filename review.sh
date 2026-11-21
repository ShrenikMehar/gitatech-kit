#!/usr/bin/env bash
# Weekly review: turn the per-video notes into proposed kit improvements, for you to approve.
#
#   ./review.sh            run inside the kit (or anywhere: it finds the kit from its own folder)
#
# Reads ~/reels/.notes/*.md (written by batch.sh sessions), looks for problems that repeat, and makes the fixes on a
# local branch review-YYYY-MM-DD-HHMM: engine (lib/), PATTERNS.md, starter/ or skill/SKILL.md. It never touches main and
# never pushes. You read ~/reels/.notes/review-YYYY-MM-DD-HHMM.md, check the diff, then merge or throw the branch away:
#   git diff main..review-YYYY-MM-DD-HHMM           # what it changed
#   git checkout main && git merge review-YYYY-MM-DD-HHMM && git push     # approve
#   git branch -D review-YYYY-MM-DD-HHMM            # reject
# Processed notes move to ~/reels/.notes/reviewed/ so the next review only sees new ones.
set -u
KIT=${GT:-$(cd "$(dirname "$0")" && pwd)}
NOTES=$HOME/reels/.notes
mkdir -p "$HOME/reels/.logs"
DAY=$(date +%F-%H%M)
BRANCH=review-$DAY
mkdir -p "$NOTES/reviewed"
cd "$KIT" || exit 1
if [ -n "$(git status --porcelain)" ]; then echo "the kit has uncommitted changes; commit or stash them first"; exit 1; fi
git checkout -q main && git pull -q --ff-only 2>/dev/null
git checkout -q -b "$BRANCH" || exit 1
find "$NOTES" -maxdepth 1 -name '*.md' ! -name 'review-*' > /tmp/gt_review_notes.txt
N=$(wc -l < /tmp/gt_review_notes.txt | tr -d ' ')
if [ "$N" -eq 0 ]; then git checkout -q main; git branch -q -D "$BRANCH"; echo "no new notes in $NOTES"; exit 0; fi
PROMPT="You are reviewing the Gita x Tech reel kit at $KIT (branch $BRANCH, already checked out) using $N notes that past
reel-making sessions left in $NOTES (the list of files is in /tmp/gt_review_notes.txt). Read them all.

1. Group the notes into themes. Only act on problems that repeat (2+ notes) or that broke a video; ignore one-offs and taste.
2. For each theme, make the smallest fix in the right place: a bug in lib/ (fix it, keep the API), a missing or clumsy
   helper (add to lib/episode.py and document it in PATTERNS.md), a technique worth reusing (PATTERNS.md, written as a
   tool, not as an episode), or guidance (skill/SKILL.md, keep it soft guidance, never hard rules, never 'copy what worked').
   Do not add episode code, templates or lists of past topics or settings: the kit must stay a blank page.
3. Test what you changed: render a few stills from starter/ (copy it to /tmp, run voices.py, then ep.py --still).
4. Commit on $BRANCH in small commits whose messages start with a capitalised action (Add, Fix, Update, Remove), no type prefixes. Do not touch main, do not push, do not merge.
5. Write $NOTES/review-$DAY.md for Shrenik: one bullet per change (what, why, which notes), then themes you saw but left
   alone and why. Short and factual.
If nothing deserves a change, commit nothing and say so in the review file."
claude -p "$PROMPT" --allowedTools "Read,Write,Edit,Bash,Glob,Grep" > "$HOME/reels/.logs/review-$DAY.log" 2>&1
STATUS=$?
git checkout -q main
if [ $STATUS -ne 0 ]; then echo "review session failed (notes kept for next time), see ~/reels/.logs/review-$DAY.log"; exit 1; fi
while IFS= read -r f; do mv "$f" "$NOTES/reviewed/"; done < /tmp/gt_review_notes.txt
if [ -z "$(git log main..$BRANCH --oneline)" ]; then
  git branch -q -D "$BRANCH"; echo "no changes proposed. Summary: $NOTES/review-$DAY.md"
else
  echo "proposed changes on branch $BRANCH:"; git log --oneline main..$BRANCH
  echo "read $NOTES/review-$DAY.md, check 'git diff main..$BRANCH', then merge or delete the branch"
fi
