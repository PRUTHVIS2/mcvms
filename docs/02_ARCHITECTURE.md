# 02 Architecture

Project root on the human's PC: `mcvms/` (Windows 11, PowerShell, venv `mcvms\.venv`, Python 3.11). Keep all code cross-platform (`pathlib`, no hard-coded separators).

## Three separate stream paths (LIVE VIEW MUST NEVER WAIT FOR AI)
```
Camera ─► MediaMTX relay ─┬─► Browser live view (WebRTC :8889, HLS fallback :8888)   [no AI in this path]
                          ├─► Analysis worker (1 process/camera, low-res, ~8 FPS)
                          │      YOLO11 detect ─► ByteTrack ─► identity queue ─► rule engine ─► events/alerts
                          └─► Recorder (ffmpeg -c copy, 10 s segments) ─► continuous store ─► clip assembler
```
Bounding boxes and zones travel as JSON over WebSocket and are drawn in the browser on a canvas over the video. NEVER re-encode video with boxes burned in.

## Cameras and the relay (matches the guide, Part B and C)
- ONE MediaMTX instance, started by the human (`C:\mediamtx\mediamtx.exe`, default config). Ports: RTSP **8554**, WebRTC **8889**, HLS **8888**.
- Cameras (fake or real) are pushed by ffmpeg to `rtsp://localhost:8554/cam01`, `/cam02`, `/cam03` (H.264, `-g 25`, no audio). Camera ids/paths are `cam01`, `cam02`, `cam03`.
- The backend does NOT start or configure MediaMTX. It only checks it is reachable and reports it on the System page.
- Camera record fields: `rtsp_url` (what analysis and recorder read; default `rtsp://localhost:8554/<live_path>`) and `live_path` (relay path the browser plays, e.g. `cam01`). For a real IP camera that MediaMTX pulls, the human adds a `source:` path to MediaMTX; the app still just reads the relay path.
- Backend `http://localhost:8000` (API docs at `/docs`), dashboard `http://localhost:5173`.

## Tech stack (fixed - do not swap)
Python 3.11, FastAPI + uvicorn, SQLite (WAL) via sqlite3/SQLAlchemy core, Pydantic v2, Ultralytics YOLO11 (`yolo11s.pt`; fall back to `yolo11n.pt` if too slow; TensorRT FP16 export in Step 15), ByteTrack (Ultralytics tracker), OSNet Re-ID (torchreid or boxmot, `osnet_x1_0` pretrained), OpenCV/PyAV for frame grabs, FFmpeg for recording/clips, React + Vite + TypeScript + Tailwind, pytest, ruff, vitest, Playwright.

## Processes
1. `backend` - REST + WebSocket, DB, scheduler (retention, health), supervisor that starts/stops workers.
2. `worker` (one per enabled camera) - low-res frame grab, detect + track + rules; sends events to backend via multiprocessing queue.
3. `recorder` (one supervised ffmpeg per camera).
4. `identity` service (one, GPU) - crops -> OSNet -> gallery matching.
5. `frontend` (Vite dev server).

## Compute plan
Detect on frames downscaled to max side 960 at ~8 FPS (`analysis_fps`, default 8; the UI overlay is fine at 8+). Batch frames across cameras in one inference call once >1 camera (filter classes per camera afterwards). Re-ID every 1-2 s per track on good crops only. Per-camera `classes` filter is derived from that camera's enabled rules (never shown to users). Measure with 1 camera before adding more.

## Failure handling
Stream drop -> reconnect with backoff (1,2,4..30 s); watchdog: no new frame in 5 s -> OFFLINE + `camera_offline` alert; recovery -> ONLINE. One camera failing never stops the others or the live view.

## Time
Server stamps frames on arrival (UTC epoch ms). Camera/phone clocks are ignored.

## Folder layout (repo root = mcvms/)
```
mcvms/
  AGENT_RULES.md  PLAN.md  PROGRESS.md  BLOCKED.md (only when blocked)
  config/    app.yaml  storage_policy.yaml  travel_times.yaml
  docs/      01_PRODUCT_SPEC.md ... 08_TESTING.md
  test_data/ human clips + matching .json answer files
  data/      db/  continuous/<cam>/  clips/  snapshots/  crops/  models/   (git-ignored)
  backend/   app/ (main.py api/ db/ services/ workers/ rules/ identity/ storage/ core/ tools/)
             tests/ (unit/ integration/)   requirements.txt
  frontend/  src/ (pages/ components/ lib/)
  scripts/   eval_events.py eval_tracking.py eval_reid.py calibrate_identity.py
  dataset/   (fine-tuning, git-ignored)
```
Commands are run from `backend/` (`python -m app.tools.check_env`, `uvicorn app.main:app --reload`, `pytest -q`) and `frontend/` (`npm run dev`).
