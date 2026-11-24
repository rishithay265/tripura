#!/usr/bin/env python3
"""Measured audio analysis for the research report.

Everything emitted here is a *measurement* on the decoded waveform, not an
opinion. Input: mono 16 kHz PCM wav. Output: CSVs + a summary txt.

Produces
  audio_rms_1s.csv        per-second RMS dBFS, peak, spectral centroid proxy
  audio_pauses.csv        silence runs (voiced/unvoiced segmentation)
  audio_blocks_30s.csv    30 s windows: speech ratio, mean level, dynamics
  audio_summary.txt       human-readable summary
"""
import csv
import os
import sys

import numpy as np


def read_wav(path):
    import wave

    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        raw = w.readframes(n)
    if sw == 2:
        x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    else:
        x = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2**31
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def db(v):
    return 20 * np.log10(max(v, 1e-9))


def main():
    wav, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    x, sr = read_wav(wav)
    dur = len(x) / sr
    win = int(sr * 0.02)  # 20 ms frames
    nfr = len(x) // win
    fr = x[: nfr * win].reshape(nfr, win)
    rms = np.sqrt((fr**2).mean(axis=1) + 1e-12)
    rdb = 20 * np.log10(rms + 1e-9)
    zcr = (np.abs(np.diff(np.signbit(fr).astype(np.int8), axis=1)) > 0).mean(axis=1)
    # spectral flatness per frame (music vs speech heuristic)
    spec = np.abs(np.fft.rfft(fr * np.hanning(win), axis=1)) + 1e-12
    flat = np.exp(np.log(spec).mean(axis=1)) / spec.mean(axis=1)
    centroid = (spec * np.arange(spec.shape[1])).sum(axis=1) / spec.sum(axis=1)
    centroid_hz = centroid * (sr / 2) / (spec.shape[1] - 1)

    # adaptive voice threshold: bottom decile of loud frames is room tone
    loud_ref = np.percentile(rdb, 90)
    thr = max(loud_ref - 32, -52)
    voiced = rdb > thr

    # per-second table
    per = int(1 / 0.02)
    secs = []
    for i in range(0, nfr // per):
        sl = slice(i * per, (i + 1) * per)
        secs.append(
            {
                "t_s": i,
                "rms_db": round(float(rdb[sl].mean()), 2),
                "peak_db": round(float(rdb[sl].max()), 2),
                "voiced_frac": round(float(voiced[sl].mean()), 3),
                "zcr": round(float(zcr[sl].mean()), 4),
                "flatness": round(float(flat[sl].mean()), 4),
                "centroid_hz": round(float(centroid_hz[sl].mean()), 1),
            }
        )
    with open(os.path.join(out, "audio_rms_1s.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(secs[0].keys()))
        w.writeheader()
        w.writerows(secs)

    # pause runs
    pauses = []
    i = 0
    while i < nfr:
        if not voiced[i]:
            j = i
            while j < nfr and not voiced[j]:
                j += 1
            d = (j - i) * 0.02
            if d >= 0.30:
                pauses.append(
                    {
                        "start_s": round(i * 0.02, 2),
                        "end_s": round(j * 0.02, 2),
                        "duration_s": round(d, 2),
                        "level_db": round(float(rdb[i:j].mean()), 1),
                    }
                )
            i = j
        else:
            i += 1
    with open(os.path.join(out, "audio_pauses.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["start_s", "end_s", "duration_s", "level_db"])
        w.writeheader()
        w.writerows(pauses)

    # 30 s blocks
    blocks = []
    for b in range(0, int(np.ceil(dur / 30))):
        a, z = int(b * 30 / 0.02), int((b + 1) * 30 / 0.02)
        if a >= nfr:
            break
        sl = slice(a, min(z, nfr))
        blocks.append(
            {
                "block_s": b * 30,
                "speech_ratio": round(float(voiced[sl].mean()), 3),
                "mean_db": round(float(rdb[sl].mean()), 2),
                "dyn_range_db": round(float(np.percentile(rdb[sl], 95) - np.percentile(rdb[sl], 10)), 1),
                "flatness": round(float(flat[sl].mean()), 4),
                "centroid_hz": round(float(centroid_hz[sl].mean()), 1),
            }
        )
    with open(os.path.join(out, "audio_blocks_30s.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(blocks[0].keys()))
        w.writeheader()
        w.writerows(blocks)

    pd = np.array([p["duration_s"] for p in pauses]) if pauses else np.array([0.0])
    lines = [
        "AUDIO MEASUREMENTS (mono 16 kHz decode of the published audio track)",
        f"duration_s            : {dur:.2f}",
        f"framing               : 20 ms RMS windows, {nfr} frames",
        f"voice threshold (dBFS): {thr:.1f}  (90th pct loudness {loud_ref:.1f} dBFS - 32 dB)",
        f"speech/voiced ratio   : {voiced.mean()*100:.1f}%",
        f"mean level (voiced)   : {rdb[voiced].mean():.1f} dBFS",
        f"mean level (unvoiced) : {rdb[~voiced].mean() if (~voiced).any() else float('nan'):.1f} dBFS",
        f"overall peak          : {rdb.max():.1f} dBFS (20 ms window RMS)",
        f"sample peak           : {db(np.abs(x).max()):.1f} dBFS",
        f"pause runs >=0.30 s   : {len(pauses)}",
        f"pause total (s)       : {pd.sum():.1f}  ({pd.sum()/dur*100:.1f}% of runtime)",
        f"pause mean / median   : {pd.mean():.2f} / {np.median(pd):.2f} s",
        f"pause p90 / max       : {np.percentile(pd,90):.2f} / {pd.max():.2f} s",
        f"pauses >2 s count     : {int((pd>2).sum())}",
        f"mean flatness (spec)  : {flat.mean():.4f}  (tonal/music-ish frames scored lower)",
        f"mean centroid         : {centroid_hz.mean():.0f} Hz",
        f"clipped samples       : {int((np.abs(x)>0.999).sum())}",
    ]
    txt = "\n".join(lines)
    open(os.path.join(out, "audio_summary.txt"), "w").write(txt + "\n")
    print(txt)
    print("\nfirst 15 pauses:")
    for p in pauses[:15]:
        print(p)


if __name__ == "__main__":
    main()
