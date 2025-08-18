import psycopg
from flask import current_app
from datetime import datetime
from config import Config

def get_db_connection():
    """Get a PostgreSQL database connection."""
    try:
        # PostgreSQL connection with psycopg3
        conn_str = f"host={Config.DB_CONFIG['host']} port={Config.DB_CONFIG['port']} dbname={Config.DB_CONFIG['database']} user={Config.DB_CONFIG['user']} password={Config.DB_CONFIG['password']}"
        conn = psycopg.connect(conn_str, row_factory=psycopg.rows.dict_row)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # PostgreSQL syntax - Enhanced schema with planning features
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(20),
                password_hash TEXT,
                force_password_change BOOLEAN DEFAULT false,
                role VARCHAR(50) DEFAULT 'speler',
                partner_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
                prefer_partner_together BOOLEAN DEFAULT true,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Ensure password_hash exists for older installations
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='players' AND column_name='password_hash'
                ) THEN
                    ALTER TABLE players ADD COLUMN password_hash TEXT;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='players' AND column_name='force_password_change'
                ) THEN
                    ALTER TABLE players ADD COLUMN force_password_change BOOLEAN DEFAULT false;
                END IF;
            END$$;
        """)
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id SERIAL PRIMARY KEY,
                home_team VARCHAR(200) NOT NULL,
                away_team VARCHAR(200) NOT NULL,
                match_date DATE NOT NULL,
                match_time TIME,
                location VARCHAR(200),
                is_home BOOLEAN NOT NULL,
                is_cup_match BOOLEAN DEFAULT false,
                is_played BOOLEAN DEFAULT false,
                round_name VARCHAR(50),
                opponent VARCHAR(200),
                result VARCHAR(20),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planning_versions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                is_final BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_planning (
                id SERIAL PRIMARY KEY,
                planning_version_id INTEGER REFERENCES planning_versions(id) ON DELETE CASCADE,
                match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
                player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
                is_pinned BOOLEAN DEFAULT false,
                actually_played BOOLEAN DEFAULT false,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(planning_version_id, match_id, player_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_availability (
                id SERIAL PRIMARY KEY,
                player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
                match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
                is_available BOOLEAN NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id, match_id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_players_active ON players(is_active)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_planning_versions_final ON planning_versions(is_final)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_match_planning_version ON match_planning(planning_version_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_match_planning_match ON match_planning(match_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_player_availability_player ON player_availability(player_id)
        ''')
        
        # Issue #22: Create single planning version (ID=1) for new single planning system
        print("🔧 Setting up single planning system (Issue #22)...")
        cursor.execute('''
            INSERT INTO planning_versions (id, name, description, is_final)
            VALUES (1, 'Team Planning (Single System)', 'Geïntegreerde planning met pin en regeneratie functionaliteit', false)
            ON CONFLICT (id) DO NOTHING
        ''')
        
        # Reset sequence to start from 2 for future legacy versions
        cursor.execute('''
            SELECT setval('planning_versions_id_seq', GREATEST(2, (SELECT COALESCE(MAX(id), 1) FROM planning_versions) + 1))
        ''')
        
        conn.commit()
        print("✅ Database initialized successfully with single planning system!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def seed_default_passwords(default_password: str = 'svdo@2025'):
    """Seed default passwords for any players missing a password.
    Always safe to run at startup; only updates rows where password_hash IS NULL.
    Also sets force_password_change = true so users must set a new password.
    """
    from werkzeug.security import generate_password_hash
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) AS cnt FROM players WHERE password_hash IS NULL")
        row = cur.fetchone()
        missing = (row['cnt'] or 0) if row else 0
        if missing > 0:
            print(f"🔐 Seeding default passwords for {missing} player(s)...")
            hashed = generate_password_hash(default_password)
            cur.execute(
                """
                UPDATE players
                SET password_hash = %s,
                    force_password_change = true,
                    updated_at = CURRENT_TIMESTAMP
                WHERE password_hash IS NULL
                """,
                (hashed,)
            )
            conn.commit()
            print("✅ Default passwords seeded.")
        else:
            print("Password seeding: no players missing a password.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error seeding default passwords: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def setup_single_planning():
    """Setup single planning version for Issue #22 if not exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if single planning version exists
        cursor.execute("SELECT COUNT(*) as count FROM planning_versions WHERE id = 1")
        version_count = cursor.fetchone()['count']
        
        if version_count == 0:
            print("🔧 Creating single planning system (Issue #22)...")
            
            # Create single planning version (ID=1) for new single planning system
            cursor.execute('''
                INSERT INTO planning_versions (id, name, description, is_final)
                VALUES (1, 'Team Planning (Single System)', 'Geïntegreerde planning met pin en regeneratie functionaliteit', false)
            ''')
            
            # Reset sequence to start from 2 for future legacy versions
            cursor.execute('''
                SELECT setval('planning_versions_id_seq', GREATEST(2, (SELECT COALESCE(MAX(id), 1) FROM planning_versions) + 1))
            ''')
            
            print("✅ Single planning system created!")
        else:
            print("Single planning system already exists.")
        
        conn.commit()
        
    except Exception as e:
        print(f"Error setting up single planning: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def reset_database():
    """Reset the database by dropping and recreating all tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Drop tables in reverse order due to foreign key constraints
        tables_to_drop = [
            'player_availability',
            'match_planning', 
            'planning_versions',
            'matches',
            'players'
        ]
        
        for table in tables_to_drop:
            cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Recreate tables
        init_database()
        
        print("Database reset successfully")
        
    except Exception as e:
        print(f"Error resetting database: {e}")
        cursor.close()
        conn.close()
        raise

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("Database setup complete!")
