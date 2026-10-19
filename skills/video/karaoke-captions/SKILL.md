---
name: karaoke-captions
description: Animated word-by-word karaoke captions overlay for vertical videos (Reels/TikTok/Shorts), Hormozi-style with a monochrome look: words appear as spoken, the current word pops on a white chip with black text, keyword words keep the chip. Use when a talking-head / voiceover vertical video needs animated viral captions timed to the speech. Not for post copy or hashtags.
---

# Karaoke Captions: animated word-by-word overlay

Renders a transparent PNG frame sequence (one per frame) composited over the
video with ffmpeg. Words appear exactly as spoken, the current word pops
(x1.3 -> 1.0 over 5 frames) on a white chip; keyword words (kw=1 in the
spec) keep the chip after being spoken.

## Workflow

1. Get word timings per clip: `whisper-cli -m <model> -f clip.wav -l en -np
   -ml 3` and offset each clip by its start time in the final edit.
2. Write a spec JSON (see below), then:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/karaoke_captions.py --frames-dir <run>/_cap_frames \
     --dur 56.4 --spec captions.json
   ffmpeg -i base.mp4 -framerate 24 -i _cap_frames/%04d.png \
     -filter_complex "[0:v][1:v]overlay=0:0[v]" \
     -map "[v]" -map 0:a -c:v libx264 -pix_fmt yuv420p -crf 20 -c:a copy out.mp4
   ```

## Spec JSON

```json
[
  {"t0": 0.0, "t1": 3.2, "words": [
    ["the", 0.01, 0.43, 0], ["most", 0.43, 0.54, 0],
    ["beautiful", 0.54, 1.24, 1]]}
]
```

One object per chunk (a spoken phrase); words = [text, start, end, keyword].
Chunks auto-wrap greedily into centered lines of max ~920px (measured, so a
line can never overflow the 1080px frame; the old midpoint split did).
Keep chunks to one breath / one phrase (split long sentences at commas);
2 lines max reads best.

## Hard-won rules

- **Whisper word timings lag the voice**: the script anticipates by
  `--shift` seconds (default 0.20). If the user says captions feel late/early,
  tune only this constant.
- If a clip is re-generated, re-transcribe it and update its chunk times,
  never reuse timings from a previous take.
- Reels-safe: default y=1365 sits just above a roulette chip at cy=1560;
  `--y-late` + `--late-after` drop captions lower once the block disappears.
- Monochrome look: white Helvetica Bold with black outline, keyword chip =
  white fill + black text. No emoji, no arrows in the text (font has no
  glyphs for them -> tofu).
- Font: the default is macOS Helvetica Neue (Bold face, index 1). On Linux or
  Windows pass `--font <file.ttf> --font-index 0`.
- Requires Python 3 with Pillow, ffmpeg, and whisper-cli (whisper.cpp) for the
  word timings.
