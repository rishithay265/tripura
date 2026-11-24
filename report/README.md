# Research Package — `Lord Shiva v/s Tripurasura War` (Eha Bhakthi, `uKpiTI20mP8`)

A complete investigative package on one YouTube video: verified metadata, a measured 10-second-resolution
visual timeline of the full 95:32 runtime, a bilingual annotated transcript of the key passages, a
retention-technique map, and a production blueprint built for TheGodmanFiles.

**Start here → [`REPORT.md`](REPORT.md)**

---

## What is in this package

| Path | What it is |
|---|---|
| `REPORT.md` | The consolidated report: executive findings, metadata, timeline, visual/editing/audio analysis, retention map, production reconstruction, packaging critique, verification, and the TheGodmanFiles blueprint + SOP + prompt framework + QC checklist |
| `data/video_metadata.csv` | Every metadata field, with its source and a status flag (`verified` / `calculated` / `unknown`) |
| `data/shot_inventory_10s.csv` | 576 rows, one per 10 s of runtime: timecode, visual cluster, asset name, class, change score, luminance, saturation |
| `data/editing_timeline.csv` | 526 runs: every contiguous hold, with start/end/duration/asset/class |
| `data/visual_library.csv` | The 27 visual assets ranked by screen time, with first/last appearance |
| `data/retention_technique_map.csv` | 20 techniques with location, evidence, mechanism and evidence type (plus 2 anti-retention observations) |
| `data/transcript_excerpts_te_en.csv` | 33 annotated Telugu lines — original, English translation, and each line's function in the script architecture |
| `assets/contact_sheet_full_video_48.jpg` | 48 timestamped frames spread across the whole video |
| `assets/visual_library_exemplars.jpg` | One labelled exemplar per visual asset with its measured screen time |
| `assets/key_frames_16.jpg` | 16 frames at analytically interesting positions |
| `assets/thumbnail_official_1280x720.jpg` | The packaging artefact analysed in §10 |
| `assets/invideo_25pct_*.jpg`, `…50pct_*.jpg`, `…75pct_*.jpg` | Full-resolution in-video frames that prove the still-photo/Ken-Burns finding |

`../evidence/` holds the raw captures (576 sliced storyboard frames, page HTML, endpoint logs).

---

## The three-sentence summary

The video is a **re-cut of a Telugu TV broadcast**: a 95-minute extempore discourse by Chaganti Koteswara Rao
laid over a **fixed-rotation slideshow of 23 still images** changing on a ~10-second grid, with an ad ticker
and station promos burned into the pixels. Its power is **entirely in the narration** — a single paradox posed
in the first 90 seconds (*why is Shiva "Tripurantaka" when his wife is "Tripurasundari"?*) and answered only
at 1:26, when the war is relocated from a battlefield to the devotee's own equilibrium. The production is
minimal, the packaging over-promises spectacle, and the **copyable asset is the script architecture**, not the edit.

---

## Honesty notes (read before quoting anything)

This environment could not reach YouTube's media servers, so:

- **No audio was analysed.** No loudness, music, silence map, speaking rate or voice measurements appear in
  this package. §7.2 lists each missing measurement.
- **Shot boundaries are quantised to 10 s** because the only obtainable frame source (storyboard) samples at
  10 s. The report states exactly what that permits and what it does not.
- **Transcript coverage is partial**: opening, one middle section and the closing were read verbatim; roughly
  20 %–85 % of the runtime is unobtained.
- **No analytics exist here** — no CTR, retention, impressions, traffic sources or revenue, and **no claim that
  any technique caused the view count**.

Every gap is itemised in `REPORT.md` §3.3 and §14 with the specific tool that would close it.

---

## Re-running the pipeline

The extraction and measurement code is committed and re-runnable from any machine with normal internet access:

```bash
# 1. Full media + audio + frames + scene detection + measurement
#    (.github/workflows/extract.yml)  — needs an IP that YouTube does not bot-check
# 2. Storyboard-based timeline (works even when media download is blocked)
#    .github/workflows/storyboard.yml -> .github/scripts/storyboard_analyze.py
# 3. Audio measurement
#    .github/scripts/analyze_audio.py   (or .github/workflows/audio.yml end-to-end)
# 4. Caption normalisation to CSV
#    .github/scripts/subs_to_csv.py
```

If you run step 1 from a residential connection or with valid session cookies, you can close every gap in
§3.3 in about twenty minutes and regenerate the audio/caption CSVs that are referenced but empty here.
