import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sorry-voor-de-overlast-secret-key-2025'
    
    # Database configuration - PostgreSQL only
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL or not (DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://')):
        raise Exception("PostgreSQL DATABASE_URL is required. SQLite is no longer supported.")
    
    # PostgreSQL configuration
    url = urlparse(DATABASE_URL)
    DB_TYPE = 'postgresql'
    DB_CONFIG = {
        'host': url.hostname,
        'port': url.port,
        'database': url.path[1:],  # Remove leading slash
        'user': url.username,
        'password': url.password
    }
    print(f"🔗 Database: PostgreSQL @ {url.hostname}:{url.port}/{url.path[1:]}")
    
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
