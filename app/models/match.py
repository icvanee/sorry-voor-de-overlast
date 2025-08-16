from app.models.database import get_db_connection
from datetime import datetime, date

class Match:
    def __init__(self, id=None, home_team=None, away_team=None, match_date=None, match_time=None, location=None, is_home=None):
        self.id = id
        self.home_team = home_team
        self.away_team = away_team
        self.match_date = match_date
        self.match_time = match_time
        self.location = location
        self.is_home = is_home

    @staticmethod
    def get_all():
        """Get all matches ordered by date."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM matches 
            ORDER BY match_date ASC, match_time ASC
        ''')
        matches = cursor.fetchall()
        cursor.close()
        conn.close()
        return matches

    @staticmethod
    def get_by_id(match_id):
        """Get a match by its ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM matches WHERE id = %s
        ''', (match_id,))
        match = cursor.fetchone()
        cursor.close()
        conn.close()
        return match

    @staticmethod
    def get_home_matches():
        """Get all home matches."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM matches 
            WHERE is_home = true 
            ORDER BY match_date ASC, match_time ASC
        ''')
        matches = cursor.fetchall()
        cursor.close()
        conn.close()
        return matches

    @staticmethod
    def get_away_matches():
        """Get all away matches."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM matches 
            WHERE is_home = false 
            ORDER BY match_date ASC, match_time ASC
        ''')
        matches = cursor.fetchall()
        cursor.close()
        conn.close()
        return matches

    @staticmethod
    def create(home_team, away_team, match_date, match_time=None, location=None, is_home=True, 
               opponent=None):
        """Create a new match."""
        conn = get_db_connection()
        
        try:
            cursor = conn.cursor()
            
            # Handle date conversion if needed
            if isinstance(match_date, str):
                try:
                    match_date = datetime.strptime(match_date, '%Y-%m-%d').date()
                except ValueError:
                    match_date = datetime.strptime(match_date, '%d-%m-%Y').date()
            
            # Determine opponent from teams
            if not opponent:
                if is_home:
                    opponent = away_team
                else:
                    opponent = home_team
            
            cursor.execute('''
                INSERT INTO matches (home_team, away_team, match_date, match_time, location, 
                                   is_home, opponent)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (home_team, away_team, match_date, match_time, location, 
                  is_home, opponent))
            
            result = cursor.fetchone()
            match_id = result['id']
            conn.commit()
            cursor.close()
            conn.close()
            return match_id
            
        except Exception as e:
            print(f"Error creating match: {e}")
            cursor.close()
            conn.close()
            raise

    @staticmethod
    def update(match_id, **kwargs):
        """Update match details."""
        conn = get_db_connection()
        
        # Build dynamic query based on provided parameters
        updates = []
        params = []
        
        # Map to actual column names in database
        field_mapping = {
            'match_time': 'time',
            'match_date': 'match_date',
            'opponent': 'opponent', 
            'location': 'location',
            'is_home': 'is_home',
            'home_team': 'home_team',
            'away_team': 'away_team'
        }
        
        for field, value in kwargs.items():
            if field in field_mapping and value is not None:
                db_field = field_mapping[field]
                updates.append(f'{db_field} = %s')
                params.append(value)
        
        if not updates:
            conn.close()
            return
        
        params.append(match_id)
        query = f'''UPDATE matches SET {", ".join(updates)} WHERE id = %s'''
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def delete(match_id):
        """Delete a match and its related data."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First delete related player availability
        cursor.execute('DELETE FROM player_availability WHERE match_id = %s', (match_id,))
        
        # Delete related match planning
        cursor.execute('DELETE FROM match_planning WHERE match_id = %s', (match_id,))
        
        # Finally delete the match
        cursor.execute('DELETE FROM matches WHERE id = %s', (match_id,))
        
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get_upcoming(limit=None):
        """Get upcoming matches."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM matches 
            WHERE match_date >= %s 
            ORDER BY match_date ASC, match_time ASC
        '''
        
        params = [date.today()]
        if limit:
            query += ' LIMIT %s'
            params.append(limit)
        
        cursor.execute(query, params)
        matches = cursor.fetchall()
        cursor.close()
        conn.close()
        return matches

    @staticmethod
    def get_past(limit=None):
        """Get past matches."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM matches 
            WHERE match_date < %s 
            ORDER BY match_date DESC, time DESC
        '''
        
        params = [date.today()]
        if limit:
            query += ' LIMIT %s'
            params.append(limit)
        
        cursor.execute(query, params)
        matches = cursor.fetchall()
        cursor.close()
        conn.close()
        return matches

    @staticmethod
    def get_by_date_range(start_date, end_date):
        """Get matches within a date range."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM matches 
            WHERE match_date >= %s AND match_date <= %s 
            ORDER BY match_date ASC, match_time ASC
        ''', (start_date, end_date))
        matches = cursor.fetchall()
        cursor.close()
        conn.close()
        return matches

    @staticmethod
    def exists(home_team, away_team, match_date):
        """Check if a match already exists."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM matches 
            WHERE home_team = %s AND away_team = %s AND match_date = %s
        ''', (home_team, away_team, match_date))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result['count'] > 0

    @staticmethod
    def get_statistics():
        """Get match statistics."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_matches,
                COUNT(CASE WHEN is_home = true THEN 1 END) as home_matches,
                COUNT(CASE WHEN is_home = false THEN 1 END) as away_matches,
                COUNT(CASE WHEN match_date >= %s THEN 1 END) as upcoming_matches,
                COUNT(CASE WHEN match_date < %s THEN 1 END) as past_matches
            FROM matches
        ''', (date.today(), date.today()))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            'total_matches': result['total_matches'] or 0,
            'home_matches': result['home_matches'] or 0,
            'away_matches': result['away_matches'] or 0,
            'upcoming_matches': result['upcoming_matches'] or 0,
            'past_matches': result['past_matches'] or 0,
        }
