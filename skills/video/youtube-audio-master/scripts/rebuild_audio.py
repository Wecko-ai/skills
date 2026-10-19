#!/usr/bin/env python3
"""Rebuild a master's audio track from clean sources, block by block.

Use when part of a master is clipped but the untouched export of that section
still exists: replacing the block removes the distortion, whereas normalising
only lowers a damaged signal.

Usage:
    rebuild_audio.py -o rebuilt.wav \\
        --block <file> <start> <end> \\
        --block <file> <start> <end> ... \\
        [--target-duration 1068.810]

`start`/`end` are seconds INSIDE that source file. Blocks concatenate in the
order given. With --target-duration, any shortfall is padded with silence
(AAC tracks decode slightly short, which otherwise drifts the tail out of sync).
Place the pad in a real silence: use --pad-at to choose which junction absorbs it.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def need(binary):
    if not shutil.which(binary):
        sys.exit(f"error: {binary} not found in PATH")


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        sys.exit(f"error: cannot read duration of {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--block", nargs=3, action="append", required=True,
                    metavar=("FILE", "START", "END"))
    ap.add_argument("--target-duration", type=float)
    ap.add_argument("--pad-at", type=int, default=None,
                    help="insert the duration pad AFTER this block index "
                         "(0-based). Default: at the end.")
    ap.add_argument("--rate", type=int, default=48000)
    args = ap.parse_args()

    need("ffmpeg")
    need("ffprobe")
    out = Path(args.output).expanduser()

    with tempfile.TemporaryDirectory() as td:
        parts = []
        for i, (f, s, e) in enumerate(args.block):
            src = Path(f).expanduser()
            if not src.exists():
                sys.exit(f"error: not found: {src}")
            start, end = float(s), float(e)
            if end <= start:
                sys.exit(f"error: block {i}: end must be greater than start")
            part = Path(td) / f"part{i}.wav"
            cmd = ["ffmpeg", "-v", "error", "-ss", f"{start}",
                   "-t", f"{end - start}", "-i", str(src), "-vn",
                   "-ac", "2", "-ar", str(args.rate), "-c:a", "pcm_s24le",
                   str(part), "-y"]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode:
                sys.exit(f"error: extracting block {i}: {r.stderr.strip()[:200]}")
            got = duration(part)
            print(f"  block {i}: {src.name} [{start} -> {end}] = {got:.3f}s "
                  f"(asked {end - start:.3f}s)")
            parts.append(part)

        total = sum(duration(p) for p in parts)
        if args.target_duration:
            gap = args.target_duration - total
            if gap > 0.001:
                pad = Path(td) / "pad.wav"
                subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi",
                                "-i", f"anullsrc=r={args.rate}:cl=stereo",
                                "-t", f"{gap}", "-c:a", "pcm_s24le",
                                str(pad), "-y"], check=True,
                               capture_output=True)
                at = len(parts) if args.pad_at is None else args.pad_at + 1
                parts.insert(at, pad)
                print(f"  padding {gap * 1000:.1f} ms of silence at position {at}")
                print("  NOTE: verify this lands in a real silence, not mid-speech")
            elif gap < -0.001:
                print(f"  WARNING: blocks exceed target by {abs(gap) * 1000:.1f} ms")

        inputs = []
        for p in parts:
            inputs += ["-i", str(p)]
        streams = "".join(f"[{i}:a]" for i in range(len(parts)))
        cmd = (["ffmpeg", "-v", "error"] + inputs +
               ["-filter_complex", f"{streams}concat=n={len(parts)}:v=0:a=1[out]",
                "-map", "[out]", "-c:a", "pcm_s24le", str(out), "-y"])
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"error: concat failed: {r.stderr.strip()[:300]}")

    final = duration(out)
    print(f"\nwrote {out} ({final:.3f}s)")
    if args.target_duration:
        delta = (final - args.target_duration) * 1000
        print(f"target {args.target_duration:.3f}s, delta {delta:+.1f} ms")
    print("next: audio_fix.py <video> --audio " + str(out))


if __name__ == "__main__":
    main()
