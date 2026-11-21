# Patterns

Techniques collected from ~90 episodes, written as tools rather than examples. Use whichever ones the
scenario needs; none of them is required, and new episodes can invent their own. Helpers named `E.*` live in
`lib/episode.py`, `K.*` in `lib/gt.py`, `Wd.*` in `lib/world.py`, iso primitives in `lib/iso.py`.

## Driver rules (these keep rendering correct)
- `frame(t)` must be a **pure function of t**. Workers render frames out of order, so no state carried
  between frames. Compute positions from t ("where is the parcel at t?"), never by stepping.
- **All beat times come from word times**: `E.w('L4', 3)` (start of audio word 3 of line L4), `E.we(...)` (its end),
  `E.cut('L3', 'L4')` (a shot boundary between lines). Never hard-code seconds; re-voicing would break them.
  Word indices are what `voices.py` prints (`index:word@time`); audio words can differ from caption tokens.
- `SHOTS = [(start, kind, key)]` + `E.shot_at(t, SHOTS)` gives the current shot and when it ends.
- `E.setup(page_at=..., emph=...)`: `page_at` = audio word index where page 2 of a `|` caption starts;
  `emph` = words that get a nod and brow lift.
- Finish every frame with `E.finish_frame(c, t, SHOTS)` (vignette, cut flash, karaoke caption, end fade).

## Timing helpers
- `ramp(t, a, d)`: 0 then 1 over d seconds from a. `E.plate(t, a, b, f)`: in at a, out at b.
- `bump(t, a, b)`: 0, 1, 0 (flashes, pulses). `back_out(k)`: overshoot pop for scaling things in.
- `ease`, `ease_out`, `lerp`, `clamp`. A pop-in: `s = back_out(k) if k < 1 else 1` with `k = clamp((t - t0)/0.35)`.

## Characters
- **Inside the world**: `E.standing_bust(c, key, t, t0, x, y_bottom, scale, flip=False)`. It talks when its
  character speaks, blinks, nods on emphasised words, glances away in pauses. Call it from the world's
  `scene()` via a callable in the state so depth order is right.
- **Close-up**: `E.closeup(c, key, t, t0, t1, backdrop=lambda c, t: E.blur_backdrop(c, draw_scene, t))`.
  A blurred render of the current world behind the bust keeps the place present.
- Expression keys (`gt.BASE`): krishna, krishna_smile, krishna_knowing, arjun_panic, arjun_worried, arjun_curious,
  arjun_relief, arjun_frustrated, arjun_sheepish, arjun_determined. Switch expression on a beat, for example a list
  `[(t, key), ...]` and pick the last one with `t >= start`.
- New expression: add a preset to `chars.EXPR[who]`, then `K.BASE[key] = (who, chars.EXPR[who][name])` and
  `K.MOUTHS[key] = (rest, talk1, talk2)` in the driver.
- Other characters: a new bust needs drawing code in `chars.py`. Simple extras (a coolie, a sevak, a crowd) are
  often better drawn directly in the world as flat shapes with a pose dict (mood, tilt, hold, look).
- Extra voices: `"voices": {"phone": {"engine": "edge", "name": "en-IN-NeerjaNeural", "rate": "-4%", "pitch": "+0Hz"}}`
  in script.json, then `"who": "phone"` on its lines. Other options: `hi-IN-SwaraNeural` (female),
  `en-IN-PrabhatNeural`, or Madhur with a different pitch.

## Cameras and layout
- **Flat 2D**: the world is drawn in its own coordinates and the camera is a tuple `(scale, focus_x, focus_y, screen_y)`:
  `c.translate(540, screen_y); c.scale(s, s); c.translate(-fx, -fy)`. Lerp between named layouts
  (e.g. a "stage" layout and a "world under a panel" layout) with an eased k.
- **Isometric**: `iso.Cam(x, y, zoom, sy0=...)`; `cam.p(x, y, z)` maps world to screen. Keyframe cameras as tuples
  and blend with `K.cam_lerp(A, B, k)` / `K.C(A)`. Draw objects sorted by depth (x + y). Boxes and cylinders:
  `iso.box`, `iso.cylinder`; text on a face: `c.concat(iso.front_left_matrix(cam, x, y, z)); c.scale(0.01, 0.01)`,
  then normal font sizes (~30).
- Slow drift keeps static shots alive: `fx + 6*sin(2*pi*t/9)`.
- **Shake** on an impact: `k = bump(t, T - 0.05, T + 0.5); dx, dy = 14*k*sin(t*71), 10*k*sin(t*53 + 1)`.
- **Split screen**: draw the world into a region with `c.saveLayerAlpha(skia.Rect(0, y0, W, y1), alpha)`, code panel
  on top. Slide the panel from full screen to the top half with a lerp on its y.
- Keep action in the middle band (y ~300 to ~1400). HUD lives top-right (y < ~190), captions from y 1440 down.

## Moving things
- **Pass an object between holders** (a parcel hop to hop, a request server to server): keyframes
  `[(t0, from_xy, t1, to_xy), ...]`; between t0 and t1 lerp with `ease(k)` and lift by `70*sin(pi*k)` for an arc;
  between keyframes it sits at the holder. Return which holder has it, so that holder can react.
- **Transform an object** (postcard folds into a locked box): squash the old one's y-scale to 0 while the new one
  pops in with `back_out`, overlapping slightly.
- **Pile up / overflow**: count = a step function of t (`sum(1 for ti in TIMES if t >= ti)`), position each item
  from its index; a topple is one more eased rotation after a threshold time.
- **Flows** (water, requests, packets): points along a path at `(t*speed + i/n) % 1` give a continuous stream.

## Tech on screen
- **Code panel**: `E.panel(c, x0, y0, x1, y1, a, title='OrderService.ts')` + `E.code_line(c, [(text, kind), ...], x, y, a, size)`
  with kinds kw, cls, fn, fn2, str, p, id, cm, ok, err, dim. Type it out with `nchars=int(len*k)` and a blinking
  caret (draw a thin rect when `sin(t*12) > -0.2`).
- **Highlight one line**: a rounded rect behind it in `Wd.DEAD_C` (bug) or `Wd.RUN_C` (fixed), fill at ~0.18
  alpha plus a 2.4 px border.
- **Terminal**: lines `(prompt, text, kind, t0, t1)` typed between t0 and t1; caret only on the last active line.
- **Scramble** (plain text into encrypted bytes): per line, cross-fade `code_line(plain)` out and `code_line(hex)` in
  with a staggered k (`clamp((k*3 - i*0.6)/1.2)`).
- **Git graph**: a straight main line, a cubic-curve branch that rejoins, commits as circles popping in on their
  beats, conflict shown by turning nodes red and an X at the merge.
- **Browser**: URL bar pill with a lock or warning icon, `http` in err colour vs `https` in ok colour.
- Real code must be correct and consistent across versions. Indian number format (10,00,000). JetBrains Mono
  here is a latin subset: no arrows or crosses, use `›` and draw icons with paths.

## Labels, numbers, cards
- `concept_tag(c, x, y, 'tech term', 'metaphor', a, k)`: one per moment, tech term first, y ~300 to ~420 (or wherever free).
- `E.pill(c, x, y, text, col, a, size, k)`: small labels on objects. `Wd.chip(...)`: iso labels that hide in safe zones.
- `E.hud(c, t, label, value, col, t_change, a, sub)`: one number that tells the story, popping on change. A HUD gag
  on the punchline has landed well (READ BY 0, counter rolling to 18/18).
- **Live graph** under the HUD: sample the same pure function over a trailing window (`t - 14` to t) into points
  and draw a polyline.
- **Speech bubbles**: rounded rect + tail, mono for code-ish text, pop with back_out.
- **Verse card**: `E.verse_card(c, t, t_in, ['line 1', 'line 2'], 'GITA 7.7')`. Devanagari goes through
  `K.draw_deva` (Pillow + raqm). Tiro has no Latin punctuation, so use `।` and write the reference in Latin.
- **A belief that breaks**: a dashed arrow (`skia.DashPathEffect.Make([22, 14], -t*40)`) drawn growing, then it
  drops a few px and fades while a red X appears at its middle.

## Atmosphere
- `iso.glow(c, x, y, r, col, a)` for lamps, auras and highlights; `Wd.particles(c, t)` for dust and sparks; `Wd.sky`,
  `Wd.diya`, `K.mandala` exist.
- Rain: many short slanted lines at `(seed_x + t*speed) % H`; lightning: a full-screen white flash with
  `bump()` plus a jagged path for 2 to 3 frames.
- Time of day mostly comes from the backdrop gradient and one glow; it is cheap and changes the mood a lot.

## Sound
- `cues()` returns `[(t, name, gain_db)]`. Names: whoosh, swell, pop, hit, glitch, tick, bowl, riser, chime
  (station jingle), train (pulling in + horn). A whoosh just before each cut (`start - 0.1`) and a bowl on the
  verse card are good defaults.
- The tanpura bed (`"music": {"bed": "tanpura", "gain": -22}`) is the default. A scenario can get its own
  soundscape by extending `lib/mix.py`.

## Checking and fixing
- `python3 $GT/lib/check.py <ep> --target 50` right after voices: flags cut-off lines and long silences, prints the length.
- Stills: `python3 ep.py --still 1 5 9 ...` writes `stills/sheet.png`; look at the sheet plus 2 to 3 key frames.
- Fix one shot after the render: `python3 $GT/lib/splice.py <ep> A B --name <Name>` re-renders only [A, B) and splices it in.
  Changed dialogue means a full `finish.py` instead.

## Gotchas
- skia's SVG renderer drops gradient fills on `<ellipse>`: draw ellipses as paths.
- Caption tokens split at `*`: trailing punctuation is moved inside the emphasis on load.
- Watch labels colliding when objects pass each other; fade labels of finished actors.
- An object in front of the path of moving things hides the key motion: check every important motion on a still.
- Objects placed beside a standing bust can cover its face: keep props clear of the bust's face x, or move the bust.
- Bright daytime scenes make the HUD unreadable: `E.hud(..., plate=True)`.
- Length: about 2.4 spoken words per second of reel, gaps included (45 s is about 110 words).
- Phone readability: keep text at 26 px or more and standing busts at 0.35 scale or more; tiny labels mean the shot is too busy.
- Bust renders are cached; a new (expression, mouth, blink, brow, gaze) combination costs ~50 ms the first time.
- Render speed is roughly 2.5 to 3 frames/s per 2 cores.
