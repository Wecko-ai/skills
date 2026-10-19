#!/usr/bin/env python3
"""Verify a reworked video still lines up with the original, across its length.

Replacing an audio track can shift it or let it drift. This probes N points and
reports the offset at each, so drift shows up as a growing lag rather than a
constant one.

Usage:
    check_sync.py <reference> <candidate> [--probes 10] [--tolerance 0.04]

Tolerance defaults to 40 ms, the usual threshold for noticing lip-sync error.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

SR = 16000


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


def grab(path, ss, dur, out):
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur),
                        "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR),
                        str(out), "-y"], capture_output=True, text=True)
    if r.returncode:
        return None
    w = wave.open(str(out))
    a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float)
    w.close()
    return a if a.size else None


def lag(a, b, span=2.0):
    import numpy as np
    from numpy.fft import rfft, irfft

    def env(x, win=160):
        return np.convolve(np.abs(x), np.ones(win) / win, mode="same")

    A, B = env(a), env(b)
    A = A - A.mean()
    B = B - B.mean()
    n = 1 << int(np.ceil(np.log2(len(A) + len(B))))
    c = irfft(rfft(A, n) * np.conj(rfft(B, n)), n)
    k = int(SR * span)
    c = np.concatenate([c[-k:], c[:k]])
    i = int(np.argmax(c)) - k
    denom = np.linalg.norm(A) * np.linalg.norm(B)
    return i / SR, float(c.max() / denom) if denom else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("candidate")
    ap.add_argument("--probes", type=int, default=10)
    ap.add_argument("--tolerance", type=float, default=0.04)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    need("ffmpeg")
    need("ffprobe")
    try:
        import numpy  # noqa: F401
    except ImportError:
        sys.exit("error: numpy required (pip3 install numpy)")

    ref = Path(args.reference).expanduser()
    cand = Path(args.candidate).expanduser()
    for p in (ref, cand):
        if not p.exists():
            sys.exit(f"error: not found: {p}")

    dur = min(duration(ref), duration(cand))
    step = dur / (args.probes + 1)
    rows = []
    with tempfile.TemporaryDirectory() as td:
        for i in range(1, args.probes + 1):
            t = round(step * i, 2)
            a = grab(cand, t, 10, Path(td) / "a.wav")
            b = grab(ref, t, 10, Path(td) / "b.wav")
            if a is None or b is None:
                continue
            l, score = lag(a, b)
            rows.append({"t": t, "tc": f"{int(t)//60}:{int(t)%60:02d}",
                         "lag_s": round(l, 4), "corr": round(score, 3),
                         "ok": abs(l) <= args.tolerance})

    worst = max((abs(r["lag_s"]) for r in rows), default=0.0)
    drift = (max((r["lag_s"] for r in rows), default=0.0) -
             min((r["lag_s"] for r in rows), default=0.0))
    verdict = "OK" if all(r["ok"] for r in rows) and rows else "OUT OF SYNC"

    if args.json:
        print(json.dumps({"probes": rows, "worst_abs_lag_s": round(worst, 4),
                          "drift_s": round(drift, 4), "verdict": verdict}, indent=2))
        return

    print(f"reference : {ref.name}")
    print(f"candidate : {cand.name}\n")
    for r in rows:
        flag = "ok" if r["ok"] else "OFF"
        print(f"  {r['tc']:>7}  lag {r['lag_s']:+.3f}s  corr {r['corr']:.3f}  {flag}")
    print(f"\nworst {worst * 1000:.0f} ms, drift {drift * 1000:.0f} ms "
          f"(tolerance {args.tolerance * 1000:.0f} ms)")
    print(f"verdict: {verdict}")
    if verdict != "OK":
        sys.exit(1)


if __name__ == "__main__":
    main()
