# 07 API and UI

Base `/api`, JSON, JWT auth (Bearer). Role checks server-side. Every mutating call writes `audit_log`.

## REST
- Auth: `POST /auth/login`, `POST /auth/logout`, `GET /me`
- Users (owner): `GET/POST /users`, `PATCH/DELETE /users/{id}`
- Cameras: `GET/POST /cameras`, `GET/PATCH/DELETE /cameras/{id}`, `POST /cameras/test` (RTSP url -> snapshot JPEG or error), `GET /cameras/{id}/snapshot`, `GET /cameras/{id}/status`
- Zones: `GET/POST /cameras/{id}/zones`, `PATCH/DELETE /zones/{id}` (points as fractions)
- Actions: `GET/POST /actions`, `GET/PATCH/DELETE /actions/{id}`, `POST /actions/{id}/enable|disable`, `POST /actions/{id}/dry-run` (body: live | clip_path; returns stream id)
- Templates: `GET /templates` (which templates fit polygon vs line, param schemas)
- Events: `GET /events?from&to&camera&severity&action&status&identity&page`, `GET /events/{id}`, `PATCH /events/{id}` (status), `POST /events/{id}/extend`, `POST /events/{id}/stop-recording`
- Clips: `GET /clips/{id}/stream` (HTTP range), `GET /clips/{id}/download?format=mp4|mkv`, `POST /clips/{id}/pin`, `POST /clips/{id}/unpin`, `GET /clips/{id}/meta`
- Identities: `GET /identities`, `GET /identities/{id}` (timeline, sightings, top matches), `POST /identities/merge`, `POST /identities/{id}/split`, `PATCH /identities/{id}` (label), `DELETE /identities/{id}`
- System: `GET /system/health` (disk %, per-camera fps/latency/status, recorder state, GPU util), `GET /system/metrics`, `GET/PATCH /settings`
- Audit: `GET /audit`

## WebSocket `/ws`
Server -> client messages `{type, ts, data}`:
`overlay` (per camera: boxes, track ids, identity labels+match%, zones, dry-run would_trigger markers, ~5-10 Hz), `event_created`, `event_updated`, `alert` (event/camera_offline/disk_low), `camera_status`, `recording_state`, `health`.
Client -> server: `subscribe{cameras:[...], overlay:true|false}`.
Overlays are drawn on a `<canvas>` above the `<video>`; toggle-able; coordinates are fractions.

## Live video
Browser plays `http://localhost:8889/<live_path>` (MediaMTX WebRTC) with HLS fallback `http://localhost:8888/<live_path>` (about 3-5 s late, so WebRTC is preferred). No AI in this path.

## Screens (React + Tailwind, dark theme default, same severity colours everywhere: low=blue, medium=amber, critical=red)
1. **Login**
2. **Live wall**: grid of camera tiles (status dot, name, fps), click to expand, toggle boxes/zones, right-side alert feed with severity badges and ack/false-alarm buttons; "Add camera" tile.
3. **Events**: filter bar + table/grid with thumbnails; detail drawer with player starting at trigger (pre-roll visible), overlays from sidecar meta, actions: acknowledge, false alarm, pin, extend/stop, download.
4. **Identities**: cards (Person #N, thumbnail, last seen), detail with timeline across cameras, top-3 match %, merge/split/rename.
5. **Cameras / Setup wizard** (steps below)
6. **Rules**: list of registered actions with on/off switch, severity, dry-run button, edit.
7. **System**: disk usage bar with watermarks, camera health, recording state, latency/fps charts.
8. **Users & audit** (placeholder-level).

## Setup wizard (stepper)
1 Add camera (name, RTSP URL, location; **Test connection** shows snapshot) ->
2 Draw zone on the snapshot (polygon: click points, double-click to close; line: two clicks with direction arrow; optional ignore polygons; name it; coordinates stored as fractions; reference snapshot saved) ->
3 Pick template (only ones fitting the shape) ->
4 Parameters (classes, schedule incl. cross-midnight, min seconds/dwell/direction/max count, confidence default 60%, identity filter) ->
5 Severity and response (recording minutes, cooldown, pre-roll fixed 15 s) ->
6 **Dry run** (live or saved clip; shows zone, boxes, "would have triggered" markers, no real alerts; user can go back and adjust) ->
7 Summary and Activate.

## Alerts
Delivered over WebSocket within the latency target (event -> UI < 2 s). Each alert has snapshot with zone+box drawn. Cooldown suppresses repeats. Browser Notification API optional. Placeholders for email/SMS/Telegram channels (interface only).
