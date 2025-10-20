import sys
import os
import argparse
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.admin import Admin
from app.core.security import get_password_hash

def create_superuser(args):
    db: Session = SessionLocal()
    
    # Check if an admin user already exists
    if db.query(Admin).filter(Admin.username == args.username).first():
        print(f"User with username '{args.username}' already exists. Aborting.")
        db.close()
        return
        
    if db.query(Admin).filter(Admin.email == args.email).first():
        print(f"User with email '{args.email}' already exists. Aborting.")
        db.close()
        return

    print(f"Creating superuser '{args.username}'...")
    
    hashed_password = get_password_hash(args.password)
    
    superuser = Admin(
        username=args.username,
        email=args.email,
        hashed_password=hashed_password,
        full_name=args.full_name,
        is_active=True
    )
    
    db.add(superuser)
    db.commit()
    db.refresh(superuser)
    
    print(f"Superuser '{args.username}' created successfully.")
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new superuser.")
    parser.add_argument("--username", type=str, required=True, help="Username for the new superuser.")
    parser.add_argument("--email", type=str, required=True, help="Email for the new superuser.")
    parser.add_argument("--password", type=str, required=True, help="Password for the new superuser.")
    parser.add_argument("--full-name", type=str, default="", help="Full name for the new superuser (optional).")
    
    args = parser.parse_args()
    create_superuser(args)