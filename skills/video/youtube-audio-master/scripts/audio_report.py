#!/usr/bin/env python3
"""Audit the audio of a video master against YouTube delivery targets.

Reports integrated loudness, true peak, real clipping (sample count, not just the
meter), and the loudness profile over time so a level jump between two assembled
blocks is visible.

Usage:
    audio_report.py <video> [--json] [--window 60]

Exit code 0 always (this is a report, not a gate). Read `verdict` in the output.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

TARGET_I = -14.0        # YouTube normalises around here
TARGET_TP = -1.0        # true peak ceiling
MAX_BLOCK_SPREAD = 2.0  # LU between sections before it is audible as a jump


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def need(binary):
    if not shutil.which(binary):
        sys.exit(f"error: {binary} not found in PATH")


def probe(video):
    r = run(["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_name,sample_rate,channels,bit_rate",
             "-show_entries", "format=duration",
             "-of", "json", str(video)])
    if r.returncode:
        sys.exit(f"error: ffprobe failed: {r.stderr.strip()[:300]}")
    data = json.loads(r.stdout or "{}")
    streams = data.get("streams") or []
    if not streams:
        sys.exit("error: no audio stream found")
    s = streams[0]
    return {
        "codec": s.get("codec_name"),
        "sample_rate": int(s.get("sample_rate") or 0),
        "channels": int(s.get("channels") or 0),
        "bitrate_kbps": round(int(s.get("bit_rate") or 0) / 1000) or None,
        "duration": float((data.get("format") or {}).get("duration") or 0.0),
    }


def ebur128(video):
    r = run(["ffmpeg", "-nostats", "-i", str(video),
             "-filter_complex", "ebur128=peak=true", "-f", "null", "-"])
    txt = r.stderr
    # Parse only the trailing Summary block. The per-frame progress lines carry
    # the same labels and would otherwise win the match.
    if "Summary:" in txt:
        txt = txt.rsplit("Summary:", 1)[1]
    out = {}
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", txt)
    if m:
        out["integrated_lufs"] = float(m.group(1))
    m = re.search(r"LRA:\s+(-?[\d.]+) LU", txt)
    if m:
        out["lra"] = float(m.group(1))
    peaks = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", txt)
    if peaks:
        out["true_peak_dbfs"] = float(peaks[-1])
    return out


def decode_wav(video, tmpdir, sample_rate=48000):
    wav = Path(tmpdir) / "audio.wav"
    r = run(["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "2",
             "-ar", str(sample_rate), "-c:a", "pcm_s16le", str(wav), "-y"])
    if r.returncode:
        sys.exit(f"error: audio decode failed: {r.stderr.strip()[:300]}")
    return wav


def clipping(wav_path, window):
    """Count samples pinned at full scale. This is what a peak meter alone hides."""
    import numpy as np
    w = wave.open(str(wav_path))
    sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
    ceiling = 32700  # 16-bit full scale is 32767; allow for codec rounding
    per_window = {}
    total = 0
    longest_run = 0
    worst = []
    pos = 0
    block = sr * 10
    carry = 0        # run length carried across block boundaries
    carry_start = 0
    while pos < n:
        w.setpos(pos)
        a = np.frombuffer(w.readframes(min(block, n - pos)), dtype="<i2")
        a = a.reshape(-1, ch)
        hit = (np.abs(a.astype(np.int32)) >= ceiling).any(axis=1)
        if hit.any():
            idx = np.flatnonzero(hit)
            total += idx.size
            for i in idx:
                key = int((pos + i) / sr // window)
                per_window[key] = per_window.get(key, 0) + 1
            # Longest consecutive run = audible flat-top distortion. Runs can span
            # block boundaries, so carry an open run into the next iteration.
            splits = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
            for gi, g in enumerate(splits):
                size = int(g.size)
                start = pos + int(g[0])
                if gi == 0 and carry and int(g[0]) == 0:
                    size += carry
                    start = carry_start
                is_last = gi == len(splits) - 1
                touches_end = int(g[-1]) == a.shape[0] - 1
                if is_last and touches_end:
                    carry, carry_start = size, start
                    continue
                carry = 0
                longest_run = max(longest_run, size)
                if size >= 20:
                    worst.append((start / sr, size))
        else:
            if carry:
                longest_run = max(longest_run, carry)
                if carry >= 20:
                    worst.append((carry_start / sr, carry))
                carry = 0
        pos += block
    if carry:
        longest_run = max(longest_run, carry)
        if carry >= 20:
            worst.append((carry_start / sr, carry))
    w.close()
    worst.sort(key=lambda x: -x[1])
    return {
        "clipped_samples": int(total),
        "longest_run_samples": longest_run,
        "per_window": {str(k): v for k, v in sorted(per_window.items())},
        "worst_spots": [{"t": round(t, 2), "tc": f"{int(t)//60}:{int(t)%60:02d}",
                         "samples": c} for t, c in worst[:15]],
    }


def loudness_profile(video, window):
    """Momentary loudness per window, gated to speech-level audio."""
    import numpy as np
    with tempfile.TemporaryDirectory() as td:
        meta = Path(td) / "m.txt"
        run(["ffmpeg", "-nostats", "-v", "warning", "-i", str(video),
             "-af", f"ebur128=metadata=1,ametadata=print:key=lavfi.r128.M:file={meta}",
             "-f", "null", "-"])
        if not meta.exists():
            return []
        times, vals, t = [], [], None
        for line in meta.read_text(errors="ignore").splitlines():
            line = line.strip()
            m = re.match(r"frame:\d+\s+pts:\d+\s+pts_time:([\d.]+)", line)
            if m:
                t = float(m.group(1))
                continue
            m = re.match(r"lavfi\.r128\.M=(-?[\d.]+|-?inf|nan)", line)
            if m and t is not None:
                try:
                    v = float(m.group(1))
                except ValueError:
                    v = -70.0
                times.append(t)
                vals.append(v)
    if not times:
        return []
    t = np.array(times)
    v = np.nan_to_num(np.array(vals), neginf=-70.0, posinf=-70.0)
    out = []
    end = float(t[-1])
    start = 0.0
    while start < end:
        seg = v[(t >= start) & (t < start + window)]
        seg = seg[seg > -40]           # gate out silence/room tone
        if seg.size > 3:
            mean = 10 * np.log10((10 ** (seg / 10.0)).mean())
            out.append({"t": start,
                        "tc": f"{int(start)//60}:{int(start)%60:02d}",
                        "lufs": round(float(mean), 1)})
        start += window
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--window", type=float, default=60.0,
                    help="profile window in seconds (default 60)")
    args = ap.parse_args()

    need("ffmpeg")
    need("ffprobe")
    try:
        import numpy  # noqa: F401
    except ImportError:
        sys.exit("error: numpy required (pip3 install numpy)")

    video = Path(args.video).expanduser()
    if not video.exists():
        sys.exit(f"error: not found: {video}")

    stream = probe(video)
    loud = ebur128(video)
    profile = loudness_profile(video, args.window)
    with tempfile.TemporaryDirectory() as td:
        clip = clipping(decode_wav(video, td), args.window)

    issues = []
    i_lufs = loud.get("integrated_lufs")
    if i_lufs is not None and abs(i_lufs - TARGET_I) > 1.0:
        direction = "too loud" if i_lufs > TARGET_I else "too quiet"
        issues.append(f"loudness {i_lufs} LUFS ({direction}, target {TARGET_I})")
    tp = loud.get("true_peak_dbfs")
    if tp is not None and tp > TARGET_TP:
        issues.append(f"true peak {tp} dBFS above {TARGET_TP} ceiling")
    if clip["clipped_samples"] > 0:
        issues.append(f"{clip['clipped_samples']} clipped samples "
                      f"(longest flat run {clip['longest_run_samples']})")
    if stream["sample_rate"] and stream["sample_rate"] != 48000:
        issues.append(f"sample rate {stream['sample_rate']} Hz (YouTube prefers 48000)")
    spread = None
    if len(profile) >= 2:
        lo = min(p["lufs"] for p in profile)
        hi = max(p["lufs"] for p in profile)
        spread = round(hi - lo, 1)
        if spread > MAX_BLOCK_SPREAD:
            issues.append(f"level spread {spread} LU across the video "
                          f"(audible jump; check assembled blocks)")

    report = {
        "file": str(video),
        "stream": stream,
        "loudness": loud,
        "clipping": clip,
        "profile": profile,
        "level_spread_lu": spread,
        "issues": issues,
        "verdict": "OK" if not issues else "NEEDS WORK",
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(f"file      : {video.name}")
    print(f"duration  : {stream['duration']:.1f}s   audio: {stream['codec']} "
          f"{stream['sample_rate']}Hz {stream['channels']}ch "
          f"{stream['bitrate_kbps'] or '?'}kb/s")
    print(f"loudness  : {i_lufs} LUFS   (target {TARGET_I})")
    print(f"true peak : {tp} dBFS   (ceiling {TARGET_TP})")
    print(f"LRA       : {loud.get('lra')} LU")
    print(f"clipping  : {clip['clipped_samples']} samples, "
          f"longest run {clip['longest_run_samples']}")
    if clip["worst_spots"]:
        spots = ", ".join(f"{s['tc']}({s['samples']})" for s in clip["worst_spots"][:6])
        print(f"worst     : {spots}")
    if spread is not None:
        print(f"spread    : {spread} LU between loudest and quietest window")
    if profile:
        print("\nprofile (gated, per window):")
        for p in profile:
            bar = "#" * max(0, int((p["lufs"] + 30)))
            print(f"  {p['tc']:>6}  {p['lufs']:>6.1f} LUFS  {bar}")
    print(f"\nverdict   : {report['verdict']}")
    for i in issues:
        print(f"  - {i}")


if __name__ == "__main__":
    main()
