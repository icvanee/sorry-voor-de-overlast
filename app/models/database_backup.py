import sqlite3
import psycopg
from flask import current_app
from datetime import datetime
from config import Config
import os

def get_db_connection():
    """Get a database connection (SQLite or PostgreSQL)."""
    try:
        if Config.DB_TYPE == 'postgresql':
            # PostgreSQL connection with psycopg3
            conn_str = f"host={Config.DB_CONFIG['host']} port={Config.DB_CONFIG['port']} dbname={Config.DB_CONFIG['database']} user={Config.DB_CONFIG['user']} password={Config.DB_CONFIG['password']}"
            conn = psycopg.connect(conn_str, row_factory=psycopg.rows.dict_row)
            return conn
        else:
            # SQLite connection
            conn = sqlite3.connect(Config.DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if Config.DB_TYPE == 'postgresql':
            # PostgreSQL syntax - Enhanced schema with planning features
            create_tables_postgresql(cursor)
        else:
            # SQLite syntax - Enhanced schema with planning features
            create_tables_sqlite(cursor)
            
        conn.commit()
        print("✅ Database tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def create_tables_sqlite(cursor):
    """Create tables for SQLite database."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            role TEXT DEFAULT 'speler',
            partner_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
            prefer_partner_together INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            match_date TEXT NOT NULL,
            match_time TEXT,
            location TEXT,
            is_home INTEGER NOT NULL,
            is_cup_match INTEGER DEFAULT 0,
            round_name TEXT,
            opponent TEXT,
            result TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS planning_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            is_final INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_planning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            planning_version_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            role TEXT DEFAULT 'speler',
            is_confirmed INTEGER DEFAULT 0,
            played INTEGER DEFAULT 0,
            pinned INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (planning_version_id) REFERENCES planning_versions(id) ON DELETE CASCADE,
            FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            UNIQUE(planning_version_id, match_id, player_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            is_available INTEGER DEFAULT 1,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
            UNIQUE(player_id, match_id)
        )
    ''')

def create_tables_postgresql(cursor):
    """Create tables for PostgreSQL database."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255),
            phone VARCHAR(20),
            role VARCHAR(50) DEFAULT 'speler',
            partner_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
            prefer_partner_together BOOLEAN DEFAULT true,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
            planning_version_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            role VARCHAR(50) DEFAULT 'speler',
            is_confirmed BOOLEAN DEFAULT false,
            played BOOLEAN DEFAULT false,
            pinned BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (planning_version_id) REFERENCES planning_versions(id) ON DELETE CASCADE,
            FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            UNIQUE(planning_version_id, match_id, player_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_availability (
            id SERIAL PRIMARY KEY,
            player_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            is_available BOOLEAN DEFAULT true,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
            FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
            UNIQUE(player_id, match_id)
        )
    ''')
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        cursor.close()
        conn.close()
        raise

def seed_initial_data():
    """Seed the database with initial data for development/testing."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if we already have data
        cursor.execute("SELECT COUNT(*) as count FROM players")
        player_count = cursor.fetchone()['count']
        
        if player_count == 0:
            print("Seeding initial players...")
            
            # Add some initial players
            initial_players = [
                ('John Doe', 'john@example.com', '+31612345678', 'speler'),
                ('Jane Smith', 'jane@example.com', '+31687654321', 'captain'),
                ('Bob Johnson', 'bob@example.com', '+31656789123', 'speler'),
                ('Alice Brown', 'alice@example.com', '+31645123789', 'speler'),
                ('Charlie Wilson', 'charlie@example.com', '+31634567890', 'speler'),
                ('Diana Davis', 'diana@example.com', '+31623456789', 'speler'),
            ]
            
            for name, email, phone, role in initial_players:
                cursor.execute('''
                    INSERT INTO players (name, email, phone, role)
                    VALUES (%s, %s, %s, %s)
                ''', (name, email, phone, role))
        
        # Check if we have a default planning version
        cursor.execute("SELECT COUNT(*) as count FROM planning_versions")
        version_count = cursor.fetchone()['count']
        
        if version_count == 0:
            print("Creating default planning version...")
            cursor.execute('''
                INSERT INTO planning_versions (name, description, is_final)
                VALUES (%s, %s, %s)
            ''', ('Definitieve Planning', 'De definitieve teamplanning voor het seizoen', True))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database seeded successfully")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        cursor.close()
        conn.close()
        raise

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
        seed_initial_data()
        
        print("Database reset successfully")
        
    except Exception as e:
        print(f"Error resetting database: {e}")
        cursor.close()
        conn.close()
        raise

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    seed_initial_data()
    print("Database setup complete!")
