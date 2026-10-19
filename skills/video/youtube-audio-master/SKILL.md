---
name: youtube-audio-master
description: "Audit and repair the audio of a finished video before publishing: integrated loudness, true peak, real clipping, and level jumps between assembled blocks. Use when a master is about to be uploaded to YouTube, when the sound is described as too loud/too quiet/saturated/distorted/uneven, when volume jumps between two parts of an edit, or when asked whether the audio of a video is well optimised."
---

# YouTube Audio Master

Bring a finished video to YouTube's delivery target (**-14 LUFS integrated, -1 dBTP,
48 kHz**) without ever re-encoding the picture.

## Why -14 and not louder

YouTube normalises playback to roughly -14 LUFS. A master pushed to -10 gets attenuated
on playback, so it sounds **no louder than -14**: it only keeps whatever distortion the
extra gain caused. Pushing past the target is a pure loss.

## Workflow

### 1. Diagnose first, always

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/audio_report.py "<video>" [--window 60] [--json]
```

Reports loudness, true peak, **clipped sample count**, and a per-window loudness profile.
Runs at roughly real-time/8 for a 4K master (~2 min for 18 min of video).

Read the output in this order:

- `clipping` above 0 -> distortion is baked in. Go to step 2 before normalising.
- `spread` above ~2 LU -> the video was assembled from blocks at different levels.
  The profile shows exactly where it jumps.
- `loudness` / `true peak` -> fix in step 3.

### 2. If clipped, try to rebuild instead of normalise

**This is the decision that matters.** Normalising a clipped master lowers the level but
keeps the flat-topped waveforms. If the clean export of the damaged section still exists,
replacing it removes the distortion entirely.

```bash
# which local export does this master's damaged section come from?
python3 ${CLAUDE_SKILL_DIR}/scripts/find_source.py "<master>" "<candidate1>" "<candidate2>" ...
```

Score >= 0.5 means a confident match, with the offset where it sits in the master.

Before swapping, confirm nothing was *added* over that block (music, SFX), otherwise the
replacement erases it. See `references/diagnosis.md` for the gain-vs-compressor-vs-added
test. Then:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/rebuild_audio.py -o rebuilt.wav \
  --block "<master>" 0 364.553 \
  --block "<clean_source>" 0 684.220 \
  --block "<master>" 1048.773 1068.810 \
  --target-duration 1068.810 --pad-at 1
```

### 3. Normalise and remux

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/audio_fix.py "<video>" [--audio rebuilt.wav] -o "<out.mp4>"
```

Two-pass loudnorm plus a safety limiter, `-c:v copy` so the picture is untouched.
Targets ~0.5 dB below the ceiling because AAC encoding pushes the peak back up.

### 4. Verify the render, not the intent

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/audio_report.py "<out.mp4>"          # expect verdict OK
python3 ${CLAUDE_SKILL_DIR}/scripts/check_sync.py "<original>" "<out.mp4>"  # expect OK, drift near 0
```

If blocks were spliced, also transcribe each junction and confirm no word was clipped:

```bash
ffmpeg -ss <junction-6> -t 12 -i "<out.mp4>" -vn -ac 1 -ar 16000 /tmp/j.wav -y
whisper-cli -m "${WHISPER_MODEL:-$HOME/Models/whisper/ggml-large-v3-turbo.bin}" -l fr -nt -np /tmp/j.wav
```

An editor's own transcript is not proof: two ASR passes of the same audio differ by
dozens of words. Only the rendered file counts.

## References

- `references/diagnosis.md`: reading the numbers, distinguishing a gain from a
  compressor from an added element, envelope correlation, why raw sample correlation
  fails after re-encoding.
- `references/gotchas.md`: AAC decoding short, peaks rising through the encoder,
  padding placement, Palmier's lack of loudnorm, disk and runtime costs.

## Scope

Handles levels, clipping, consistency, and delivery format. Does **not** do noise
reduction, EQ, de-essing, or music ducking. For those, use Palmier's `denoise_audio`
or hand the file back for a proper mix.
