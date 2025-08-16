import sqlite3
import psycopg
from flask import current_app
from datetime import datetime
from config import Config
import os

def get_placeholder():
    """Get the correct parameter placeholder for the current database type."""
    return '%s' if Config.DB_TYPE == 'postgresql' else '?'

def format_query(query):
    """Convert PostgreSQL-style query to SQLite if needed."""
    if Config.DB_TYPE == 'sqlite':
        # Convert %s to ? for SQLite
        return query.replace('%s', '?')
    return query

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