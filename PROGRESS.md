# PROGRESS (the agent updates this after every step)

Status: NOT STARTED / IN PROGRESS / PASSED / PASSED (synthetic) / BLOCKED (see BLOCKED.md)

| Step | Name | Status | Date | Notes |
|---|---|---|---|---|
| 0 | Project skeleton and environment check | PASSED | 2026-09-29 | |
| 1 | Database and login | NOT STARTED | | |
| 2 | Camera streams and health | NOT STARTED | | |
| 3 | Object detection | NOT STARTED | | |
| 4 | Tracking | NOT STARTED | | |
| 5 | Rule engine | NOT STARTED | | |
| 6 | Recording and clips | NOT STARTED | | |
| 7 | Events and alerts | NOT STARTED | | |
| 8 | Camera, zone and rule management | NOT STARTED | | |
| 9 | Dashboard: live wall | NOT STARTED | | |
| 10 | Events page and playback | NOT STARTED | | |
| 11 | Setup wizard | NOT STARTED | | |
| 12 | Person identity | NOT STARTED | | |
| 13 | Multi-camera | NOT STARTED | | |
| 14 | Vehicles and plates | NOT STARTED | | |
| 15 | System health and benchmarks | NOT STARTED | | |
| 16 | Hardening and demo | NOT STARTED | | |

## Log
(For each step: what was built, files touched, pasted test output, limitations, how the human runs/checks it, open questions. After 3 failed attempts: see BLOCKED.md.)

### Step 0: Project skeleton and environment check
**What was built**: 
- Folder skeleton as per `02_ARCHITECTURE.md`.
- Basic configuration (`backend/requirements.txt`, `backend/pyproject.toml`, `config/app.yaml`, `config/travel_times.yaml`).
- `check_env.py` script for validating Python, Torch+CUDA, FFmpeg, MediaMTX, camera streams, and downloading YOLO weights.
- `test_env.py` unit test placeholder.

**Files touched**:
- Directories in `backend`, `data`, `frontend`, `scripts`.
- `backend/requirements.txt`, `backend/pyproject.toml`, `config/app.yaml`, `config/travel_times.yaml`, `backend/app/tools/check_env.py`, `backend/tests/unit/test_env.py`

**Test output**:
```text
.                                                                        [100%]
Environment Check
--------------------------------------------------
Python              : 3.11.9 
Torch/CUDA          : 2.6.0+cu124, GPU: NVIDIA GeForce RTX 4070 Ti 
Ultralytics         : 8.4.165 
FFmpeg              : ffmpeg version 9.0.2-full_buil... 
FFprobe             : ffprobe version 9.0.2-full_bui... 
Node                : Not found 
NPM                 : Not found 
MediaMTX (8554)     : Reachable 
Camera cam01        : Readable 
Camera cam02        : Failed (not running?) 
Camera cam03        : Failed (not running?) 
Free Disk           : 129 GB 
yolo11s.pt          : Already exists 
yolo11n.pt          : Already exists 
```

**Limitations**: None.
**How you check**: Run `python -m app.tools.check_env` from the `backend/` folder and verify it's mostly green (cam02/03 failing is fine if they are not running).
**Open questions**: Node and NPM were not found in PATH; they will be needed for frontend steps later (Step 9+).
