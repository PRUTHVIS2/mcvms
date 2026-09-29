# 04 Rule Engine

Lives in `backend/app/rules/`. Pure logic, no I/O, fully unit-testable with synthetic tracks.

## Inputs per analysed frame (per camera)
`FrameResult{ts, frame_w, frame_h, tracks:[Track{track_id, cls, conf, bbox_xyxy_px}]}`.
Convert bbox to fractions, then use the **bottom-centre point** ((x1+x2)/2, y2) as the "foot" point for zone tests. Use bbox centre only for objects that are not standing (bags).

## Zone geometry
- Point-in-polygon: ray casting on fraction coordinates. Ignore polygons: if the foot point is inside any ignore polygon, drop the detection for that rule.
- Line crossing: track keeps last K foot points; crossing = segment (prev->curr) intersects the line AND sides (sign of cross product) differ by more than `margin_frac` on each side (buffer so standing on the line doesn't refire). Direction "in" = crossing from the line's left to right normal (document the convention and show it in the wizard with an arrow).

## Templates (v1)
1. **presence**: subject class inside polygon continuously >= `min_seconds` while schedule active. Fires once per track (cooldown).
2. **line_crossing**: as above, direction filter.
3. **dwell**: track inside polygon >= `dwell_seconds` (timer resets if track leaves > 2 s).
4. **count_threshold**: number of distinct tracks of class inside polygon > `max_count` for >= `min_seconds`.

## Rule state machine (per rule + track; implement exactly)
```
IDLE --object seen in zone--> PENDING --gone before min time--> IDLE
PENDING --held long enough (N-of-M + min_seconds)--> ACTIVE (event fires, clip starts)
ACTIVE --object left--> HOLDING --came back--> ACTIVE
HOLDING --gone for hold_s--> IDLE (clip closes)
```
Rules fire only after the situation HOLDS and end only after it has been gone for the hold time, so single-frame flicker never alerts.

## Confirmation and stability
- Only tracks with conf >= `min_confidence` and box height >= `min_box_px` count.
- **N-of-M**: condition must be true in N of the last M analysed frames before a trigger becomes "active".
- **Hysteresis**: starting a trigger needs `min_confidence`; keeping it active only needs `min_confidence - 0.15`.
- **Cooldown** per (rule, track): no new event for `cooldown_s`. If the rule re-fires while a clip is recording, EXTEND the current clip (do not create a new event).
- Track loss tolerance: a track missing < 1.5 s keeps its state (ByteTrack buffer).
- Schedule gate first: outside schedule, evaluate nothing.

## Output
`RuleTrigger{action_id, camera_id, ts, track_id, cls, details, snapshot_frame}` -> event service: create event row, save snapshot (with drawn zone + box), emit alert, tell recorder to build/extend clip. Record `latency_ms` = now - frame arrival ts.

## Dry run
A rule with `dry_run=1` or executed via the dry-run endpoint produces `would_trigger` markers (frame ts, track, reason) streamed to the UI; NO event row, alert, or clip. Dry run works on the live feed or on a saved test clip file.

## Stretch triggers (future work, not in PLAN): wrong_direction, unattended_object (object stationary with no person within R px for T s), unknown_person, expected_presence_missing, tailgating, AND/OR/NOT + "A then B within T s".

## Required unit tests (synthetic)
Track walks across line both directions; stands on line (0 events); flickers in/out of polygon (N-of-M suppresses); dwell timer reset; count threshold with 2/3 tracks; schedule across midnight; ignore polygon suppresses; cooldown; clip extension on re-fire.
