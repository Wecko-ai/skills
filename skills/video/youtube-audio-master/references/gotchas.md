# Gotchas

Measured, not inferred.

- [AAC decodes short](#aac-decodes-short)
- [Peaks rise through the encoder](#peaks-rise-through-the-encoder)
- [Where to put the padding](#where-to-put-the-padding)
- [ffmpeg parsing traps](#ffmpeg-parsing-traps)
- [Palmier Pro](#palmier-pro)
- [Cost and runtime](#cost-and-runtime)

## AAC decodes short

An AAC track decodes slightly shorter than its container duration. A block asked to be
684.220 s came back as 684.134 s (**86 ms lost**). Concatenating several blocks
accumulates the error and drifts the tail out of sync.

Always pass `--target-duration` to `rebuild_audio.py`; it pads the difference. Verify the
result with `check_sync.py` rather than trusting the arithmetic.

## Peaks rise through the encoder

Normalising to exactly -1.0 dBTP then encoding to AAC yields a file measuring **above**
-1.0. Lossy encoding reconstructs a slightly different waveform.

`audio_fix.py` targets 0.5 dB below the requested ceiling and adds a limiter. Measured:
ask -1.5 before encoding, get -1.0 after. Verify on the final file, never on the
intermediate WAV.

## Where to put the padding

Silence inserted to correct duration must land in **actual silence**. Both junctions of a
typical talking-head edit fall mid-sentence, where 86 ms of silence is an audible glitch.

Find a real gap first (scan RMS in 100 ms slices around the junctions, look for
something below -50 dBFS) and use `--pad-at` to choose which junction absorbs it.

## ffmpeg parsing traps

- **ebur128 summary**: per-frame progress lines carry the same `I:` / `LRA:` / `Peak:`
  labels as the final summary. A naive regex matches a progress line and returns
  nonsense (-70 LUFS). Split on `Summary:` and parse only what follows.
- **`-nostats` is not enough**: `-v warning` still emits the ebur128 summary on stderr;
  `-v error` suppresses it. Use `-nostats` with default verbosity to get the summary
  without the progress spam.
- **Blockwise sample scans**: a run of clipped samples can straddle a read boundary.
  Carry an open run across iterations or the longest run gets undercounted.

## Palmier Pro

- The MCP server only answers when the app is running (`open -a PalmierPro`, ~2 s).
- **No loudnorm exposed.** Normalisation stays an ffmpeg pass after export.
- The canvas caps the export: `export_project resolution=4K` on a 1080p canvas only
  upscales. Set `set_project_settings` width/height first.
- Importing media sets the canvas from the *first* asset imported.

## Cost and runtime

For an 18-minute 4K master (3.3 GB):

| step | time |
|---|---|
| `audio_report.py` | ~2 min (decode + two analysis passes) |
| `find_source.py`, 4 candidates | ~10 s (8 kHz envelopes) |
| `rebuild_audio.py` | ~5 s |
| `audio_fix.py` (remux) | ~50 s |
| `check_sync.py` | ~3 s |

Remuxing writes a full copy: keep free space above the source size. The source is never
modified: `audio_fix.py` refuses to overwrite it in place.
