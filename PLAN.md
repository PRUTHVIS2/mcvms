# PLAN.md - gated build plan (17 steps, 0-16)

Follow AGENT_RULES.md. One step per request. After each step: show test output, update PROGRESS.md, STOP. The "You check" line is what the human does before approving. Each step is about 2-4 hours of agent work. Human commits after approval.
Human-supplied inputs: clips + answer JSONs in `test_data/` (guide Part D), running MediaMTX and fake cameras cam01-cam03 (guide Part C).

## Step 0 - Project skeleton and environment check
Tasks: create the folder layout from docs/02; `backend/requirements.txt` (pinned), `backend/pyproject.toml` (ruff, pytest), `frontend/` placeholder, `config/app.yaml` (analysis_fps 8, thresholds, timezone, gallery policy) and `config/travel_times.yaml`; `python -m app.tools.check_env` prints (green/red): Python version, torch + CUDA + GPU name, ultralytics version, ffmpeg/ffprobe version, node/npm, MediaMTX reachable (RTSP 8554), each camera URL readable (ffprobe, red is allowed with a message if the camera is not running), free disk. Download `yolo11s.pt` (and `yolo11n.pt`) into `data/models/`.
Tests: `pytest -q` runs; check_env exit code 0 when torch CUDA and ffmpeg are OK.
You check: `python -m app.tools.check_env` is all green.

## Step 1 - Database and login
Tasks: FastAPI app + `/api/health`; config loader with Pydantic validation (app.yaml, storage_policy.yaml); SQLite migrations creating all tables in docs/03; seed owner user via CLI; JWT auth with password hashing; role dependency (owner/admin/incharge); audit-log helper.
Tests: bad YAML rejected; DB created; login success/fail; incharge cannot create a camera; audit row written.
You check: open `http://localhost:8000/docs`, log in, see role restrictions.

## Step 2 - Camera streams and health
Tasks: camera registry (create/list/get with `rtsp_url`, `live_path`) enough to add cam01-cam03; stream health monitor per camera (frame reader via ffmpeg/PyAV): status ONLINE/OFFLINE/UNKNOWN, fps, last_frame_at; frozen >5 s -> OFFLINE; reconnect with backoff; `POST /cameras/test` (grab one frame -> JPEG); MediaMTX reachability on `/system/health`; `python -m app.tools.snapshot --camera cam01 --out x.jpg` and `--clip test_data/X.mp4 --at 5` (snapshot from a stream or clip, used later to pick zones).
Tests: with a running fake camera status becomes ONLINE; stop the ffmpeg push -> OFFLINE within 10 s; restart -> ONLINE; snapshot returns a valid JPEG.
You check: start a fake camera, see ONLINE; stop it, see OFFLINE; restart, it recovers. Live view in the browser (`http://localhost:8889/cam01`) stays smooth (no AI yet).

## Step 3 - Object detection
Tasks: analysis worker: read frames from the relay (or a clip file in test mode), downscale (max side 960), throttle to `analysis_fps`, stamp arrival time, run YOLO11 on GPU with per-camera `classes` (person, car, motorcycle, bus, truck), output `FrameResult` in fractions; log per-stage timings; `python -m app.tools.annotate --source <clip|rtsp> --out out.mp4` writes an annotated video.
Tests: on the test_data clips people/vehicles are detected in >= 90% of frames where visible (spot-check list built with the human); GPU is used; worker survives a stream drop; live view unaffected with worker on vs off.
You check: watch the annotated video; do people and cars get boxes? Note misses (candidates for fine-tuning in guide Part G).

## Step 4 - Tracking
Tasks: ByteTrack (Ultralytics tracker, persist across frames) per camera with stable track ids like `cam01-T41`; `annotate` tool now draws track numbers; `python -m app.tools.track_report --source <clip>` prints track count and estimated ID switches; WebSocket `/ws` with `overlay` messages (boxes, ids) and a minimal HTML test page drawing them over the live video.
Tests: id continuity through a 1 s occlusion on a clip; ws message schema test.
You check: watch numbers on people in the annotated video; do ids stay the same while they walk? Count switches. Boxes on the live test page line up with the video.

## Step 5 - Rule engine
Tasks: zone geometry, foot-point logic, 4 templates, state machine (IDLE/PENDING/ACTIVE/HOLDING), N-of-M, hysteresis, cooldown, schedule (incl. across midnight), ignore zones, dry-run markers, per docs/04. Engine works on `RegisteredActionSpec` objects (a JSON file loader is enough until Step 8). Event objects carry snapshot frame and latency. `python -m app.tools.run_rules --clip test_data/X.mp4 --rule test_data/X.json` prints events with times. `scripts/eval_events.py` compares against answer JSONs and prints precision/recall. If a JSON has no `zone_polygon`, the tool must fail with a message telling the human to pick one using the snapshot tool (do not invent zones).
Tests: all synthetic tests listed in docs/04; each clip in test_data with an answer JSON.
You check: read the test names; ask the agent to explain the line-crossing test; confirm line direction (in/out) matches what you see.

## Step 6 - Recording and clips
Tasks: continuous recorder (ffmpeg -c copy, 10 s segments, per docs/06 and config/storage_policy.yaml), segment index, clip assembler (15 s pre-roll + active + hold, extend on re-fire, max length), finalize (size, SHA-256, retention_until), crash recovery, sidecar metadata JSON, clips API with range streaming; `python -m app.tools.trigger_test_event --camera cam01` creates a test event and clip.
Tests: gapless segments for 10 min; clip starts about T-15 s (+/-2 s) and plays in ffprobe; re-fire extends instead of duplicating; kill ffmpeg -> restarts; hash verified; recovery finalizes a stuck clip.
You check: trigger a test event, open the saved clip in VLC; does it start about 15 s before?

## Step 7 - Events and alerts
Tasks: event service writes events + snapshot (zone + box drawn); alert service over WebSocket with cooldown; `camera_offline` and `disk_low` alerts; events API (filters, acknowledge, false alarm, extend, stop recording, pin) with audit entries.
Tests: alert latency p95 < 2 s on clip replay; cooldown suppresses repeats; offline alert within 10 s; filter tests.
You check: watch an alert arrive over the WebSocket; acknowledge it via `/docs`.

## Step 8 - Camera, zone and rule management
Tasks: full CRUD for cameras (with test connection), zones (fractions, ignore zones) and registered actions with Pydantic validation and the `/templates` endpoint; workers load enabled actions from the DB and reload when they change; enable/disable; dry-run endpoint; per-camera class filter derived automatically.
Tests: validation rejects bad shapes (e.g. line_crossing on a polygon); creating a rule via API makes it fire on a clip replay; disabling stops it.
You check: create a camera, zone and rule through `/docs`, see it work.

## Step 9 - Dashboard: live wall
Tasks: React + Vite + TS + Tailwind app on :5173; login; Live wall with WebRTC tiles from :8889 (HLS fallback), status dots, boxes and zones drawn on canvas over video (toggle), alert feed with severity colours and ack/false-alarm buttons, dark theme, "Add camera" tile linking to the wizard (placeholder).
Tests: `npm run build` clean; vitest for severity badge and filters; Playwright smoke: login -> live wall shows 3 tiles.
You check: log in on the web page; is video smooth; are boxes and zones drawn over it?

## Step 10 - Events page and playback
Tasks: Events page (filters, thumbnails), detail drawer with player starting at the trigger with pre-roll visible and overlays from sidecar metadata, actions: acknowledge, false alarm, pin, extend/stop, download; Rules page (list, on/off, dry-run button); System page (disk bar with watermarks, camera health, recording state, latency).
Tests: Playwright: click an event -> clip plays; pin/unpin works.
You check: click an alert, play the clip, pin it, extend it.

## Step 11 - Setup wizard
Tasks: 7-step wizard per docs/07 (add camera + test connection + snapshot, draw polygon/line with direction arrow and ignore polygons, template filtering by shape, parameters incl. schedule, severity/response, dry run with "would have triggered" markers, activate); reference snapshot saved; camera-moved warning (compare live frame with reference).
Tests: unit tests for canvas<->fraction conversion at 3 resolutions; Playwright: wizard end-to-end creates a rule that fires on a clip replay.
You check: add a camera, draw a zone, run the dry run, activate.

## Step 12 - Person identity
Tasks: identity service per docs/05: crop quality filter, diversity rule (>=20 good varied crops to confirm), OSNet embeddings, track-level fingerprint, gallery, same-camera conflict, ambiguity margin, Hungarian assignment, tentative/confirmed, top-3, uncalibrated High/Medium/Low tiers, "collecting evidence..." state, identity filter in rules, identities API and page (timeline, merge/split/rename), overlay shows "Person #N" with match.
Tests: unit tests for quality filter, diversity, margin, same-camera conflict; reid_walk clips: same person keeps identity, different people differ; `scripts/eval_reid.py` prints Rank-1/mAP.
You check: walk in front of a camera, leave, return. Same "Person #N" with a match indicator? Look at the crops used.

## Step 13 - Multi-camera
Tasks: run cam01-cam03 together; batched inference across cameras; per-camera class filtering; travel-time table; cross-camera identity and incident linking (same identity within `incident_window_s`); `scripts/calibrate_identity.py` (isotonic, Platt fallback) and UI switch to calibrated percentages once labelled pairs exist; `scripts/eval_tracking.py` (IDF1, ID switches).
Tests: 30-minute run with 3 streams: no crash, RAM growth < 10%, p95 alert latency < 2 s; cross-camera fixture passes; calibration unit test on synthetic scores.
You check: walk past cam 1, 2, 3; is the identity kept; is the incident linked?

## Step 14 - Vehicles and plates
Tasks: plate detector (human supplies dataset in `dataset/plates/`; agent writes the training script and evaluation vs pretrained), pretrained OCR for reading, plate identity in the Identity Manager (match = OCR confidence x string similarity, 1-char tolerance; appearance fallback), shown on events/identities pages; gate_line_01 rule for vehicles.
Tests: plate string tests on labelled images; gate clip produces expected in/out events; OCR similarity unit tests.
You check: show a plate to the camera; is it read? Failure cases noted.

## Step 15 - System health and benchmarks
Tasks: `python -m app.tools.bench` (1, 2, 3 cameras and simulated 4-8), resource logging, latency p50/p95 per stage, TensorRT FP16 export with fallback, graphs to `docs/results/`, `scripts/eval_events.py` over all clips, System page charts, retention job and disk watermarks (80% warn, 90% purge order per storage_policy.yaml).
Tests: retention never deletes critical or pinned clips; simulated 90% disk purges in the right order; bench produces CSV + PNG.
You check: run the benchmark and look at the graphs; find the knee of the latency curve.

## Step 16 - Hardening and demo
Tasks: startup self-check (paths writable, space, ffmpeg, MediaMTX); users/roles UI (assigned cameras for in-charge) and audit page; privacy placeholders; log rotation; a demo seed script and `docs/DEMO_SCRIPT.md` following the guide's 8-step demo (live wall, wizard, hallway alert with Person #N, clip with 15 s pre-roll, cross-camera identity and incident, vehicle plate, System page, kill a camera -> offline alert); top-level `README.md` with run instructions (MediaMTX, fake cameras, backend, frontend).
Tests: full test suite green; role tests; a scripted end-to-end dry run of the demo.
You check: rehearse the full demo twice; keep a backup screen recording.
