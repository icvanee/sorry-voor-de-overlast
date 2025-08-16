import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sorry-voor-de-overlast-secret-key-2025'
    
    # Database configuration - Railway with PostgreSQL support
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    try:
        if DATABASE_URL and (DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://')):
            # Try PostgreSQL configuration
            url = urlparse(DATABASE_URL)
            DATABASE_PATH = None  # Not used for PostgreSQL
            DB_TYPE = 'postgresql'
            DB_CONFIG = {
                'host': url.hostname,
                'port': url.port,
                'database': url.path[1:],  # Remove leading slash
                'user': url.username,
                'password': url.password
            }
            print(f"Using PostgreSQL: {url.hostname}:{url.port}/{url.path[1:]}")
        else:
            raise Exception("PostgreSQL URL not available, falling back to SQLite")
    except Exception as e:
        # Fallback to SQLite if PostgreSQL setup fails
        print(f"PostgreSQL setup failed: {e}. Using SQLite fallback.")
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            # Railway environment - use /tmp directory for SQLite fallback
            DATABASE_PATH = '/tmp/database.db'
            DB_TYPE = 'sqlite'
            DB_CONFIG = None
        else:
            # Local development
            DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'database.db')
            DB_TYPE = 'sqlite'
            DB_CONFIG = None
            # Ensure local data directory exists
            os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    TEAM_NAME = "Sorry voor de overlast"
    TEAM_URL = "https://feeds.teambeheer.nl/web/team?d=36&t=8723&s=25-26"
    VENUE = "Café De Vrijbuiter"
    VENUE_ADDRESS = "Schubertplein 12, 7333 CV Apeldoorn"
    SEASON = "2025-2026"
    DIVISION = "4A"
    
    # Planning settings
    MIN_PLAYERS_PER_MATCH = 4
    MAX_PLAYERS_PER_MATCH = 6
    MATCHES_PER_PLAYER_TARGET = 12  # Ongeveer aantal wedstrijden per speler per seizoen
