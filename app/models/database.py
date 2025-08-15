import sqlite3
import os
from flask import current_app
from datetime import datetime

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(current_app.config['DATABASE_PATH'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create players table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            role TEXT DEFAULT '',
            is_active BOOLEAN DEFAULT TRUE,
            partner_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partner_id) REFERENCES players (id)
        )
    ''')
    
    # Create matches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_number TEXT,
            date TEXT NOT NULL,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            is_home BOOLEAN NOT NULL,
            is_friendly BOOLEAN DEFAULT FALSE,
            venue TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create planning_versions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS planning_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            is_final BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create match_planning table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_planning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            planning_version_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            is_confirmed BOOLEAN DEFAULT FALSE,
            actually_played BOOLEAN DEFAULT FALSE,
            notes TEXT DEFAULT '',
            FOREIGN KEY (planning_version_id) REFERENCES planning_versions (id),
            FOREIGN KEY (match_id) REFERENCES matches (id),
            FOREIGN KEY (player_id) REFERENCES players (id),
            UNIQUE(planning_version_id, match_id, player_id)
        )
    ''')
    
    # Create player_availability table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            is_available BOOLEAN NOT NULL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id),
            FOREIGN KEY (match_id) REFERENCES matches (id),
            UNIQUE(player_id, match_id)
        )
    ''')
    
    # Create player_preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            preference_type TEXT NOT NULL,
            preference_value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')
    
    # Add soft delete column to planning_versions if it doesn't exist
    try:
        cursor.execute('ALTER TABLE planning_versions ADD COLUMN deleted_at TIMESTAMP NULL')
    except Exception:
        # Column already exists, ignore
        pass
    
    # Add active planning column to planning_versions if it doesn't exist
    try:
        cursor.execute('ALTER TABLE planning_versions ADD COLUMN is_active BOOLEAN DEFAULT FALSE')
    except Exception:
        # Column already exists, ignore
        pass
    
    conn.commit()
    conn.close()

def seed_initial_data():
    """Seed the database with initial team data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Initial players from the team
    players = [
        ('Bea Brummel', 'C'),
        ('Dion Nijland', ''),
        ('Anita Boomgaard-de Groot', ''),
        ('Dirk Boomgaard', ''),
        ('Iwan van Ee', 'RC'),
        ('Jaap Draaijer', 'Bestuurslid'),
        ('Marise Draaijer-Holierhoek', ''),
        ('Ruben Brem', '')
    ]
    
    for name, role in players:
        cursor.execute('''
            INSERT OR IGNORE INTO players (name, role) VALUES (?, ?)
        ''', (name, role))
    
    # Set partner relationships
    # Anita en Dirk Boomgaard zijn partners
    cursor.execute('SELECT id FROM players WHERE name = ?', ('Anita Boomgaard-de Groot',))
    anita_id = cursor.fetchone()
    cursor.execute('SELECT id FROM players WHERE name = ?', ('Dirk Boomgaard',))
    dirk_id = cursor.fetchone()
    
    if anita_id and dirk_id:
        cursor.execute('UPDATE players SET partner_id = ? WHERE id = ?', (dirk_id[0], anita_id[0]))
        cursor.execute('UPDATE players SET partner_id = ? WHERE id = ?', (anita_id[0], dirk_id[0]))
    
    # Jaap en Marise Draaijer zijn partners
    cursor.execute('SELECT id FROM players WHERE name = ?', ('Jaap Draaijer',))
    jaap_id = cursor.fetchone()
    cursor.execute('SELECT id FROM players WHERE name = ?', ('Marise Draaijer-Holierhoek',))
    marise_id = cursor.fetchone()
    
    if jaap_id and marise_id:
        cursor.execute('UPDATE players SET partner_id = ? WHERE id = ?', (marise_id[0], jaap_id[0]))
        cursor.execute('UPDATE players SET partner_id = ? WHERE id = ?', (jaap_id[0], marise_id[0]))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_initial_data()
    print("Database initialized with team data!")
