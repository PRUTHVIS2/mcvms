import argparse
import time
from app.db.session import SessionLocal
from app.db.models import User
from app.auth import get_password_hash

def seed_owner(username, password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            print(f"User '{username}' already exists.")
            return
        
        hashed_pw = get_password_hash(password)
        new_user = User(
            username=username,
            password_hash=hashed_pw,
            role="owner",
            enabled=1,
            created_at=int(time.time() * 1000)
        )
        db.add(new_user)
        db.commit()
        print(f"Owner user '{username}' created successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed initial owner user")
    parser.add_argument("--username", required=True, help="Username for the owner")
    parser.add_argument("--password", required=True, help="Password for the owner")
    args = parser.parse_args()
    seed_owner(args.username, args.password)
