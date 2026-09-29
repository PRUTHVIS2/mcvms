from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.auth import verify_password, create_access_token, get_current_user, role_required
from app.audit import log_audit
from app.config import settings

app = FastAPI(title="MCVMS API")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "timezone": settings.app_config.timezone}

@app.post("/api/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        log_audit(db, user_id=None, action="login_failed", target=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.enabled == 0:
        log_audit(db, user_id=user.id, action="login_failed", target="disabled_account")
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    log_audit(db, user_id=user.id, action="login_success")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/cameras")
def create_camera(
    db: Session = Depends(get_db), 
    current_user: User = Depends(role_required(["owner", "admin"]))
):
    """
    Placeholder endpoint to demonstrate role restriction.
    Only owner and admin can create a camera. Incharge cannot.
    """
    log_audit(db, user_id=current_user.id, action="create_camera", target="new_camera")
    return {"status": "camera_created"}
