# 08 Testing and Benchmarks

## Test data (recorded by the HUMAN in guide Part D; the agent must never fabricate or edit it)
Folder `test_data/`. Format: 1280x720 or 1920x1080, 25 fps, H.264 MP4, fixed camera, 30-120 s. Every clip has a same-name `.json` answer file. Templates for all of them are already in `test_data/` (`reid_walk_appearances.json` covers the three reid_walk clips) (they may have `"zone_polygon": null` until the human picks a zone; the agent's snapshot tool helps pick it).
| Clip | What happens | Correct answer |
|---|---|---|
| hall_presence_01 | empty 10 s, person walks in, stays 8 s, leaves, empty 10 s | 1 presence event ~10-18 s |
| hall_flicker_01 | person crosses zone in < 2 s | 0 events (min_seconds = 3) |
| door_line_01 | 3 people enter one by one, 2 leave | 3 "in", 2 "out" |
| door_dwell_01 | person stands near door 90 s | 1 dwell event at ~60 s |
| gate_line_01 | 2 vehicles enter, 1 leaves | 2 "in", 1 "out" |
| night_01 | presence in dim light | robustness check (report only) |
| crowd_01 | 5+ people crossing/overlapping | tracking stress test (report only) |
| reid_walk_cam1/2/3 | same 5-10 people walk past cam1, then cam2, then cam3 | same person keeps same identity (appearances JSON) |

Event answer JSON: `{clip, rule{template, classes, zone_polygon (fractions) or zone_line, min_seconds|dwell_seconds|direction}, expected_events:[{start_s,end_s,tolerance_s}]}`. Line clips list `expected_events` with `"direction":"in"|"out"`.
Count-based answers (line clips) use `expected_counts:{in:N,out:M}` when exact times are not recorded; `report_only:true` clips (night_01, crowd_01) produce metrics but no pass/fail.
Re-ID answer JSON: `{appearances:[{person, camera, clip, start_s, end_s}]}`.
Rules: the agent may not weaken tolerances or special-case clip names. If a clip's answer looks wrong, ask the human.
Until clips exist, steps run on synthetic unit tests and any looping video, and are marked `PASSED (synthetic)` in PROGRESS.md; they must be re-run against real clips once available.

## Test levels
1. Unit (pytest): geometry, rule state machine, schedule, calibration, retention logic, DB layer, auth.
2. Integration: replay a clip through the worker (file source instead of RTSP) and compare with its answer JSON; API tests with FastAPI TestClient.
3. System: run against the 3 fake camera streams for >= 30 min: no crash, RAM growth < 10%, segments gapless.
4. Human checkpoints (PLAN.md lists them per step).

## Evaluation scripts (guide Part H; write outputs to `docs/results/` as CSV + markdown + PNG graphs)
| Script | Measures |
|---|---|
| `scripts/eval_events.py` | event precision, recall, F1 vs answer JSONs |
| `python -m app.tools.bench` | event-to-alert latency p50/p95, per-stage latency, GPU/CPU/RAM per camera count (1,2,3 real, then simulated 4-8 by duplicating streams), knee of the latency curve = max cameras at target p95 < 2 s |
| `scripts/eval_tracking.py` | IDF1, ID switches vs hand-labelled clips (py-motmetrics) |
| `scripts/eval_reid.py` | Rank-1, mAP, cross-camera identity accuracy, reliability curve of the match % |
| `scripts/calibrate_identity.py` | fits similarity -> probability (isotonic, Platt fallback) from labelled pairs |
Also: live-view latency unaffected by AI load (detector on vs off); kill a stream -> `camera_offline` within 10 s and auto-recover; kill ffmpeg -> restarts; recording gaps > 1 segment = fail; clip pre-roll within +/- 2 s.
Report conditions: day/evening/night, crowded/sparse, backlight, similar clothing, partial occlusion.
