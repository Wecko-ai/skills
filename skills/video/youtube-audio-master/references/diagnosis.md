# Reading the numbers

- [Targets](#targets)
- [Clipping vs a hot peak](#clipping-vs-a-hot-peak)
- [Level jumps between blocks](#level-jumps-between-blocks)
- [Finding the clean source](#finding-the-clean-source)
- [Gain, compressor, or added element](#gain-compressor-or-added-element)
- [Null test](#null-test)

## Targets

| Metric | Target | Why |
|---|---|---|
| Integrated | -14 LUFS | YouTube normalises here; louder gets attenuated |
| True peak | -1 dBTP | headroom for lossy codec overshoot |
| Sample rate | 48 kHz | 44.1 gets resampled |
| Bitrate | 384 kb/s stereo | YouTube's own recommendation |
| LRA | 3-11 LU | spoken content sits low; not a defect by itself |

Within ~1 LU of -14 is fine. Chasing exactness is pointless: YouTube re-encodes anyway.

## Clipping vs a hot peak

`Peak: 0.0 dBFS` alone means little. What matters is **how many samples sit at full
scale** and whether they form consecutive runs:

- isolated samples at ceiling: inaudible, ignore.
- runs of 10+ consecutive samples: flat-topped waveform, audible as harshness on
  transients (plosives, hand claps, door slams).
- thousands of clipped samples spread over minutes: the section was gain-staged too hot,
  and no amount of later normalisation undoes it.

`audio_report.py` reports `clipped_samples`, `longest_run_samples`, and the worst
timestamps. Clipping concentrated in one contiguous stretch of the video (and absent
elsewhere) is the signature of **one block** being processed differently, not of a bad
recording.

## Level jumps between blocks

The per-window profile exposes what an integrated number hides. A master assembled from
an intro, a tour, and a talk can average -14 while alternating between -17 and -10.

Interpreting `spread`:

- under 2 LU: consistent, nothing to do.
- 2-4 LU: noticeable on headphones at a section change.
- above 4 LU: an obvious volume step; viewers reach for the volume control.

Find the boundary by narrowing the window (`--window 10`) around the suspected jump.

## Finding the clean source

`find_source.py` correlates the **amplitude envelope**, deliberately.

Raw sample cross-correlation fails on re-encoded audio: lossy codecs preserve what is
heard, not sample phase. Measured on a real case where a block was an exact copy of an
earlier export, only louder:

| method | score |
|---|---|
| raw sample correlation | 0.004 (looks like noise) |
| envelope correlation | 0.812 (unambiguous) |

The envelope survives because loudness over time is preserved. Smooth `abs(signal)` over
~100 ms, decimate, then FFT-correlate.

Confirm a match by probing the offset at several points: a real match holds a constant
lag across the whole block. A lag that grows means different frame rates or a speed
change, and the block cannot be swapped in directly.

## Gain, compressor, or added element

Before replacing a block with a "clean" source, verify nothing was added on top:
background music, sound effects, a voiceover. Replacing would silently delete it.

Method: align the two, then compare levels **inside the speech gaps** of the clean
source (its quietest blocks) against the same moments in the master.

| observation | meaning | safe to replace? |
|---|---|---|
| gaps and speech differ by the same amount | flat gain | yes |
| gaps louder than speech by a few dB | compressor (upward gain on quiet parts) | yes |
| gaps much louder, uncorrelated | something was mixed in | **no** |

A compressor shows a monotonically decreasing gain as level rises. Real measurement from
a master that had been "loudened":

```
source level    gain applied
-60..-45 dB       +3.30 dB
-45..-35 dB       +3.03 dB
-35..-28 dB       +2.87 dB
-22..-16 dB       +2.89 dB
-16..-10 dB       +2.45 dB
-10..  0 dB       +1.69 dB     <- ceiling pushing back
```

## Null test

To prove block B is block A with gain applied: align precisely, then compute
`g = sum(a*b)/sum(b*b)` and subtract `a - g*b`.

- residual 20 dB or more below the signal, correlation above 0.99: same material.
  The residual is the clipping damage plus codec noise, which is exactly what gets
  removed by rebuilding.
- correlation below ~0.9: different takes or different edits. Do not swap.
