from app.models.database import get_db_connection
from datetime import datetime
from config import Config

class Match:
    def __init__(self, id=None, match_date=None, opponent=None, location=None, 
                 is_home=True):
        self.id = id
        self.match_date = match_date
        self.opponent = opponent
        self.location = location
        self.is_home = is_home
    
    @staticmethod
    def get_all():
        """Get all matches ordered by date."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM matches 
                ORDER BY match_date ASC
            ''')
            matches = cursor.fetchall()
            cursor.close()
        else:
            matches = conn.execute('''
                SELECT * FROM matches 
                ORDER BY match_date ASC
            ''').fetchall()
        
        conn.close()
        return matches
    
    @staticmethod
    def get_by_id(match_id):
        """Get a match by ID."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM matches WHERE id = %s
            ''', (match_id,))
            match = cursor.fetchone()
            cursor.close()
        else:
            match = conn.execute('''
                SELECT * FROM matches WHERE id = ?
            ''', (match_id,)).fetchone()
        
        conn.close()
        return match
    
    @staticmethod
    def create(match_date, opponent, location=None, is_home=True):
        """Create a new match."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO matches (match_date, opponent, location, is_home) 
                VALUES (%s, %s, %s, %s) RETURNING id
            ''', (match_date, opponent, location, is_home))
            match_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
        else:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO matches (match_date, opponent, location, is_home) 
                VALUES (?, ?, ?, ?)
            ''', (match_date, opponent, location, is_home))
            match_id = cursor.lastrowid
            conn.commit()
        
        conn.close()
        return match_id
    
    @staticmethod
    def update(match_id, match_date=None, opponent=None, location=None, is_home=None):
        """Update a match."""
        conn = get_db_connection()
        
        # Build dynamic update query
        updates = []
        params = []
        
        if match_date is not None:
            updates.append('match_date = %s' if Config.DB_TYPE == 'postgresql' else 'match_date = ?')
            params.append(match_date)
        if opponent is not None:
            updates.append('opponent = %s' if Config.DB_TYPE == 'postgresql' else 'opponent = ?')
            params.append(opponent)
        if location is not None:
            updates.append('location = %s' if Config.DB_TYPE == 'postgresql' else 'location = ?')
            params.append(location)
        if is_home is not None:
            updates.append('is_home = %s' if Config.DB_TYPE == 'postgresql' else 'is_home = ?')
            params.append(is_home)
        
        if not updates:
            conn.close()
            return
        
        params.append(match_id)
        param_placeholder = '%s' if Config.DB_TYPE == 'postgresql' else '?'
        
        query = f'''UPDATE matches SET {", ".join(updates)} WHERE id = {param_placeholder}'''
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
        else:
            conn.execute(query, params)
            conn.commit()
        
        conn.close()
    
    @staticmethod
    def delete(match_id):
        """Delete a match."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            # First delete related planning entries
            cursor.execute('DELETE FROM match_planning WHERE match_id = %s', (match_id,))
            cursor.execute('DELETE FROM player_availability WHERE match_id = %s', (match_id,))
            cursor.execute('DELETE FROM matches WHERE id = %s', (match_id,))
            conn.commit()
            cursor.close()
        else:
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
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM matches 
                WHERE match_date >= %s
                ORDER BY match_date ASC
            ''', (today,))
            matches = cursor.fetchall()
            cursor.close()
        else:
            matches = conn.execute('''
                SELECT * FROM matches 
                WHERE match_date >= ?
                ORDER BY match_date ASC
            ''', (today,)).fetchall()
        
        conn.close()
        return matches
    
    @staticmethod
    def get_home_matches():
        """Get all home matches."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM matches 
                WHERE is_home = true
                ORDER BY match_date ASC
            ''')
            matches = cursor.fetchall()
            cursor.close()
        else:
            matches = conn.execute('''
                SELECT * FROM matches 
                WHERE is_home = 1
                ORDER BY match_date ASC
            ''').fetchall()
        
        conn.close()
        return matches
    
    @staticmethod
    def get_away_matches():
        """Get all away matches."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM matches 
                WHERE is_home = false
                ORDER BY match_date ASC
            ''')
            matches = cursor.fetchall()
            cursor.close()
        else:
            matches = conn.execute('''
                SELECT * FROM matches 
                WHERE is_home = 0
                ORDER BY match_date ASC
            ''').fetchall()
        
        conn.close()
        return matches
