# 03 Data Model

SQLite, WAL mode, `PRAGMA foreign_keys=ON`. Times = INTEGER epoch ms UTC. Use migrations (Alembic or numbered .sql files in `backend/app/db/migrations/`).

```sql
CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN('owner','admin','incharge')), enabled INTEGER DEFAULT 1, created_at INTEGER NOT NULL);
CREATE TABLE user_cameras(user_id INTEGER REFERENCES users(id), camera_id TEXT REFERENCES cameras(id), PRIMARY KEY(user_id,camera_id));
CREATE TABLE cameras(id TEXT PRIMARY KEY, name TEXT NOT NULL, location TEXT, rtsp_url TEXT NOT NULL,   -- default rtsp://localhost:8554/<live_path>
  live_path TEXT NOT NULL,  -- MediaMTX path the browser plays, e.g. cam01
  analysis_fps REAL DEFAULT 8, enabled INTEGER DEFAULT 1, status TEXT DEFAULT 'unknown', last_frame_at INTEGER,
  reference_snapshot TEXT, created_at INTEGER NOT NULL);
CREATE TABLE zones(id TEXT PRIMARY KEY, camera_id TEXT NOT NULL REFERENCES cameras(id), name TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN('polygon','line')), points_json TEXT NOT NULL,      -- [[x,y],...] fractions 0-1
  ignore_json TEXT DEFAULT '[]');                                                     -- list of polygons
CREATE TABLE registered_actions(id TEXT PRIMARY KEY, camera_id TEXT NOT NULL REFERENCES cameras(id),
  zone_id TEXT NOT NULL REFERENCES zones(id), name TEXT NOT NULL, template TEXT NOT NULL,
  spec_json TEXT NOT NULL,            -- full registered-action JSON (below), validated by Pydantic
  severity TEXT NOT NULL CHECK(severity IN('low','medium','critical')), enabled INTEGER DEFAULT 1,
  dry_run INTEGER DEFAULT 0, created_by INTEGER REFERENCES users(id), created_at INTEGER NOT NULL);
CREATE TABLE events(id TEXT PRIMARY KEY, action_id TEXT NOT NULL REFERENCES registered_actions(id),
  camera_id TEXT NOT NULL, ts INTEGER NOT NULL, severity TEXT NOT NULL, status TEXT DEFAULT 'new'
  CHECK(status IN('new','acknowledged','false_alarm')), snapshot_path TEXT, track_id TEXT, identity_id INTEGER,
  identity_score REAL, details_json TEXT, incident_id TEXT, latency_ms INTEGER);
CREATE INDEX idx_events_ts ON events(ts); CREATE INDEX idx_events_cam ON events(camera_id, ts);
CREATE TABLE clips(id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id), camera_id TEXT NOT NULL,
  start_ts INTEGER NOT NULL, end_ts INTEGER, path TEXT, size_bytes INTEGER, sha256 TEXT,
  state TEXT DEFAULT 'recording' CHECK(state IN('recording','finalizing','ready','failed')),
  pinned INTEGER DEFAULT 0, retention_until INTEGER, meta_path TEXT);   -- meta = boxes/track/identity JSON for overlays
CREATE TABLE identities(id INTEGER PRIMARY KEY AUTOINCREMENT, cls TEXT NOT NULL,       -- person|vehicle
  status TEXT NOT NULL CHECK(status IN('tentative','confirmed')), label TEXT,          -- optional admin name
  first_seen INTEGER, last_seen INTEGER, sightings INTEGER DEFAULT 0, plate TEXT);
CREATE TABLE identity_embeddings(id INTEGER PRIMARY KEY, identity_id INTEGER REFERENCES identities(id) ON DELETE CASCADE,
  vector BLOB NOT NULL, quality REAL, camera_id TEXT, ts INTEGER);                     -- cap N per identity (config)
CREATE TABLE sightings(id INTEGER PRIMARY KEY, identity_id INTEGER REFERENCES identities(id), camera_id TEXT,
  track_id TEXT, start_ts INTEGER, end_ts INTEGER, score REAL, top3_json TEXT);
CREATE TABLE incidents(id TEXT PRIMARY KEY, identity_id INTEGER, start_ts INTEGER, end_ts INTEGER, summary TEXT);
CREATE TABLE alerts(id TEXT PRIMARY KEY, event_id TEXT, kind TEXT NOT NULL,   -- event|camera_offline|disk_low|...
  ts INTEGER, message TEXT, delivered INTEGER DEFAULT 0);
CREATE TABLE audit_log(id INTEGER PRIMARY KEY, ts INTEGER NOT NULL, user_id INTEGER, action TEXT NOT NULL, target TEXT, detail TEXT);
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT);
```

## Registered-action JSON (`spec_json`, Pydantic model `RegisteredActionSpec`)
```json
{
  "id": "ra_021", "camera": "cam01", "zone": "z_003", "enabled": true,
  "subject": { "classes": ["person"], "identity": {"mode":"any"}, "min_box_px": 60 },
  "trigger": { "template": "presence", "min_seconds": 3 },
  "schedule": { "days": ["mon","tue","wed","thu","fri","sat","sun"], "from": "22:00", "to": "06:00" },
  "confirm": { "min_confidence": 0.6, "n_of_m": [4,5] },
  "response": { "severity": "critical", "pre_roll_s": 15, "record_min": 60, "hold_s": 20, "cooldown_s": 30, "max_clip_min": 120 }
}
```
- `identity.mode`: `any` | `unknown_only` | `specific` (with `identity_id` + `min_match` 0-1, judged on the track-level score) | `watchlist`.
- `trigger` per template: `presence{min_seconds}`, `line_crossing{direction: in|out|either, margin_frac}`, `dwell{dwell_seconds}`, `count_threshold{max_count, min_seconds}`.
- Schedule windows may cross midnight (22:00-06:00 means evening to next morning). Evaluate in server local time zone from `config/app.yaml`.
- Severity defaults (editable in settings): low 15 min / medium 30 min / critical 60 min recording.
