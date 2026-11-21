---
name: "gita-tech-reels"
description: "Make a 'Gita × Tech' vertical reel with Krishna and Arjun (Hinglish) that explains a tech concept through a Gita idea, fully code-drawn with the gitatech kit. Use for new episodes, new formats, topics or scenes, or fixes to one."
---

# Gita × Tech reels

Vertical reels (1080×1920, 30 fps, usually 30–60 s, longer when the topic needs it) for a tech + Gita page: a tech concept made clear through one Gita idea, with Krishna and Arjun. Everything is code: skia-python worlds, SVG-generated Krishna/Arjun busts, karaoke Hinglish captions, Microsoft neural voices (edge-tts, free, no key), a synthesised tanpura bed and SFX. No image/video AI, no GPU.

**How to read this skill.** Everything below is soft guidance and lessons from past episodes, not hard rules. The owner wants creative freedom in every part: hook, structure, script, dialogue, characters, scenes, sound, even how you discuss options with him. Make whatever makes the best episode for the concept. What he consistently cares about: his approval workflow (or batch mode when he asks for it), technical accuracy, the tech coming across clearly without crowding the screen, enough dialogue, and the recognisable Krishna/Arjun look and voices. Only three things are firm: technical accuracy, the Krishna/Arjun look and voices, and his approval gates (outside batch mode). Everything else, including words like 'never' or 'keep under' below, is a default that bends: if breaking it makes a genuinely better reel, break it and mention the change in one line. Interpret, don't follow mechanically.

He posts about 9 reels a day, so **repeating a topic now and then is fine**. Don't check past episodes for repeats; if a topic comes up again, just make it fresh. Verses can repeat too (2.47 can come back many times): pick the verse that maps best.

## 0. Get the kit (every new session, silently, before asking anything)
The kit is the private GitHub repo **ShrenikMehar/gitatech-kit**. Sessions only read it. Try in order:
1. If `$GT` is set or `~/gitatech-kit/lib/episode.py` exists (Claude Code on his laptop, or a workspace that kept it), use it as it is. Don't pull: he updates it himself with `git pull`, so the code and these instructions always come from the same version.
2. Otherwise clone it: `git clone https://github.com/ShrenikMehar/gitatech-kit ~/gitatech-kit`. In claude.ai, attach the repo first with the add-repo tool (read access), then clone.
3. If the repo can't be reached (GitHub not connected on this account): use an attached `gitatech-kit.zip`, or, if his computer is connected, ask in one line whether to look for it in Downloads. Otherwise ask him in one line to connect GitHub or attach the zip. Beats and dialogue don't need the kit, so keep going on those while you wait. Never rebuild the kit from scratch: Krishna, Arjun and the look would not match.
Then `export GT=~/gitatech-kit` (or wherever it is), `bash $GT/setup.sh`, and read `$GT/README.md`, `$GT/PATTERNS.md`, `$GT/API.md` (every helper's signature) and `$GT/starter/`. Don't read the library source in `lib/` unless something breaks or a helper in API.md is unclear: everything read stays in context for every later turn, so reading the source makes each reel cost far more.

The kit holds the engine (`lib/`), fonts, a blank `starter/`, `PATTERNS.md` (techniques from past episodes), `batch.sh` and this skill (`skill/SKILL.md`). It deliberately holds **no past episode code**, so new episodes start from a blank page instead of copying an old one. Change the repo only when he asks to improve the engine or patterns (after changing a helper, re-run `python3 lib/apidoc.py` so API.md stays current; small commits, messages starting with a capitalised action like "Add", "Fix", "Update", no type prefixes; push needs push access). Don't save episodes to it, and don't suggest committing episode files: `~/reels` is not a git repo, and he only wants the mp4.

## 1. Workflow
### Normal mode (one topic, wait for an OK at each gate)
1. **Topic**: if he hasn't given one, suggest 4–6 with the Gita link and a one-line visual idea; give your pick. Any CS/dev concept works.
2. **Beats**: start with the one-sentence takeaway about the tech and the key moments where real tech appears; then the verse + why it maps, the world, the beats, the ending. Check the concept is technically correct before proposing (he checks; a wrong label once had to be re-rendered). When the topic allows, offer two different formats with your pick and **give both the same depth** (takeaway, how the tech is shown, world, Gita link, 4–6 short beats, ending). Expand the chosen one into shot-by-shot beats only after he picks.
3. **Dialogue**: numbered lines, speaker + Hinglish only; list on-screen tags separately. No scene directions inside lines. Mention the rough length it will run.
4. **Build** right after the dialogue OK (section 4). Don't ask for approval of stills; don't render repeatedly.
5. **Deliver** with a short bullet summary of what happens on screen, plus one line on technical accuracy. Flag deviations (length, a split line) in one line each.

### Batch mode
He often sends a numbered list of topics, each with the verse already mapped ('Router ← Gita 18.61: ...'), plus 'don't stop, don't ask for approval, I just want the mp4 files, you decide everything'. Then skip every gate: pick the format, write beats and dialogue, build, QA and deliver all videos without asking anything. Still:
- Use his verse mapping, but check the reference. If a line comes from outside the Gita itself (e.g. the Gita Dhyanam's cows-and-milk line), attribute it correctly on screen.
- Name files exactly as he asks (e.g. `B13_VirtualMemory.mp4`). If he names a series but no numbers, continue from the last number in that chat.
- Overlap work: write the next episode's script, voices and world while the previous one renders.
- Deliver all files together, one short bullet per video (what happens, the setting, a one-line accuracy note).
This mode covers the batch he sent. `batch.sh` (Claude Code) runs each video as its own batch-mode session.

## 2. Story and script
### What stays the same
Krishna and Arjun as the core cast (same designs and voices; others can join when a concept is better with them), a technically correct concept, one Gita idea that really maps to it, a small shloka part, Hinglish karaoke captions, clarity (section 3) and the pacing below.

### Tech and story in balance
Viewers should clearly get the tech, but story, characters and world make it watchable. One episode hid the tech in a HUD and the metaphor, so it didn't read as a tech video; the next crammed a terminal, code, counter, graph and labels on screen at once. Aim between:
- **Make the concept clear early**, in whatever way fits: a line, a simple visual of the failure, a title, a phone screen.
- **Name the concept out loud in English** at a natural moment; tech terms stay in English in captions.
- **Real tech at the key moments, not all the time**: a few lines of real code big enough to read on a phone, one real number or error, then out of the way.
- **One focus per moment**: the main visual plus at most one tech element. If a viewer wouldn't know where to look, remove something.
- Code on screen must be correct and consistent; numbers in Indian format (10,00,000).
- Test before proposing: could a viewer say the concept in one sentence, and would they enjoy watching it?

### What is open
- **Structure.** Options that have worked: wordless failure hook → problem → Krishna names it → mechanism → Gita moment → fix → relief → punchline; cold open mid-conversation; Gita moment first, land on the tech; Krishna only asks questions until Arjun works it out; Arjun explains it wrong and Krishna corrects him; failure montage; before/after split screen; the world tells the story and one line lands at the end; a two-part cliffhanger.
- **Who speaks, and how.** No fixed opener or roles; 'Keshav!' is as good as anything. Extra voices (a narrator, another Pandava, a phone) are fine (see PATTERNS.md).
- **Length.** Default 30–60 s; shorter is fine for simple ideas. For a genuinely complex topic go longer (say so with the planned length) or offer a two-part episode. Never pad.
- **Ending.** A punchline last has worked well; a quiet close, a callback or a question to the viewer are fine.
- **Make these choices genuinely random**, not 'different from last time'. Roll for them to avoid habits, e.g. `python3 -c "import random; print(random.choice([...]))"`, then shape the episode around the result; re-roll or skip when a clearly better idea exists. Never mention the rolls to him.

### Dialogue
- **Dialogue throughout.** He disliked a reel with a long wordless stretch (the microservices one): keep any stretch without a voice under ~3 s, hooks included. Too sparse is also a miss: he rejected a 4-line script as too short; episodes that worked had roughly 9–13 lines. Rough length guide: about 2.2 spoken words per second of reel, gaps included (~100 words for 45 s); line counts mislead because long lines run ~7 s.
- **Krishna's register**: gentle tum-form, never orders: 'hatao', 'karo', 'dekho', not 'hata', 'kar'.
- **Gita moment small**: usually one spoken line with the verse on a small card for a few seconds, not recited in full.
- Tech terms spoken in English and shown on screen; a concept tag can pair the term with its metaphor, tech term first (`circuit breaker = kachhua`).
- Humour that landed: everyday Indian life (mummy's bag of bags, 'shaadi kab?', good-morning forwards, Kurukshetra callbacks). Keep jokes short.
- **Pacing**: `gap_before` 0.6–1.0 between speakers, ~0.9 before the Gita line, up to ~3 s of quiet where a visual payoff needs room. `outro` 1.5.
- **Voices (edge-tts)**: one Hindi male voice he picked for both: Arjun `hi-IN-MadhurNeural` rate `+12%`, pitch `+18Hz`; Krishna `hi-IN-MadhurNeural` rate `+4%`, pitch `-6Hz`. These are the `voices.py` defaults. He found the stock speed sluggish and +18%/+10% a touch fast, so don't drift slower or faster; get breathing room from `gap_before`, not slow speech. Microsoft leaves ~1 s between sentences; `voices.py` shortens pauses inside a line to `max_pause` (default 0.32 s). Kokoro is only for when the network is down (it sounded like English reading Hindi): `"voices": {"krishna": {"engine": "kokoro", "name": "hm_omega", "speed": 0.92}, "arjun": {"engine": "kokoro", "name": "hm_psi", "speed": 1.04}}`.
- **Writing `say`**: Hindi in Devanagari, English tech words in Latin letters (`मेरा cache full हो गया`) so they're said as English. Put names first rather than at the end of a sentence; prefer commas over '…'.
- `voices.py` gets **real word timings** (WordBoundary) and prints every line as `index:word@time`; use those indices for beats and caption page breaks (audio words can differ from caption tokens, e.g. numbers).
- `script.json` lines: `{id, who, mood, say, cap, gap_before?, rate?, pitch?}`. `cap` is Hinglish with `*emphasis*` and at most one `|` page break. Top level: `fps 30, lead, outro, max_pause?, voices?, music {bed: tanpura, gain: -22}, loudness: -14`. See `starter/script.json`.

## 3. Visuals
- **Clarity first.** One physical metaphor a viewer gets in 1 s without captions; cause → effect visible on screen; one hero object, big; at most 2 labels + 1 concept tag at a time; one state change at a time; prefer metaphors where the failure is obvious (jam, overflow, collapse, pile-up). A stone tortoise as a living arch with orbs and threads was 'weird and difficult to understand'; two chariots stuck on a one-lane bridge read instantly.
- **Setting: whatever the scenario needs.** Indian (ghat, bazaar, gurukul, railway station, temple kitchen), mythic, modern (office, metro, home kitchen, cricket ground), abstract or sci-fi. Map each tech entity to a physical thing. A familiar setting is fine when it serves the concept; he found scenes repetitive when the same few settings came back out of habit, so don't default to one without a reason.
- **Look and camera are open**: isometric worlds with bust close-ups, flat 2D side views, full-screen diagrams, code panels, split screens, characters inside the world, close-up-only. Keep Krishna and Arjun looking the same. Sound is open too: tanpura and the SFX set are defaults; a concept can get its own soundscape.
- A HUD (one number that tells the story) helps when it does; a HUD gag on the punchline has landed well.
- **Readable on a phone**: text and code big enough to read on a phone screen; if a shot needs many tiny labels, it's probably too busy.
- Safe zones: HUD top-right (y < ~190, plus any graph under it), captions from y 1440 down, action in the middle band (fill empty space by moving the camera, not by adding clutter). Concept tags and labels must not overlap: check on stills.

## 4. Building an episode
```
export GT=~/gitatech-kit
cp -r $GT/starter ~/reels/<name> && cd ~/reels/<name>    # rewrite script.json, scene.py and ep.py for this episode
python3 $GT/lib/voices.py .                              # prints index:word@time per line (use these for beats)
python3 $GT/lib/check.py . --target <planned s>          # cut-offs, long silences, length
GT_EP=$PWD python3 ep.py --still 1 5 9 13 ...            # stills/ + stills/sheet.png
python3 $GT/lib/finish.py . --name <FileName>            # cues, mix, render, mux, qa.png
```
- `starter/ep.py` shows the mechanics only (word-timed beats, shots, standing busts, close-up with verse card, HUD, cues); `lib/episode.py` holds the plumbing. Write the world and story fresh; take techniques from `PATTERNS.md`, not from memory of old episodes.
- **After voices, run check.py.** A truncated Krishna line once broke the voice ~15 s into a delivered reel; regenerate only the flagged line.
- **QA lean**: one still sheet plus 2–3 full-size frames, then `qa.png` after the render. Every image read costs a lot of context.
- **Fix one shot by splicing**: `python3 $GT/lib/splice.py . A B --name <FileName>` re-renders only [A, B). Changed dialogue needs a full finish.py.
- Renders use all cores by default (~4–5 min for a minute of video in the cloud). In claude.ai, run long renders in the background, tell him it's rendering, and wait with `sleep` loops (never busy loops). In Claude Code batch runs, render in the foreground.
- Deliver: in claude.ai copy the mp4 to `/mnt/user-data/outputs/` and send it with SendUserFile. In Claude Code (his laptop), work in `~/reels/.work/<name>/` and copy the finished mp4 to `~/reels/out/<name>.mp4`: he only wants the mp4, so `out/` is the one folder he opens (unless a batch prompt says otherwise).
- New expressions, extra characters and voices, cameras, code panels and other techniques: see PATTERNS.md.

## 5. Notes and the weekly review
**Most reels need no note.** On his laptop, write `~/reels/.notes/<name>.md` only when the kit itself broke or forced a workaround: a crash, a wrong result from a helper, something you had to patch or hand-roll that the kit should clearly handle. One short bullet per problem, with the fix. Leave out layout choices, length, taste, techniques that worked and tips for next time: those are judgement calls for each episode, and turning them into rules would make the kit rigid. `review.sh` turns notes that repeat into proposed fixes on a branch he approves. In claude.ai, skip notes unless he asks.

## 6. Gotchas (more in PATTERNS.md)
- Devanagari needs shaping: always `K.draw_deva` / `E.verse_card` (Pillow + raqm), never skia text. Tiro Devanagari has no Latin punctuation: use `।`, write the reference in Latin ('GITA 2.58').
- JetBrains Mono here is a latin subset: no `→` or `✕` (use `›`, draw icons with paths). Inter has `₹` and `↺`.
- skia's SVG renderer drops gradient fills on `<ellipse>`: draw ellipses as paths.
- An object in front of the path of moving things hides the key motion: check every important motion on a still.
