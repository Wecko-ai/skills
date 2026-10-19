#!/usr/bin/env python3
"""Locate where a candidate clip sits inside a longer master, by audio.

Answers "which export did this section come from, and at what offset?" so a
damaged block can be replaced with its clean original instead of being patched.

Usage:
    find_source.py <master> <candidate> [<candidate> ...] [--json]

Correlates the amplitude ENVELOPE, not raw samples: re-encoding (AAC) destroys
sample phase, so raw cross-correlation returns noise (~0.004) even for an exact
match, while envelope correlation still peaks cleanly (~0.8).

A score above ~0.5 is a confident match. Verify sync afterwards with
check_sync.py before trusting it.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

ENV_SR = 8000      # envelope analysis rate
ENV_WIN = 800      # smoothing window in samples
DECIM = 80         # decimation after smoothing


def need(binary):
    if not shutil.which(binary):
        sys.exit(f"error: {binary} not found in PATH")


def envelope(path, tmpdir, name):
    import numpy as np
    wav = Path(tmpdir) / f"{name}.wav"
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn",
                        "-ac", "1", "-ar", str(ENV_SR), str(wav), "-y"],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"error: decode failed for {path}: {r.stderr.strip()[:200]}")
    w = wave.open(str(wav))
    a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float)
    w.close()
    env = np.convolve(np.abs(a), np.ones(ENV_WIN) / ENV_WIN, mode="same")[::DECIM]
    return env, ENV_SR / DECIM


def locate(master_env, cand_env, esr):
    import numpy as np
    from numpy.fft import rfft, irfft
    A = master_env - master_env.mean()
    B = cand_env - cand_env.mean()
    n = 1 << int(np.ceil(np.log2(len(A) + len(B))))
    c = irfft(rfft(A, n) * np.conj(rfft(B, n)), n)
    usable = c[:max(1, len(A))]
    i = int(np.argmax(usable))
    denom = np.linalg.norm(A) * np.linalg.norm(B)
    score = float(usable[i] / denom) if denom else 0.0
    return i / esr, score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("master")
    ap.add_argument("candidates", nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    need("ffmpeg")
    try:
        import numpy  # noqa: F401
    except ImportError:
        sys.exit("error: numpy required (pip3 install numpy)")

    master = Path(args.master).expanduser()
    if not master.exists():
        sys.exit(f"error: not found: {master}")

    results = []
    with tempfile.TemporaryDirectory() as td:
        m_env, esr = envelope(master, td, "master")
        for idx, cand in enumerate(args.candidates):
            p = Path(cand).expanduser()
            if not p.exists():
                results.append({"candidate": str(p), "error": "not found"})
                continue
            c_env, _ = envelope(p, td, f"cand{idx}")
            offset, score = locate(m_env, c_env, esr)
            results.append({
                "candidate": str(p),
                "name": p.name,
                "offset_s": round(offset, 3),
                "offset_tc": f"{int(offset)//60}:{int(offset)%60:02d}",
                "length_s": round(len(c_env) / esr, 2),
                "score": round(score, 3),
                "match": score >= 0.5,
            })

    if args.json:
        print(json.dumps({"master": str(master), "results": results}, indent=2))
        return

    print(f"master: {master.name}\n")
    for r in sorted(results, key=lambda x: -x.get("score", 0)):
        if "error" in r:
            print(f"  {r['candidate']}: {r['error']}")
            continue
        mark = "MATCH" if r["match"] else "  -  "
        print(f"  [{mark}] {r['name']:<34} offset {r['offset_tc']:>7} "
              f"({r['offset_s']:>9.3f}s)  len {r['length_s']:>8.2f}s  score {r['score']:.3f}")
    print("\nscore >= 0.5 = confident. Confirm with check_sync.py before replacing.")


if __name__ == "__main__":
    main()
