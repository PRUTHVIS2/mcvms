# 01 Product Spec

## Goal
A centralized monitoring system for multiple cameras. Each camera watches a **predefined zone**. The admin attaches **registered actions** (rules) to zones. When a registered action triggers, the system (a) alerts the admin immediately, (b) saves the event as a permanent, searchable clip (with 15 s pre-roll) and keeps recording while the trigger is active or until the severity-based duration ends / admin stops it. Additionally, recurring objects (people first) get a persistent **identity** ("Person #N") tracked across cameras with a **match percentage**.

Course: Computer Vision (MCA, RVCE). Team 18. Evaluated on processing latency and multi-camera scalability; includes user authentication and role-based access control.

## Demo setup
3 camera feeds named cam01, cam02, cam03: looping video files pushed by ffmpeg to MediaMTX (default), phone camera (IP Webcam) or laptop webcam. Build and verify with 1 camera, then 2, then 3. Hardware: RTX 4070 Ti (12 GB), 12th-gen i7, 16 GB RAM, 500 GB storage. The client may have better hardware; design so cameras scale by config, not code.

## Vocabulary
- **Camera**: name, RTSP URL, location label, enabled flag.
- **Zone**: polygon or line drawn on a camera snapshot; coordinates stored as fractions (0-1) of frame width/height. May have ignore-polygons (posters, TVs, mirrors).
- **Registered action**: one rule = camera + zone + subject + trigger template + parameters + schedule + confirmation + response (severity, recording length, cooldown). See 04.
- **Event**: one firing of a registered action. Has snapshot, clip, severity, status (new / acknowledged / false_alarm).
- **Clip**: saved video for an event (pre-roll + active period + hold).
- **Identity**: persistent Person #N (or plate) built from a track's embeddings; matched with a percentage, never declared as certainty.
- **Incident**: events linked by the same identity across cameras within a time window.
- **Severity**: low / medium / critical -> recording length, retention, alert priority, cooldown.

## Users / roles
Owner (everything), Admin (cameras, rules, events, identities), In-charge (view assigned cameras/events, acknowledge). Department will define final policy; implement roles + audit log with placeholders.

## In scope (v1)
Live wall (no AI delay), camera setup wizard with zone drawing + dry run, 4 action templates, vehicle plate reading (Step 14), alerts (WebSocket + snapshot + cooldown, camera-offline alert), event clips + events page, person identity (body Re-ID) across cameras with match %, storage/retention, auth + roles, system health page, benchmarks.

## Future work (NOT built unless the human asks)
Extra triggers (wrong direction, unattended object, unknown person, expected-presence-missing, tailgating), AND/OR/NOT + sequence rules, H.265 recompression, open-vocabulary detection, adjacency-based prediction, face matching (needs approval).

## OUT OF SCOPE
Camera adjacency mesh / next-camera prediction (only the tiny travel-time table in 05 is allowed); open-vocabulary detectors (YOLO-World); face recognition on by default (optional module, OFF, needs department sign-off - biometric data); cloud deployment; mobile app; animal re-identification.

## Privacy note (placeholder for department)
What is stored: clips, snapshots, embeddings. Retention: per severity (06). Access: roles + audit log. Legal reference: India DPDP Act 2023. Department to finalize policy text.
