#!/usr/bin/env python3
"""
Database initialization script for Railway deployment
This script ensures the database is properly initialized on first run
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def ensure_database():
    """Ensure database exists and is initialized"""
    try:
        from config import Config
        from app.models.database import init_database
        
        # Create database directory if it doesn't exist
        db_path = Path(Config.DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if database exists and has tables
        if not db_path.exists() or not has_tables(str(db_path)):
            print("Initializing database...")
            init_database()
            print("Database initialized successfully!")
        else:
            print("Database already exists and is initialized.")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Don't exit on Railway - just log the error
        return False
    
    return True

def has_tables(db_path):
    """Check if database has the required tables"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for essential tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players'")
        has_players = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches'")
        has_matches = cursor.fetchone() is not None
        
        conn.close()
        return has_players and has_matches
        
    except Exception:
        return False

if __name__ == "__main__":
    ensure_database()
