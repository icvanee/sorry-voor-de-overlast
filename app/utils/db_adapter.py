"""
Database adapter voor zowel SQLite als PostgreSQL support
"""
import sqlite3
from config import Config

def get_db_connection():
    """Get database connection based on configuration"""
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
        conn.row_factory = psycopg2.extras.RealDictCursor
        return conn
    else:
        # SQLite
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(query, params=None, fetch=False):
    """Execute database query with proper connection handling"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            if Config.DB_TYPE == 'postgresql':
                result = cursor.fetchall()
                return [dict(row) for row in result]
            else:
                return [dict(row) for row in cursor.fetchall()]
        else:
            conn.commit()
            return cursor.rowcount
    finally:
        conn.close()

def get_database_info():
    """Get database connection information for external access"""
    if Config.DB_TYPE == 'postgresql':
        return {
            'type': 'PostgreSQL',
            'host': Config.DB_CONFIG['host'],
            'port': Config.DB_CONFIG['port'],
            'database': Config.DB_CONFIG['database'],
            'user': Config.DB_CONFIG['user'],
            'dbeaver_url': f"postgresql://{Config.DB_CONFIG['host']}:{Config.DB_CONFIG['port']}/{Config.DB_CONFIG['database']}"
        }
    else:
        return {
            'type': 'SQLite',
            'path': Config.DATABASE_PATH,
            'dbeaver_url': 'Not accessible externally (file-based)'
        }
