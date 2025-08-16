import sqlite3
import psycopg
import os
from flask import current_app
from datetime import datetime
from config import Config

def get_db_connection():
    """Get a database connection based on configuration."""
    try:
        if Config.DB_TYPE == 'postgresql':
            # PostgreSQL connection with psycopg3
            conn_str = f"host={Config.DB_CONFIG['host']} port={Config.DB_CONFIG['port']} dbname={Config.DB_CONFIG['database']} user={Config.DB_CONFIG['user']} password={Config.DB_CONFIG['password']}"
            conn = psycopg.connect(conn_str, row_factory=psycopg.rows.dict_row)
            return conn
        else:
            # SQLite fallback
            conn = sqlite3.connect(Config.DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        # Fallback to SQLite if PostgreSQL fails
        if hasattr(Config, 'DATABASE_PATH') and Config.DATABASE_PATH:
            conn = sqlite3.connect(Config.DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            return conn
        else:
            # Emergency fallback
            conn = sqlite3.connect('/tmp/emergency.db')
            conn.row_factory = sqlite3.Row
            return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # SQL statements based on database type
    if Config.DB_TYPE == 'postgresql':
        # PostgreSQL syntax - Enhanced schema with planning features
        players_sql = '''
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                email VARCHAR(255),
                phone VARCHAR(50),
                role VARCHAR(100) DEFAULT '',
                is_active BOOLEAN DEFAULT true,
                partner_id INTEGER,
                prefer_partner_together BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES players(id)
            )
        '''
        
        matches_sql = '''
            CREATE TABLE IF NOT EXISTS matches (
                id SERIAL PRIMARY KEY,
                match_number VARCHAR(50),
                match_date DATE,
                date TEXT,
                home_team VARCHAR(255),
                away_team VARCHAR(255),
                opponent VARCHAR(255),
                location VARCHAR(255),
                venue VARCHAR(255) DEFAULT '',
                time VARCHAR(20) DEFAULT '',
                competition VARCHAR(255) DEFAULT '',
                is_home BOOLEAN DEFAULT true,
                is_friendly BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        
        planning_versions_sql = '''
            CREATE TABLE IF NOT EXISTS planning_versions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT false,
                is_final BOOLEAN DEFAULT false,
                deleted_at TIMESTAMP NULL
            )
        '''
    else:
        # SQLite syntax - Enhanced schema with planning features
        players_sql = '''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT,
                phone TEXT,
                role TEXT DEFAULT '',
                is_active BOOLEAN DEFAULT 1,
                partner_id INTEGER,
                prefer_partner_together BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES players(id)
            )
        '''
        
        matches_sql = '''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_number TEXT,
                match_date DATE,
                date TEXT,
                home_team TEXT,
                away_team TEXT,
                opponent TEXT,
                location TEXT,
                venue TEXT DEFAULT '',
                time TEXT DEFAULT '',
                competition TEXT DEFAULT '',
                is_home BOOLEAN DEFAULT 1,
                is_friendly BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        '''
        
        planning_versions_sql = '''
            CREATE TABLE IF NOT EXISTS planning_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 0,
                is_final BOOLEAN DEFAULT 0,
                deleted_at DATETIME NULL
            )
        '''
    
    # Create players table
    cursor.execute(players_sql)
    
    # Create matches table
    cursor.execute(matches_sql)
    
    # Create planning_versions table
    cursor.execute(planning_versions_sql)
    
    # Additional tables (database-agnostic approach)
    if Config.DB_TYPE == 'postgresql':
        # PostgreSQL syntax for additional tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_planning (
                id SERIAL PRIMARY KEY,
                planning_version_id INTEGER REFERENCES planning_versions(id),
                match_id INTEGER REFERENCES matches(id),
                player_id INTEGER REFERENCES players(id),
                is_confirmed BOOLEAN DEFAULT false,
                actually_played BOOLEAN DEFAULT false,
                is_pinned BOOLEAN DEFAULT false,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(planning_version_id, match_id, player_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_availability (
                id SERIAL PRIMARY KEY,
                player_id INTEGER REFERENCES players(id),
                match_id INTEGER REFERENCES matches(id),
                is_available BOOLEAN DEFAULT true,
                available BOOLEAN DEFAULT true,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id, match_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_preferences (
                id SERIAL PRIMARY KEY,
                player_id INTEGER REFERENCES players(id),
                preference_type VARCHAR(255) NOT NULL,
                preference_value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_preferences (
                id SERIAL PRIMARY KEY,
                player_id INTEGER REFERENCES players(id),
                partner_id INTEGER REFERENCES players(id),
                match_id INTEGER REFERENCES matches(id),
                prefer_together BOOLEAN DEFAULT true,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id, partner_id, match_id)
            )
        ''')
    else:
        # SQLite syntax for additional tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_planning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                planning_version_id INTEGER NOT NULL,
                match_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                is_confirmed BOOLEAN DEFAULT 0,
                actually_played BOOLEAN DEFAULT 0,
                is_pinned BOOLEAN DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (planning_version_id) REFERENCES planning_versions(id),
                FOREIGN KEY (match_id) REFERENCES matches(id),
                FOREIGN KEY (player_id) REFERENCES players(id),
                UNIQUE(planning_version_id, match_id, player_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                match_id INTEGER NOT NULL,
                is_available BOOLEAN NOT NULL,
                available BOOLEAN DEFAULT 1,
                notes TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id),
                FOREIGN KEY (match_id) REFERENCES matches(id),
                UNIQUE(player_id, match_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                preference_type TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                partner_id INTEGER NOT NULL,
                match_id INTEGER,
                prefer_together BOOLEAN DEFAULT 1,
                notes TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id),
                FOREIGN KEY (partner_id) REFERENCES players(id),
                FOREIGN KEY (match_id) REFERENCES matches(id),
                UNIQUE(player_id, partner_id, match_id)
            )
        ''')
    
    # Commit changes and close connection
    conn.commit()
    if Config.DB_TYPE == 'postgresql':
        cursor.close()
    conn.close()
    print(f"Database initialized successfully with {Config.DB_TYPE}")

def seed_initial_data():
    """Seed the database with initial team data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Initial players from the team with roles
    players = [
        ('Bea Brummel', 'bea@example.com', '06-12345678', 'Speler'),
        ('Dion Nijland', 'dion@example.com', '06-12345679', 'Speler'),
        ('Anita Boomgaard-de Groot', 'anita@example.com', '06-12345680', 'Speler'),
        ('Dirk Boomgaard', 'dirk@example.com', '06-12345681', 'Speler'),
        ('Iwan van Ee', 'iwan@example.com', '06-12345682', 'Speler'),
        ('Jaap Draaijer', 'jaap@example.com', '06-12345683', 'Speler'),
        ('Marise Draaijer-Holierhoek', 'marise@example.com', '06-12345684', 'Speler'),
        ('Ruben Brem', 'ruben@example.com', '06-12345685', 'Speler')
    ]
    
    # Insert players based on database type
    if Config.DB_TYPE == 'postgresql':
        for name, email, phone, role in players:
            cursor.execute('''
                INSERT INTO players (name, email, phone, role) VALUES (%s, %s, %s, %s) 
                ON CONFLICT (name) DO UPDATE SET email = EXCLUDED.email, phone = EXCLUDED.phone, role = EXCLUDED.role
            ''', (name, email, phone, role))
    else:
        for name, email, phone, role in players:
            cursor.execute('''
                INSERT OR REPLACE INTO players (name, email, phone, role) VALUES (?, ?, ?, ?)
            ''', (name, email, phone, role))
    
    # Set up partner relationships
    try:
        if Config.DB_TYPE == 'postgresql':
            # Anita en Dirk Boomgaard zijn partners
            cursor.execute('SELECT id FROM players WHERE name = %s', ('Anita Boomgaard-de Groot',))
            anita_id = cursor.fetchone()
            cursor.execute('SELECT id FROM players WHERE name = %s', ('Dirk Boomgaard',))
            dirk_id = cursor.fetchone()
            
            if anita_id and dirk_id:
                cursor.execute('UPDATE players SET partner_id = %s WHERE id = %s', (dirk_id[0], anita_id[0]))
                cursor.execute('UPDATE players SET partner_id = %s WHERE id = %s', (anita_id[0], dirk_id[0]))
            
            # Jaap en Marise Draaijer zijn partners
            cursor.execute('SELECT id FROM players WHERE name = %s', ('Jaap Draaijer',))
            jaap_id = cursor.fetchone()
            cursor.execute('SELECT id FROM players WHERE name = %s', ('Marise Draaijer-Holierhoek',))
            marise_id = cursor.fetchone()
            
            if jaap_id and marise_id:
                cursor.execute('UPDATE players SET partner_id = %s WHERE id = %s', (marise_id[0], jaap_id[0]))
                cursor.execute('UPDATE players SET partner_id = %s WHERE id = %s', (jaap_id[0], marise_id[0]))
        else:
            # SQLite version
            cursor.execute('SELECT id FROM players WHERE name = ?', ('Anita Boomgaard-de Groot',))
            anita_id = cursor.fetchone()
            cursor.execute('SELECT id FROM players WHERE name = ?', ('Dirk Boomgaard',))
            dirk_id = cursor.fetchone()
            
            if anita_id and dirk_id:
                cursor.execute('UPDATE players SET partner_id = ? WHERE id = ?', (dirk_id[0], anita_id[0]))
                cursor.execute('UPDATE players SET partner_id = ? WHERE id = ?', (anita_id[0], dirk_id[0]))
            
            cursor.execute('SELECT id FROM players WHERE name = ?', ('Jaap Draaijer',))
            jaap_id = cursor.fetchone()
            cursor.execute('SELECT id FROM players WHERE name = ?', ('Marise Draaijer-Holierhoek',))
            marise_id = cursor.fetchone()
            
            if jaap_id and marise_id:
                cursor.execute('UPDATE players SET partner_id = ? WHERE id = ?', (marise_id[0], jaap_id[0]))
                cursor.execute('UPDATE players SET partner_id = ? WHERE id = ?', (jaap_id[0], marise_id[0]))
                
    except Exception as e:
        print(f"Note: Could not set partner relationships: {e}")
    
    conn.commit()
    if Config.DB_TYPE == 'postgresql':
        cursor.close()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_initial_data()
    print("Database initialized with team data!")
