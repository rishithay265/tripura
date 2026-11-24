#!/usr/bin/env python3
"""Slice YouTube storyboard sprite sheets into per-frame samples and measure
visual change across the whole video.

Storyboard L3 for this video: 3x3 tiles of 320x180, 64 sheets, 575 frames,
interval 10 s -> one sample every 10 s over the whole runtime.

Outputs (all under <out>):
  storyboard_frames/f_XXXX.jpg      every sampled frame (320x180)
  storyboard_frames.csv             timestamp, change score, colour stats
  visual_segments.csv               runs of visually-static vs changing material
  contact_storyboard.jpg            montage of 48 evenly spaced frames
"""
import csv
import glob
import os
import re
import sys

import numpy as np
from PIL import Image

# region of interest: exclude the burned-in lower-third/ADVT bars
ROI_TOP = 0.00
ROI_BOT = 0.74


def load_sheets(sheet_dir):
    files = sorted(glob.glob(os.path.join(sheet_dir, "M*.jpg")),
                   key=lambda p: int(re.search(r"M(\d+)", os.path.basename(p)).group(1)))
    return files


def main():
    sheet_dir, out = sys.argv[1], sys.argv[2]
    interval_ms = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
    os.makedirs(os.path.join(out, "storyboard_frames"), exist_ok=True)
    sheets = load_sheets(sheet_dir)
    print("sheets:", len(sheets))

    frames = []  # (idx, np.array float, Image)
    for si, path in enumerate(sheets):
        im = Image.open(path).convert("RGB")
        W, H = im.size
        # 3x3 grid
        gw, gh = 3, 3
        tw, th = W // gw, H // gh
        for r in range(gh):
            for c in range(gw):
                idx = si * (gw * gh) + r * gw + c
                tile = im.crop((c * tw, r * th, (c + 1) * tw, (r + 1) * th))
                frames.append((idx, tile))
    print("frames:", len(frames))

    rows = []
    prev = None
    for idx, tile in frames:
        a = np.asarray(tile).astype(np.float32) / 255.0
        h = a.shape[0]
        roi = a[int(ROI_TOP * h):int(ROI_BOT * h)]
        g = (0.2126 * roi[..., 0] + 0.7152 * roi[..., 1] + 0.0722 * roi[..., 2])
        t_ms = idx * interval_ms
        # colour stats over ROI
        mx = roi.max(2); mn = roi.min(2)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        diff = float(np.abs(g - prev).mean()) if prev is not None else 0.0
        rows.append({
            "frame": idx,
            "t_s": round(t_ms / 1000, 1),
            "t_hms": "%d:%02d:%02d" % (t_ms // 3600000, (t_ms // 60000) % 60, (t_ms // 1000) % 60),
            "diff_prev": round(diff, 4),
            "mean_luma": round(float(g.mean()), 4),
            "std_luma": round(float(g.std()), 4),
            "mean_sat": round(float(sat.mean()), 4),
        })
        prev = g
        tile.save(os.path.join(out, "storyboard_frames", "f_%04d.jpg" % idx), quality=88)

    with open(os.path.join(out, "storyboard_frames.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # visual segments: a "cut" is a change far above the local baseline
    diffs = np.array([r["diff_prev"] for r in rows])
    base = np.median(diffs[1:]) if len(diffs) > 1 else 0
    thr = max(base * 4, 0.012)
    cuts = [i for i in range(1, len(rows)) if diffs[i] > thr]
    segs = []
    bounds = [0] + cuts + [len(rows) - 1]
    for k in range(len(bounds) - 1):
        a, b = bounds[k], bounds[k + 1]
        if b <= a:
            continue
        seg = rows[a:b + 1]
        segs.append({
            "shot": k + 1,
            "start_s": seg[0]["t_s"],
            "end_s": seg[-1]["t_s"],
            "dur_s": round(seg[-1]["t_s"] - seg[0]["t_s"], 1),
            "mean_luma": round(float(np.mean([s["mean_luma"] for s in seg])), 3),
            "mean_sat": round(float(np.mean([s["mean_sat"] for s in seg])), 3),
            "internal_change": round(float(np.mean([s["diff_prev"] for s in seg[1:]]) if len(seg) > 1 else 0), 4),
            "start_hms": seg[0]["t_hms"],
            "end_hms": seg[-1]["t_hms"],
        })
    with open(os.path.join(out, "visual_segments.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(segs[0].keys()))
        w.writeheader(); w.writerows(segs)

    # contact sheet of 48 evenly spaced frames with timestamps burned in
    from PIL import ImageDraw
    step = max(len(frames) // 48, 1)
    picks = frames[::step][:48]
    cols, rowsn = 8, 6
    cell_w, cell_h = 240, 135
    sheet = Image.new("RGB", (cols * cell_w, rowsn * (cell_h + 14)), (18, 18, 18))
    d = ImageDraw.Draw(sheet)
    for i, (idx, tile) in enumerate(picks):
        x = (i % cols) * cell_w
        y = (i // cols) * (cell_h + 14)
        sheet.paste(tile.resize((cell_w, cell_h)), (x, y))
        t = idx * interval_ms // 1000
        d.text((x + 4, y + cell_h + 1), "%d:%02d:%02d" % (t // 3600, (t // 60) % 60, t % 60),
               fill=(255, 220, 120))
    sheet.save(os.path.join(out, "contact_storyboard.jpg"), quality=90)

    print("cuts detected:", len(cuts), "threshold:", round(thr, 4), "baseline:", round(float(base), 5))
    print("segments:", len(segs))
    for s in segs[:40]:
        print(s)


if __name__ == "__main__":
    main()
