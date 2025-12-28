"""
Migration script to add case management columns to consultations table
"""
from sqlalchemy import create_engine, text
from database import DATABASE_URL

def migrate():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add status column
            print("Adding status column...")
            conn.execute(text("""
                ALTER TABLE consultations 
                ADD COLUMN status ENUM('pending', 'under_supervision', 'solved') 
                DEFAULT 'pending' AFTER recommended_specialization
            """))
            conn.commit()
            print("✓ Status column added")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ Status column already exists")
            else:
                print(f"✗ Error adding status column: {e}")
        
        try:
            # Add supervising_admin_id column
            print("Adding supervising_admin_id column...")
            conn.execute(text("""
                ALTER TABLE consultations 
                ADD COLUMN supervising_admin_id INT NULL AFTER status,
                ADD CONSTRAINT fk_supervising_admin 
                FOREIGN KEY (supervising_admin_id) REFERENCES users(id)
            """))
            conn.commit()
            print("✓ Supervising_admin_id column added")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ Supervising_admin_id column already exists")
            else:
                print(f"✗ Error adding supervising_admin_id column: {e}")
        
        try:
            # Add supervision_notes column
            print("Adding supervision_notes column...")
            conn.execute(text("""
                ALTER TABLE consultations 
                ADD COLUMN supervision_notes TEXT NULL AFTER supervising_admin_id
            """))
            conn.commit()
            print("✓ Supervision_notes column added")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ Supervision_notes column already exists")
            else:
                print(f"✗ Error adding supervision_notes column: {e}")
        
        print("\n✅ Migration completed successfully!")
        print("\nNew features:")
        print("- Case status tracking (pending → under_supervision → solved)")
        print("- Hospital supervision tracking")
        print("- Resolution notes")

if __name__ == "__main__":
    print("🔄 Starting migration: Add case management columns\n")
    migrate()
