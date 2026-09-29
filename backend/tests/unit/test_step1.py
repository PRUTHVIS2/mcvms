import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import get_db
from app.db.models import User, AuditLog, Base
from app.auth import get_password_hash
from app.config import load_yaml_config, AppConfig
from pydantic import ValidationError
import time
from sqlalchemy.pool import StaticPool

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Seed owner
    db.add(User(username="owner", password_hash=get_password_hash("pass"), role="owner", created_at=int(time.time()*1000)))
    # Seed incharge
    db.add(User(username="incharge", password_hash=get_password_hash("pass"), role="incharge", created_at=int(time.time()*1000)))
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(setup_db):
    return TestClient(app)

def test_bad_yaml_rejected(tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("analysis_fps: 'not_a_float'\ntimezone: UTC")
    with pytest.raises(ValidationError):
        load_yaml_config(bad_yaml, AppConfig)

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200

def test_login_success(client):
    response = client.post("/api/token", data={"username": "owner", "password": "pass"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Verify audit log
    db = TestingSessionLocal()
    audit = db.query(AuditLog).filter(AuditLog.action == "login_success").first()
    assert audit is not None
    db.close()

def test_login_fail(client):
    response = client.post("/api/token", data={"username": "owner", "password": "wrong"})
    assert response.status_code == 401
    
    # Verify audit log
    db = TestingSessionLocal()
    audit = db.query(AuditLog).filter(AuditLog.action == "login_failed").first()
    assert audit is not None
    db.close()

def test_incharge_cannot_create_camera(client):
    # Log in as incharge
    response = client.post("/api/token", data={"username": "incharge", "password": "pass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Try to create camera
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/cameras", headers=headers)
    assert response.status_code == 403
    assert "Operation not permitted" in response.json()["detail"]

def test_owner_can_create_camera(client):
    # Log in as owner
    response = client.post("/api/token", data={"username": "owner", "password": "pass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Try to create camera
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/cameras", headers=headers)
    assert response.status_code == 200
