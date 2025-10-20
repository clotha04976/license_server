import sys
import os
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.admin import Admin
from app.core.security import get_password_hash

def reset_admin_password():
    db: Session = SessionLocal()
    
    print("--- Reset Admin Password ---")
    
    username = input("Enter the username of the admin to reset: ")
    
    admin = db.query(Admin).filter(Admin.username == username).first()
    
    if not admin:
        print(f"Error: Admin with username '{username}' not found.")
        db.close()
        return

    new_password = input(f"Enter new password for '{username}': ")
    
    if not new_password:
        print("Password cannot be empty. Aborting.")
        db.close()
        return

    hashed_password = get_password_hash(new_password)
    admin.hashed_password = hashed_password
    
    db.add(admin)
    db.commit()
    
    print(f"Password for admin '{username}' has been reset successfully.")
    db.close()

if __name__ == "__main__":
    reset_admin_password()