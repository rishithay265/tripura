#!/usr/bin/env python3
"""Normalise YouTube subtitle files (json3 / vtt / srv*) into analysis CSVs.

Outputs:
  <out>/caption_words.csv   one row per timed word/segment
  <out>/caption_lines.csv   one row per caption event (line-level)
"""
import csv
import json
import os
import re
import sys


def ts_from_json3(events, out_words, out_lines):
    for ev in events:
        segs = ev.get("segs")
        if not segs:
            continue
        start = ev.get("tStartMs", 0) / 1000.0
        dur = ev.get("dDurationMs", 0) / 1000.0
        text = "".join(s.get("utf8", "") for s in segs).replace("\n", " ").strip()
        if not text:
            continue
        out_lines.append(
            {
                "start_s": round(start, 2),
                "end_s": round(start + dur, 2),
                "duration_s": round(dur, 2),
                "text": text,
            }
        )
        for s in segs:
            w = s.get("utf8", "").replace("\n", " ").strip()
            if not w:
                continue
            wstart = start + s.get("tOffsetMs", 0) / 1000.0
            wdur = 0.0
            if "dDurationMs" in s:
                wdur = s["dDurationMs"] / 1000.0
            out_words.append(
                {
                    "start_s": round(wstart, 2),
                    "end_s": round(wstart + wdur, 2),
                    "word": w,
                }
            )
    return out_words, out_lines


def ts_from_vtt(path, out_words, out_lines):
    def conv(t):
        parts = t.split(":")
        parts = [float(p) for p in parts]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return parts[0] * 60 + parts[1]

    cur = None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if "-->" in line:
            a, b = line.split("-->")[:2]
            cur = (conv(a.strip().replace(",", ".")), conv(b.strip().split()[0].replace(",", ".")))
        elif line.startswith("<") and cur:
            words = [w for w in re.split(r"\s+", re.sub(r"<[^>]+>", "", line)) if w]
            n = max(len(words), 1)
            step = (cur[1] - cur[0]) / n
            out_lines.append(
                {
                    "start_s": round(cur[0], 2),
                    "end_s": round(cur[1], 2),
                    "duration_s": round(cur[1] - cur[0], 2),
                    "text": " ".join(words),
                }
            )
            for i, w in enumerate(words):
                out_words.append(
                    {
                        "start_s": round(cur[0] + i * step, 2),
                        "end_s": round(cur[0] + (i + 1) * step, 2),
                        "word": w,
                    }
                )
            cur = None


def main():
    raw, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    words, lines = [], []
    for fn in sorted(os.listdir(raw)):
        p = os.path.join(raw, fn)
        if fn.endswith(".json3"):
            data = json.load(open(p, encoding="utf-8"))
            ts_from_json3(data.get("events", []), words, lines)
        elif fn.endswith(".vtt"):
            ts_from_vtt(p, words, lines)
    words.sort(key=lambda r: r["start_s"])
    lines.sort(key=lambda r: r["start_s"])
    with open(os.path.join(out, "caption_words.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["start_s", "end_s", "word"])
        w.writeheader()
        w.writerows(words)
    with open(os.path.join(out, "caption_lines.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["start_s", "end_s", "duration_s", "text"])
        w.writeheader()
        w.writerows(lines)
    print(f"words={len(words)} lines={len(lines)}")
    if lines:
        print(f"span={lines[0]['start_s']}..{lines[-1]['end_s']}")


if __name__ == "__main__":
    main()
