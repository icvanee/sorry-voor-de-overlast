from app.models.database import get_db_connection
from datetime import datetime

class Match:
    def __init__(self, id=None, match_number=None, date=None, home_team=None, 
                 away_team=None, is_home=None, is_friendly=False, venue=''):
        self.id = id
        self.match_number = match_number
        self.date = date
        self.home_team = home_team
        self.away_team = away_team
        self.is_home = is_home
        self.is_friendly = is_friendly
        self.venue = venue
    
    @staticmethod
    def get_all():
        """Get all matches ordered by date."""
        conn = get_db_connection()
        matches = conn.execute('''
            SELECT * FROM matches 
            ORDER BY date ASC
        ''').fetchall()
        conn.close()
        return matches
    
    @staticmethod
    def get_by_id(match_id):
        """Get a match by ID."""
        conn = get_db_connection()
        match = conn.execute('''
            SELECT * FROM matches WHERE id = ?
        ''', (match_id,)).fetchone()
        conn.close()
        return match
    
    @staticmethod
    def create(match_number, date, home_team, away_team, is_home, is_friendly=False, venue=''):
        """Create a new match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO matches (match_number, date, home_team, away_team, is_home, is_friendly, venue) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (match_number, date, home_team, away_team, is_home, is_friendly, venue))
        match_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return match_id
    
    @staticmethod
    def update(match_id, match_number, date, home_team, away_team, is_home, is_friendly=False, venue=''):
        """Update a match."""
        conn = get_db_connection()
        conn.execute('''
            UPDATE matches 
            SET match_number = ?, date = ?, home_team = ?, away_team = ?, 
                is_home = ?, is_friendly = ?, venue = ?
            WHERE id = ?
        ''', (match_number, date, home_team, away_team, is_home, is_friendly, venue, match_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(match_id):
        """Delete a match."""
        conn = get_db_connection()
        # First delete related planning entries
        conn.execute('DELETE FROM match_planning WHERE match_id = ?', (match_id,))
        conn.execute('DELETE FROM player_availability WHERE match_id = ?', (match_id,))
        conn.execute('DELETE FROM matches WHERE id = ?', (match_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_upcoming():
        """Get upcoming matches."""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = get_db_connection()
        matches = conn.execute('''
            SELECT * FROM matches 
            WHERE date >= ?
            ORDER BY date ASC
        ''', (today,)).fetchall()
        conn.close()
        return matches
    
    @staticmethod
    def get_home_matches():
        """Get all home matches."""
        conn = get_db_connection()
        matches = conn.execute('''
            SELECT * FROM matches 
            WHERE is_home = TRUE
            ORDER BY date ASC
        ''').fetchall()
        conn.close()
        return matches
    
    @staticmethod
    def get_away_matches():
        """Get all away matches."""
        conn = get_db_connection()
        matches = conn.execute('''
            SELECT * FROM matches 
            WHERE is_home = FALSE
            ORDER BY date ASC
        ''').fetchall()
        conn.close()
        return matches
