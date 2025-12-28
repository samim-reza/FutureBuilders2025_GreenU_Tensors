#!/usr/bin/env python3
"""Create admin user for WeCare"""
from database import SessionLocal, init_db
from models import User
from auth import get_password_hash

def create_admin():
    init_db()
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("⚠️  Admin user already exists!")
            print(f"Username: admin")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@wecare.com",
            hashed_password=get_password_hash("admin123"),
            full_name="WeCare Administrator",
            phone="+880-1700-000000",
            blood_group="O+",
            is_admin=True
        )
        db.add(admin)
        db.commit()
        
        print("✅ Admin user created successfully!")
        print("\n" + "="*50)
        print("🔐 ADMIN CREDENTIALS")
        print("="*50)
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"Email: admin@wecare.com")
        print("="*50)
        print("\n⚠️  IMPORTANT: Change this password in production!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
