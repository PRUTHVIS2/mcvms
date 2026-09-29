import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class ThresholdsConfig(BaseModel):
    min_confidence: float = 0.6
    min_box_px: int = 60
    margin_frac: float = 0.05
    match_threshold: float = 0.85
    min_crops_confirm: int = 20

class AppConfig(BaseModel):
    analysis_fps: float = 8.0
    timezone: str = "UTC"
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    gallery_policy: str = "persistent"

class DiskConfig(BaseModel):
    total_disk_gb: int = 500
    reserve_gb: int = 50
    warn_at_percent: int = 80
    emergency_at_percent: int = 90

class PathsConfig(BaseModel):
    continuous: str = "data/continuous"
    clips: str = "data/clips"
    snapshots: str = "data/snapshots"

class ContinuousConfig(BaseModel):
    hours: int = 24
    segment_seconds: int = 10
    container: str = "mkv"
    copy_codec: bool = True
    keyframe_interval_hint_s: int = 1
    restart_backoff_s: list[int] = [1, 2, 4, 8, 30]

class SeverityMinutes(BaseModel):
    low: int = 15
    medium: int = 30
    critical: int = 60

class ClipsConfig(BaseModel):
    pre_roll_seconds: int = 15
    hold_seconds: int = 20
    extend_on_refire: bool = True
    max_clip_minutes: int = 120
    severity_default_minutes: SeverityMinutes = Field(default_factory=SeverityMinutes)
    admin_can_extend: bool = True
    container: str = "mkv"
    compute_sha256: bool = True
    sidecar_metadata: bool = True

class RetentionConfig(BaseModel):
    low: int = 14
    medium: int = 60
    critical: int = 0
    pinned_never_deleted: bool = True
    run_at: str = "03:30"

class StoragePolicy(BaseModel):
    disk: DiskConfig = Field(default_factory=DiskConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    continuous: ContinuousConfig = Field(default_factory=ContinuousConfig)
    clips: ClipsConfig = Field(default_factory=ClipsConfig)
    retention: RetentionConfig = Field(default_factory=RetentionConfig)

class Settings(BaseSettings):
    app_config: AppConfig
    storage_policy: StoragePolicy
    secret_key: str = "supersecretkey_change_in_production"

def load_yaml_config(file_path: Path, model_cls):
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")
    with open(file_path, "r") as f:
        data = yaml.safe_load(f) or {}
    return model_cls(**data)

def load_settings() -> Settings:
    base_dir = Path(__file__).resolve().parent.parent.parent
    app_path = base_dir / "config" / "app.yaml"
    storage_path = base_dir / "config" / "storage_policy.yaml"
    
    app_config = load_yaml_config(app_path, AppConfig)
    storage_policy = load_yaml_config(storage_path, StoragePolicy)
    
    # Resolve paths absolutely against base_dir so they work from any cwd
    storage_policy.paths.continuous = str((base_dir / storage_policy.paths.continuous).resolve())
    storage_policy.paths.clips = str((base_dir / storage_policy.paths.clips).resolve())
    storage_policy.paths.snapshots = str((base_dir / storage_policy.paths.snapshots).resolve())
    
    return Settings(app_config=app_config, storage_policy=storage_policy)

settings = load_settings()
