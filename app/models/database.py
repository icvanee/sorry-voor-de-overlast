import sqlite3
import os
from flask import current_app
from datetime import datetime
from config import Config

def get_db_connection():
    """Get a database connection based on configuration."""
    try:
        if Config.DB_TYPE == 'postgresql':
            import psycopg2
            import psycopg2.extras
            
            conn = psycopg2.connect(
                host=Config.DB_CONFIG['host'],
                port=Config.DB_CONFIG['port'],
                database=Config.DB_CONFIG['database'],
                user=Config.DB_CONFIG['user'],
                password=Config.DB_CONFIG['password']
            )
            conn.cursor_factory = psycopg2.extras.RealDictCursor
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
        # PostgreSQL syntax
        players_sql = '''
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                email VARCHAR(255),
                phone VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        
        matches_sql = '''
            CREATE TABLE IF NOT EXISTS matches (
                id SERIAL PRIMARY KEY,
                match_date DATE NOT NULL,
                opponent VARCHAR(255) NOT NULL,
                location VARCHAR(255),
                is_home BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        
        planning_versions_sql = '''
            CREATE TABLE IF NOT EXISTS planning_versions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT false,
                deleted_at TIMESTAMP NULL
            )
        '''
    else:
        # SQLite syntax
        players_sql = '''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT,
                phone TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        '''
        
        matches_sql = '''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_date DATE NOT NULL,
                opponent TEXT NOT NULL,
                location TEXT,
                is_home BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        '''
        
        planning_versions_sql = '''
            CREATE TABLE IF NOT EXISTS planning_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 0,
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
                version_id INTEGER REFERENCES planning_versions(id),
                match_id INTEGER REFERENCES matches(id),
                player1_id INTEGER REFERENCES players(id),
                player2_id INTEGER REFERENCES players(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_availability (
                id SERIAL PRIMARY KEY,
                player_id INTEGER REFERENCES players(id),
                match_id INTEGER REFERENCES matches(id),
                available BOOLEAN DEFAULT true,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        # SQLite syntax for additional tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_planning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id INTEGER,
                match_id INTEGER,
                player1_id INTEGER,
                player2_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (version_id) REFERENCES planning_versions(id),
                FOREIGN KEY (match_id) REFERENCES matches(id),
                FOREIGN KEY (player1_id) REFERENCES players(id),
                FOREIGN KEY (player2_id) REFERENCES players(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER,
                match_id INTEGER,
                available BOOLEAN DEFAULT 1,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id),
                FOREIGN KEY (match_id) REFERENCES matches(id)
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
    
    # Initial players from the team
    players = [
        ('Bea Brummel', 'bea@example.com', '06-12345678'),
        ('Dion Nijland', 'dion@example.com', '06-12345679'),
        ('Anita Boomgaard-de Groot', 'anita@example.com', '06-12345680'),
        ('Dirk Boomgaard', 'dirk@example.com', '06-12345681'),
        ('Iwan van Ee', 'iwan@example.com', '06-12345682'),
        ('Jaap Draaijer', 'jaap@example.com', '06-12345683'),
        ('Marise Draaijer-Holierhoek', 'marise@example.com', '06-12345684'),
        ('Ruben Brem', 'ruben@example.com', '06-12345685')
    ]
    
    # Insert players based on database type
    if Config.DB_TYPE == 'postgresql':
        for name, email, phone in players:
            cursor.execute('''
                INSERT INTO players (name, email, phone) VALUES (%s, %s, %s) 
                ON CONFLICT (name) DO NOTHING
            ''', (name, email, phone))
    else:
        for name, email, phone in players:
            cursor.execute('''
                INSERT OR IGNORE INTO players (name, email, phone) VALUES (?, ?, ?)
            ''', (name, email, phone))
    
    conn.commit()
    if Config.DB_TYPE == 'postgresql':
        cursor.close()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_initial_data()
    print("Database initialized with team data!")
