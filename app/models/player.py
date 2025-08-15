from app.models.database import get_db_connection

class Player:
    def __init__(self, id=None, name=None, role='', is_active=True, partner_id=None):
        self.id = id
        self.name = name
        self.role = role
        self.is_active = is_active
        self.partner_id = partner_id
    
    @staticmethod
    def get_all():
        """Get all active players."""
        conn = get_db_connection()
        players = conn.execute('''
            SELECT p1.*, p2.name as partner_name 
            FROM players p1
            LEFT JOIN players p2 ON p1.partner_id = p2.id
            WHERE p1.is_active = TRUE
            ORDER BY p1.name
        ''').fetchall()
        conn.close()
        return players
    
    @staticmethod
    def get_by_id(player_id):
        """Get a player by ID."""
        conn = get_db_connection()
        player = conn.execute('''
            SELECT p1.*, p2.name as partner_name 
            FROM players p1
            LEFT JOIN players p2 ON p1.partner_id = p2.id
            WHERE p1.id = ?
        ''', (player_id,)).fetchone()
        conn.close()
        return player
    
    @staticmethod
    def create(name, role='', partner_id=None):
        """Create a new player."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO players (name, role, partner_id) 
            VALUES (?, ?, ?)
        ''', (name, role, partner_id))
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return player_id
    
    @staticmethod
    def update(player_id, name, role='', partner_id=None):
        """Update a player."""
        conn = get_db_connection()
        conn.execute('''
            UPDATE players 
            SET name = ?, role = ?, partner_id = ?
            WHERE id = ?
        ''', (name, role, partner_id, player_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def deactivate(player_id):
        """Deactivate a player."""
        conn = get_db_connection()
        conn.execute('''
            UPDATE players SET is_active = FALSE WHERE id = ?
        ''', (player_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_availability(player_id, match_id):
        """Get player availability for a specific match."""
        conn = get_db_connection()
        availability = conn.execute('''
            SELECT * FROM player_availability 
            WHERE player_id = ? AND match_id = ?
        ''', (player_id, match_id)).fetchone()
        conn.close()
        return availability
    
    @staticmethod
    def set_availability(player_id, match_id, is_available, notes=''):
        """Set player availability for a specific match."""
        conn = get_db_connection()
        conn.execute('''
            INSERT OR REPLACE INTO player_availability 
            (player_id, match_id, is_available, notes) 
            VALUES (?, ?, ?, ?)
        ''', (player_id, match_id, is_available, notes))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_partner_pairs():
        """Get all partner pairs."""
        conn = get_db_connection()
        pairs = conn.execute('''
            SELECT p1.id as id1, p1.name as name1, p2.id as id2, p2.name as name2
            FROM players p1
            JOIN players p2 ON p1.partner_id = p2.id
            WHERE p1.id < p2.id AND p1.is_active = TRUE AND p2.is_active = TRUE
        ''').fetchall()
        conn.close()
        return pairs
    
    @staticmethod
    def get_available_for_partnership():
        """Get players available for partnership (those without partners)."""
        conn = get_db_connection()
        players = conn.execute('''
            SELECT * FROM players 
            WHERE partner_id IS NULL AND is_active = TRUE
            ORDER BY name
        ''').fetchall()
        conn.close()
        return players
    
    @staticmethod
    def get_availability_for_all_matches(player_id):
        """Get availability for all matches for a specific player."""
        conn = get_db_connection()
        availabilities = conn.execute('''
            SELECT m.id as match_id, m.date, m.time, m.opponent, 
                   m.is_home, m.competition, pa.is_available, pa.notes
            FROM matches m
            LEFT JOIN player_availability pa ON m.id = pa.match_id AND pa.player_id = ?
            ORDER BY m.date ASC, m.time ASC
        ''', (player_id,)).fetchall()
        conn.close()
        return availabilities
    
    @staticmethod
    def get_availability_stats(player_id):
        """Get availability statistics for a player."""
        conn = get_db_connection()
        stats = conn.execute('''
            SELECT 
                COUNT(m.id) as total_matches,
                COUNT(CASE WHEN pa.is_available = 1 THEN 1 END) as available_matches,
                COUNT(CASE WHEN pa.is_available = 0 THEN 1 END) as unavailable_matches
            FROM matches m
            LEFT JOIN player_availability pa ON m.id = pa.match_id AND pa.player_id = ?
        ''', (player_id,)).fetchone()
        conn.close()
        return stats
    
    @staticmethod
    def get_match_stats(player_id):
        """Get match playing statistics for a player."""
        conn = get_db_connection()
        stats = conn.execute('''
            SELECT 
                COUNT(DISTINCT mp.match_id) as matches_planned,
                COUNT(CASE WHEN mp.actually_played = 1 THEN 1 END) as matches_played,
                COUNT(CASE WHEN mp.is_confirmed = 1 THEN 1 END) as matches_confirmed
            FROM match_planning mp
            WHERE mp.player_id = ?
        ''', (player_id,)).fetchone()
        conn.close()
        return stats
    
    @staticmethod
    def set_partner_preference(player_id, prefer_together=True):
        """Set general partner preference for a player."""
        conn = get_db_connection()
        conn.execute('''
            UPDATE players 
            SET prefer_partner_together = ?
            WHERE id = ?
        ''', (prefer_together, player_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_partner_preference(player_id, match_id=None):
        """Get partner preference for a player (general or match-specific)."""
        conn = get_db_connection()
        
        if match_id:
            # Check for match-specific preference first
            pref = conn.execute('''
                SELECT prefer_together FROM partner_preferences 
                WHERE player_id = ? AND match_id = ?
            ''', (player_id, match_id)).fetchone()
            
            if pref:
                conn.close()
                return pref['prefer_together']
        
        # Fall back to general preference
        player = conn.execute('''
            SELECT prefer_partner_together FROM players WHERE id = ?
        ''', (player_id,)).fetchone()
        conn.close()
        
        return player['prefer_partner_together'] if player else True
