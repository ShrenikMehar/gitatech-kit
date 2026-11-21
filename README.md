# Gita x Tech reel kit

Code-drawn vertical reels (1080x1920, 30 fps): Krishna and Arjun explain a tech concept through a Gita idea, in Hinglish.
No image/video AI, no GPU. Every frame is drawn with skia-python; voices are Microsoft neural voices (edge-tts);
the tanpura bed and SFX are synthesised. Used by the `gita-tech-reels` skill.

## Layout
```
setup.sh          one-time deps (skia-python, edge-tts, soundfile, pillow+raqm, numpy; checks ffmpeg). Safe to re-run.
batch.sh          Claude Code: many videos from topics.txt, one fresh session each
review.sh         weekly: turns ~/reels/notes (one per video) into proposed kit fixes on a branch you approve
skill/SKILL.md    the gita-tech-reels skill (source of truth; claude.ai copy is saved from this)
PATTERNS.md       reusable techniques (cameras, moving objects, code panels, HUD, cards, sound, fixing)
starter/          a blank episode showing only the mechanics: ep.py (driver), scene.py (world), script.json
lib/episode.py    driver runtime: timeline, word times, busts with life motion, close-ups, verse card, HUD,
                  code panels, captions + frame finishing, render CLI (--still / --cues / --range / --workers)
lib/chars.py      Krishna + Arjun busts (generated SVG -> skia), EXPR presets
lib/gt.py         easing, cam_lerp, BASE/MOUTHS expression keys, blink, karaoke captions, Devanagari, card, concept_tag
lib/iso.py        isometric camera + primitives (Cam, box, cylinder, face matrices, glow, blurred)
lib/world.py      fonts, text, chip labels, vignette, colours, sky/particles/diya
lib/voices.py     script.json -> data/narration.wav + timeline.json (real word times, mouth track)
lib/check.py      after voices: flags cut-off lines and long silences, prints length vs target
lib/mix.py        narration + bed + SFX cues -> data/mix.wav (-14 LUFS)
lib/finish.py     cues -> mix -> full render -> mux -> qa.png
lib/splice.py     re-render one time range of a finished episode and splice it in
fonts/            Inter, Poppins, Cinzel, JetBrains Mono (latin subset), Tiro Devanagari
```

## One episode
```
export GT=~/gitatech-kit
cp -r $GT/starter ~/reels/my_ep && cd ~/reels/my_ep        # then rewrite script.json, scene.py, ep.py
python3 $GT/lib/voices.py .                                 # prints index:word@time for every line
python3 $GT/lib/check.py . --target 50                      # cut-offs, silences, length
GT_EP=$PWD python3 ep.py --still 1 5 9 13 17                # stills/ + stills/sheet.png
python3 $GT/lib/finish.py . --name B16_Topic                # -> B16_Topic.mp4 + qa.png
python3 $GT/lib/splice.py . 21.0 24.5 --name B16_Topic      # optional: fix one shot without a full re-render
```

## Many episodes (Claude Code on your laptop)
One-time: `mkdir -p ~/.claude/skills/gita-tech-reels && ln -sf "$PWD/skill/SKILL.md" ~/.claude/skills/gita-tech-reels/SKILL.md`
(run inside the kit; the link means a `git pull` also updates the skill).
```
./batch.sh topics.txt 2      # topics.txt lines: NAME | topic ← Gita x.yy: idea
```
Finished reels land in `~/reels/out/`. Working files (`~/reels/.work/`, kept 7 days), logs and notes are hidden folders.

## Getting better over time
Each batch session writes a short note to `~/reels/.notes/NAME.md`. Run `./review.sh` about once a week: it groups the notes,
fixes repeated problems on a branch `review-<date>` (never on main), and writes `~/reels/.notes/review-<date>.md`.
Read it, check `git diff main..review-<date>`, then merge + push to approve or delete the branch to reject.

## Mac notes
`brew install ffmpeg fribidi` (fribidi gives Pillow's raqm the Devanagari shaping; setup.sh warns if it's missing).

## Changing the kit
Sessions only read this repo. Commit here when the engine or the patterns improve (a voice fix, a new helper,
a technique worth reusing). Episode code is not kept here, so new episodes start from a blank page.
