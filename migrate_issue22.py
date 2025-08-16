"""
Database migration for Issue #22 - Single Planning System
Adds is_played column to matches table if it doesn't exist.
"""
from app.models.database import get_db_connection

def migrate_database():
    """Add missing columns for Issue #22."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if is_played column exists in matches table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'matches' AND column_name = 'is_played'
        """)
        
        if not cursor.fetchone():
            print("Adding is_played column to matches table...")
            cursor.execute("""
                ALTER TABLE matches 
                ADD COLUMN is_played BOOLEAN DEFAULT false
            """)
            print("✅ Added is_played column to matches table")
        else:
            print("✅ is_played column already exists in matches table")
        
        # Ensure single planning version exists
        cursor.execute("SELECT id FROM planning_versions WHERE id = 1")
        version = cursor.fetchone()
        
        if not version:
            print("Creating single planning version...")
            cursor.execute("""
                INSERT INTO planning_versions (id, name, description, is_final, created_at)
                VALUES (1, 'Master Planning', 'Single unified planning for all matches', false, CURRENT_TIMESTAMP)
            """)
            print("✅ Created single planning version (ID=1)")
        else:
            print("✅ Single planning version already exists")
        
        conn.commit()
        print("\n🎉 Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
        raise
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🔄 Running Issue #22 database migration...")
    migrate_database()
