#!/usr/bin/env python3
"""Normalise a video's audio to YouTube targets without touching the picture.

Two-pass loudnorm (measure, then apply) plus a safety limiter, remuxed with
`-c:v copy` so the video stream is bit-identical to the source.

Usage:
    audio_fix.py <video> [-o out.mp4] [--audio replacement.wav] [--lufs -14] [--tp -1]

`--audio` swaps in an externally rebuilt track (see rebuild_audio.py) instead of
the source's own audio. The track must already match the video duration.

Note: normalising a clipped master lowers the level but keeps the distortion.
When a clean source of the damaged section still exists, rebuild first.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def need(binary):
    if not shutil.which(binary):
        sys.exit(f"error: {binary} not found in PATH")


def measure(src, lufs, tp, lra):
    """Pass 1: collect loudnorm's measurements for a linear second pass."""
    r = run(["ffmpeg", "-i", str(src), "-af",
             f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:print_format=json",
             "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        sys.exit("error: loudnorm measurement failed")
    return json.loads(m.group(0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("-o", "--output")
    ap.add_argument("--audio", help="external audio track to use instead of the source")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tp", type=float, default=-1.0)
    ap.add_argument("--lra", type=float, default=11.0)
    ap.add_argument("--bitrate", default="384k")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    need("ffmpeg")
    video = Path(args.video).expanduser()
    if not video.exists():
        sys.exit(f"error: not found: {video}")
    src_audio = Path(args.audio).expanduser() if args.audio else video
    if not src_audio.exists():
        sys.exit(f"error: not found: {src_audio}")

    out = Path(args.output).expanduser() if args.output else \
        video.with_name(f"{video.stem}_fixed{video.suffix}")
    if out.resolve() == video.resolve():
        sys.exit("error: refusing to overwrite the source in place; pass -o")

    # Aim ~0.5 dB below the final ceiling: AAC encoding pushes the peak back up.
    enc_tp = args.tp - 0.5
    limit = 10 ** (enc_tp / 20.0)

    print(f"measuring {src_audio.name} ...")
    m = measure(src_audio, args.lufs, enc_tp, args.lra)
    print(f"  in: {m['input_i']} LUFS, TP {m['input_tp']} dBFS, LRA {m['input_lra']}")

    af = (
        f"loudnorm=I={args.lufs}:TP={enc_tp}:LRA={args.lra}"
        f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
        f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
        f":offset={m['target_offset']}:linear=true,"
        f"alimiter=limit={limit:.4f}:attack=5:release=50:level=disabled"
    )

    cmd = ["ffmpeg", "-v", "warning", "-stats",
           "-i", str(video), "-i", str(src_audio),
           "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "copy", "-af", af,
           "-c:a", "aac", "-b:a", args.bitrate, "-ar", "48000",
           "-movflags", "+faststart", str(out), "-y"]
    if args.video == args.audio or not args.audio:
        cmd = ["ffmpeg", "-v", "warning", "-stats", "-i", str(video),
               "-map", "0:v:0", "-map", "0:a:0",
               "-c:v", "copy", "-af", af,
               "-c:a", "aac", "-b:a", args.bitrate, "-ar", "48000",
               "-movflags", "+faststart", str(out), "-y"]

    if args.dry_run:
        print(" ".join(cmd))
        return

    print(f"writing {out} (video stream copied, not re-encoded) ...")
    r = subprocess.run(cmd)
    if r.returncode:
        sys.exit("error: ffmpeg failed")
    print(f"done: {out}")
    print("verify with: audio_report.py " + str(out))


if __name__ == "__main__":
    main()
