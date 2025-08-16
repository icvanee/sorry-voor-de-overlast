from app.models.database import get_db_connection
from config import Config

class Player:
    def __init__(self, id=None, name=None, email=None, phone=None):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
    
    @staticmethod
    def get_all():
        """Get all active players."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM players
                ORDER BY name
            ''')
            players = cursor.fetchall()
            cursor.close()
        else:
            players = conn.execute('''
                SELECT * FROM players
                ORDER BY name
            ''').fetchall()
        
        conn.close()
        return players
    
    @staticmethod
    def get_by_id(player_id):
        """Get a player by ID."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM players WHERE id = %s
            ''', (player_id,))
            player = cursor.fetchone()
            cursor.close()
        else:
            player = conn.execute('''
                SELECT * FROM players WHERE id = ?
            ''', (player_id,)).fetchone()
        
        conn.close()
        return player

    @staticmethod
    def create(name, email=None, phone=None):
        """Create a new player."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO players (name, email, phone) 
                VALUES (%s, %s, %s) RETURNING id
            ''', (name, email, phone))
            player_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
        else:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO players (name, email, phone) 
                VALUES (?, ?, ?)
            ''', (name, email, phone))
            player_id = cursor.lastrowid
            conn.commit()
        
        conn.close()
        return player_id
    
    @staticmethod
    def update(player_id, name=None, email=None, phone=None):
        """Update a player."""
        conn = get_db_connection()
        
        # Build dynamic update query
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = %s' if Config.DB_TYPE == 'postgresql' else 'name = ?')
            params.append(name)
        if email is not None:
            updates.append('email = %s' if Config.DB_TYPE == 'postgresql' else 'email = ?')
            params.append(email)
        if phone is not None:
            updates.append('phone = %s' if Config.DB_TYPE == 'postgresql' else 'phone = ?')
            params.append(phone)
        
        if not updates:
            conn.close()
            return
        
        params.append(player_id)
        param_placeholder = '%s' if Config.DB_TYPE == 'postgresql' else '?'
        
        query = f'''UPDATE players SET {", ".join(updates)} WHERE id = {param_placeholder}'''
        
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
    def delete(player_id):
        """Delete a player."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('DELETE FROM players WHERE id = %s', (player_id,))
            conn.commit()
            cursor.close()
        else:
            conn.execute('DELETE FROM players WHERE id = ?', (player_id,))
            conn.commit()
        
        conn.close()

    @staticmethod
    def get_partner_pairs():
        """Get player partner pairs for statistics."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p1.id as player1_id, p1.name as player1_name, 
                       p2.id as player2_id, p2.name as player2_name
                FROM players p1
                JOIN players p2 ON p1.partner_id = p2.id
                WHERE p1.id < p2.id  -- Avoid duplicates by only including pairs where player1_id < player2_id
                  AND p1.is_active = true AND p2.is_active = true
                ORDER BY p1.name
            ''')
            pairs = cursor.fetchall()
            cursor.close()
        else:
            pairs = conn.execute('''
                SELECT p1.id as player1_id, p1.name as player1_name, 
                       p2.id as player2_id, p2.name as player2_name
                FROM players p1
                JOIN players p2 ON p1.partner_id = p2.id
                WHERE p1.id < p2.id  -- Avoid duplicates
                  AND p1.is_active = 1 AND p2.is_active = 1
                ORDER BY p1.name
            ''').fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries for easier use
        partner_pairs = []
        for pair in pairs:
            if Config.DB_TYPE == 'postgresql':
                # psycopg3 dict-like row access
                partner_pairs.append({
                    'player1': {'id': pair['player1_id'], 'name': pair['player1_name']},
                    'player2': {'id': pair['player2_id'], 'name': pair['player2_name']}
                })
            else:
                # SQLite row access
                partner_pairs.append({
                    'player1': {'id': pair[0], 'name': pair[1]},
                    'player2': {'id': pair[2], 'name': pair[3]}
                })
        
        return partner_pairs

    @staticmethod
    def get_availability_stats(player_id):
        """Get availability statistics for a player."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as total_matches,
                       SUM(CASE WHEN is_available = true THEN 1 ELSE 0 END) as available,
                       SUM(CASE WHEN is_available = false THEN 1 ELSE 0 END) as unavailable
                FROM player_availability 
                WHERE player_id = %s
            ''', (player_id,))
            result = cursor.fetchone()
            cursor.close()
        else:
            result = conn.execute('''
                SELECT COUNT(*) as total_matches,
                       SUM(CASE WHEN is_available = 1 THEN 1 ELSE 0 END) as available,
                       SUM(CASE WHEN is_available = 0 THEN 1 ELSE 0 END) as unavailable
                FROM player_availability 
                WHERE player_id = ?
            ''', (player_id,)).fetchone()
        
        conn.close()
        
        if result:
            if Config.DB_TYPE == 'postgresql':
                total = result['total_matches'] or 0
                available = result['available'] or 0  
                unavailable = result['unavailable'] or 0
            else:
                total = result[0] or 0
                available = result[1] or 0
                unavailable = result[2] or 0
                
            availability_rate = round((available / total) * 100, 1) if total > 0 else 0
            
            return {
                'total_matches': total,
                'available': available,
                'unavailable': unavailable,
                'availability_rate': availability_rate
            }
        else:
            return {
                'total_matches': 0,
                'available': 0,
                'unavailable': 0,
                'availability_rate': 0
            }

    @staticmethod
    def get_match_stats(player_id):
        """Get match statistics for a player."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as played,
                       SUM(CASE WHEN m.is_home = true THEN 1 ELSE 0 END) as home_matches,
                       SUM(CASE WHEN m.is_home = false THEN 1 ELSE 0 END) as away_matches
                FROM match_planning mp
                JOIN matches m ON mp.match_id = m.id
                WHERE mp.player_id = %s AND mp.actually_played = true
            ''', (player_id,))
            result = cursor.fetchone()
            cursor.close()
        else:
            result = conn.execute('''
                SELECT COUNT(*) as played,
                       SUM(CASE WHEN m.is_home = 1 THEN 1 ELSE 0 END) as home_matches,
                       SUM(CASE WHEN m.is_home = 0 THEN 1 ELSE 0 END) as away_matches
                FROM match_planning mp
                JOIN matches m ON mp.match_id = m.id
                WHERE mp.player_id = ? AND mp.actually_played = 1
            ''', (player_id,)).fetchone()
        
        conn.close()
        
        if result:
            if Config.DB_TYPE == 'postgresql':
                played = result['played'] or 0
                home_matches = result['home_matches'] or 0
                away_matches = result['away_matches'] or 0
            else:
                played = result[0] or 0
                home_matches = result[1] or 0
                away_matches = result[2] or 0
            
            return {
                'played': played,
                'home_matches': home_matches,
                'away_matches': away_matches
            }
        else:
            return {
                'played': 0,
                'home_matches': 0,
                'away_matches': 0
            }
