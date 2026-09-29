# PROGRESS (the agent updates this after every step)

Status: NOT STARTED / IN PROGRESS / PASSED / PASSED (synthetic) / BLOCKED (see BLOCKED.md)

| Step | Name | Status | Date | Notes |
|---|---|---|---|---|
| 0 | Project skeleton and environment check | PASSED | 2026-09-29 | |
| 1 | Database and login | PASSED | 2026-09-29 | |


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

### Step 1: Database and login
**What was built**:
- Configuration loader (`config.py`) parsing `app.yaml` and `storage_policy.yaml` with Pydantic.
- SQLite WAL mode database session (`session.py`).
- SQLAlchemy models mapping to `03_DATA_MODEL.md` (`models.py`).
- Alembic set up and initial migration executed.
- JWT authentication and bcrypt password hashing using `passlib` (`auth.py`).
- Role dependency (`role_required`) to restrict access.
- Audit logging helper (`audit.py`).
- FastAPI `main.py` entrypoint with `/api/health`, `/api/token`, and a placeholder `/api/cameras` route restricted to owner/admin.
- CLI script to seed the first owner user (`seed_owner.py`).
- Tests covering bad YAML, database fixtures, login success/fail, and role permissions.

**Files touched**:
- `backend/requirements.txt`
- `backend/app/config.py`
- `backend/app/db/session.py`
- `backend/app/db/models.py`
- `backend/app/auth.py`
- `backend/app/audit.py`
- `backend/app/main.py`
- `backend/app/tools/seed_owner.py`
- `backend/app/db/migrations/*`
- `backend/tests/unit/test_step1.py`

**Test output**:
```text
......                                                                   [100%]
============================== warnings summary ===============================
C:\Users\pruth\AppData\Local\Programs\Python\Python311\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\pruth\AppData\Local\Programs\Python\Python311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
6 passed, 1 warning in 1.54s
```

**Limitations**: `/api/cameras` is currently a placeholder for testing roles, and the storage policy isn't fully utilized yet.
**How you check**: Run `cd backend && python -m app.tools.seed_owner --username admin --password pass`, then start the server with `uvicorn app.main:app`. Go to `http://localhost:8000/docs`, use "Authorize" to log in with `admin/pass`, and try the `/api/cameras` endpoint.
**Open questions**: None.
