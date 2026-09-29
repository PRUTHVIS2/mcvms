# AGENT RULES (read first, every session)

You are building the system described in `docs/01`-`docs/08`, working ONLY through `PLAN.md`. The human is a student following a guide; they run the checkpoints and commit with git.

## Session start (first prompt of a session)
Read this file, then every file in `docs/`, then `PLAN.md` and `PROGRESS.md`. If the human says "do not write code yet", write no code: reply with a ~15-line summary of what you will build and in what order, list conflicts/gaps/risks in the documents, and state the Python version, GPU and OS you detected. Do not add ideas that are not in the docs (no camera adjacency graph, no cloud services).

## The gate (one step per request)
1. Do only the step the human names ("Do PLAN.md step N"). Do not start later steps.
2. Implement that step's tasks, run its tests, and ALSO re-run all earlier steps' tests (regression).
3. "Passed" means you show the actual test output (paste it). Never just say "tests pass".
4. When the step passes: update `PROGRESS.md` (status, date, test output summary, files, limitations, how the human runs and checks it) and **STOP** so the human can do the human checkpoint and review. Do not move on until told "Step N is approved".
5. If tests fail: diagnose the root cause BEFORE changing code, fix, retest. **Maximum 3 attempts.** After the 3rd failure write `BLOCKED.md` (what you tried, the exact error, your hypothesis, options) and STOP.
6. Be able to explain the step in plain English and show exactly how the human runs it themselves.

## Protected things (never without explicit human approval)
- Do not weaken, delete or skip any test, tolerance or threshold, and do not edit files in `test_data/` (clips or answer JSONs). If you think a test or answer is wrong, ASK the human first.
- Do not hard-code expected results or special-case clip names.
- Do not change `docs/` or `PLAN.md`. If a spec is wrong or impossible, STOP and report.
- Do not add anything from "Future work / OUT OF SCOPE" in `docs/01_PRODUCT_SPEC.md`.
- Do not swap the detector, tracker, Re-ID model, database or frontend framework.
- No AI inference in the live-view path; never burn boxes into video.
- Do not run `git commit`/`git tag` (the human commits after each step); do tell them when it is a good moment to commit.
- Do not write outside the repo or the configured `data/` directory. Do not upload footage anywhere (all labelling/training stays local).
- Face recognition stays OFF.

## Environment facts
Windows 11 + PowerShell, venv at `.venv` (Python 3.11), NVIDIA RTX 4070 Ti with CUDA PyTorch, FFmpeg on PATH, MediaMTX running separately (`C:\mediamtx\mediamtx.exe`, RTSP 8554 / WebRTC 8889 / HLS 8888), cameras `cam01..cam03` pushed to `rtsp://localhost:8554/cam01..03`. Commands run from `backend/` or `frontend/`. Keep code cross-platform (pathlib, no hard-coded separators). Pin dependency versions in `backend/requirements.txt`.

## Coding standards
- Python 3.11, type hints, `logging` (no bare prints), `ruff` clean, pytest for tests; frontend TypeScript strict.
- Config in `config/*.yaml` and `.env`; no secrets, hard-coded IPs or paths in code.
- Timestamps: UTC integer epoch milliseconds; the UI converts to local time.
- Every service reconnects with exponential backoff and never lets one camera failure take down the system.
- Each module has a docstring saying WHY it exists and what to do if it fails (alternatives). Comment non-obvious CV logic (coordinate spaces, thresholds).
- Log per-stage timings so latency can be measured (docs/08).
- Provide small CLI tools under `backend/app/tools/` where PLAN.md asks for them so the human can verify things by running one command.
