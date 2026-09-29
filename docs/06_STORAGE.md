# 06 Storage

Config: `storage_policy.yaml` (authoritative; read its comments). Implementation in `backend/app/storage/`.

## Two stores
1. **Continuous store**: per-camera ffmpeg `-c copy` into 10-second MKV segments named by UTC epoch ms
   `data/continuous/<camera_id>/<epoch_ms>.mkv`. Rolling 24 h, deleted oldest-first by the retention job.
   Command shape:
   `ffmpeg -rtsp_transport tcp -i <rtsp> -an -c copy -f segment -segment_time 10 -segment_format matroska -reset_timestamps 1 -strftime 0 -segment_list_flags live data/continuous/<cam>/%%s.mkv`
   (Agent: verify segment naming works on Windows; if `%s` epoch isn't supported by the ffmpeg build, name by counter and store start times in a small sqlite table `segments`.)
2. **Event-clip store**: `data/clips/<YYYY-MM-DD>/<event_id>.mkv` + `<event_id>.json` (overlay metadata) + snapshot. Indexed in DB (`clips`, `events`). Kept per retention rules. Dashboard lists events by date/camera/action/severity with thumbnails; clicking plays only that clip.

## Clip assembly
Trigger at T: clip window = [T - pre_roll, T + active + hold]. Recorder service finds segments overlapping the window, concatenates with the ffmpeg concat demuxer `-c copy`. While the event is active the clip is "recording": append newly finished segments. On end (trigger off + hold, or duration cap, or admin stop) -> finalize: SHA-256, size, state=ready, retention_until from severity.
Cut accuracy is one keyframe interval (1-2 s) because of `-c copy`; acceptable. Fallback if cuts fail: re-encode only the first/last segment.

## Guards
- Disk watermarks (80% warn, 90% emergency purge order: old continuous -> expired low clips -> expired medium; never critical/pinned).
- Max clip length, per-rule cooldown, extend-not-duplicate.
- Startup self-check: paths writable, free space >= reserve, ffmpeg found.
- Pin/unpin clip (admin), manual stop/extend recording from the alert.
- Crash recovery on startup: clips in `recording` state -> finalize from available segments.

## Storage tests: see 08.
