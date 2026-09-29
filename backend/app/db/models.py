from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    enabled = Column(Integer, default=1)
    created_at = Column(Integer, nullable=False)
    __table_args__ = (CheckConstraint("role IN ('owner','admin','incharge')"),)

class UserCamera(Base):
    __tablename__ = "user_cameras"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    camera_id = Column(String, ForeignKey("cameras.id"), primary_key=True)

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String)
    rtsp_url = Column(String, nullable=False)
    live_path = Column(String, nullable=False)
    analysis_fps = Column(Float, default=8.0)
    enabled = Column(Integer, default=1)
    status = Column(String, default='unknown')
    last_frame_at = Column(Integer)
    reference_snapshot = Column(String)
    created_at = Column(Integer, nullable=False)

class Zone(Base):
    __tablename__ = "zones"
    id = Column(String, primary_key=True)
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    points_json = Column(String, nullable=False)
    ignore_json = Column(String, default='[]')
    __table_args__ = (CheckConstraint("type IN ('polygon','line')"),)

class RegisteredAction(Base):
    __tablename__ = "registered_actions"
    id = Column(String, primary_key=True)
    camera_id = Column(String, ForeignKey("cameras.id"), nullable=False)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    name = Column(String, nullable=False)
    template = Column(String, nullable=False)
    spec_json = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    enabled = Column(Integer, default=1)
    dry_run = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(Integer, nullable=False)
    __table_args__ = (CheckConstraint("severity IN ('low','medium','critical')"),)

class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True)
    action_id = Column(String, ForeignKey("registered_actions.id"), nullable=False)
    camera_id = Column(String, nullable=False)
    ts = Column(Integer, nullable=False, index=True)
    severity = Column(String, nullable=False)
    status = Column(String, default='new')
    snapshot_path = Column(String)
    track_id = Column(String)
    identity_id = Column(Integer)
    identity_score = Column(Float)
    details_json = Column(String)
    incident_id = Column(String)
    latency_ms = Column(Integer)
    __table_args__ = (CheckConstraint("status IN ('new','acknowledged','false_alarm')"),)

class Clip(Base):
    __tablename__ = "clips"
    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    camera_id = Column(String, nullable=False)
    start_ts = Column(Integer, nullable=False)
    end_ts = Column(Integer)
    path = Column(String)
    size_bytes = Column(Integer)
    sha256 = Column(String)
    state = Column(String, default='recording')
    pinned = Column(Integer, default=0)
    retention_until = Column(Integer)
    meta_path = Column(String)
    __table_args__ = (CheckConstraint("state IN ('recording','finalizing','ready','failed')"),)

class Identity(Base):
    __tablename__ = "identities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cls = Column(String, nullable=False)
    status = Column(String, nullable=False)
    label = Column(String)
    first_seen = Column(Integer)
    last_seen = Column(Integer)
    sightings = Column(Integer, default=0)
    plate = Column(String)
    __table_args__ = (CheckConstraint("status IN ('tentative','confirmed')"),)

class IdentityEmbedding(Base):
    __tablename__ = "identity_embeddings"
    id = Column(Integer, primary_key=True)
    identity_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    vector = Column(String, nullable=False)  # SQLite does not have BLOB type cleanly without type decorators, let's use String/BLOB. Wait, SQLAlchemy has LargeBinary
    quality = Column(Float)
    camera_id = Column(String)
    ts = Column(Integer)

from sqlalchemy import LargeBinary
IdentityEmbedding.__table__.columns['vector'].type = LargeBinary()

class Sighting(Base):
    __tablename__ = "sightings"
    id = Column(Integer, primary_key=True)
    identity_id = Column(Integer, ForeignKey("identities.id"))
    camera_id = Column(String)
    track_id = Column(String)
    start_ts = Column(Integer)
    end_ts = Column(Integer)
    score = Column(Float)
    top3_json = Column(String)

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True)
    identity_id = Column(Integer)
    start_ts = Column(Integer)
    end_ts = Column(Integer)
    summary = Column(String)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True)
    event_id = Column(String)
    kind = Column(String, nullable=False)
    ts = Column(Integer)
    message = Column(String)
    delivered = Column(Integer, default=0)

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    ts = Column(Integer, nullable=False)
    user_id = Column(Integer)
    action = Column(String, nullable=False)
    target = Column(String)
    detail = Column(String)

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String)
