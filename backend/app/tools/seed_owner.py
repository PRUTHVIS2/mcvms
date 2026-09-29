import argparse
import time
from app.db.session import SessionLocal
from app.db.models import User
from app.auth import get_password_hash

def seed_owner(username, password, role="owner"):
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
            role=role,
            enabled=1,
            created_at=int(time.time() * 1000)
        )
        db.add(new_user)
        db.commit()
        print(f"User '{username}' with role '{role}' created successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed initial user")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--role", choices=["owner", "admin", "incharge"], default="owner", help="Role of the user (owner, admin, incharge)")
    args = parser.parse_args()
    seed_owner(args.username, args.password, args.role)
