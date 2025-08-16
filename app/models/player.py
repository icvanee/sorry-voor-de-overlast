from app.models.database import get_db_connection

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
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM players
            WHERE is_active = true
            ORDER BY name
        ''')
        players = cursor.fetchall()
        cursor.close()
        conn.close()
        return players
    
    @staticmethod
    def get_by_id(player_id):
        """Get a player by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM players WHERE id = %s
        ''', (player_id,))
        player = cursor.fetchone()
        cursor.close()
        conn.close()
        return player
    
    @staticmethod
    def create(name, email=None, phone=None, role='speler', partner_id=None):
        """Create a new player."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO players (name, email, phone, role, partner_id) 
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING id
        ''', (name, email, phone, role, partner_id))
        result = cursor.fetchone()
        player_id = result['id']
        conn.commit()
        cursor.close()
        conn.close()
        return player_id
    
    @staticmethod
    def update(player_id, name=None, role=None, partner_id=None, email=None, phone=None):
        """Update player details."""
        conn = get_db_connection()
        
        # Build dynamic query based on provided parameters
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if role is not None:
            updates.append("role = %s")
            params.append(role)
        if partner_id is not None:
            updates.append("partner_id = %s")
            params.append(partner_id)
        if email is not None:
            updates.append("email = %s")
            params.append(email)
        if phone is not None:
            updates.append("phone = %s")
            params.append(phone)
        
        if not updates:
            conn.close()
            return
        
        params.append(player_id)
        query = f'''UPDATE players SET {", ".join(updates)} WHERE id = %s'''
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def set_partner_preference(player_id, prefer_together=True):
        """Set player's preference for playing with their partner."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE players 
            SET prefer_partner_together = %s 
            WHERE id = %s
        ''', (prefer_together, player_id))
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def get_partner_preference(player_id):
        """Get player's preference for playing with their partner."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT prefer_partner_together FROM players WHERE id = %s
        ''', (player_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result['prefer_partner_together'] if result else True
    
    @staticmethod
    def delete(player_id):
        """Delete a player."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM players WHERE id = %s', (player_id,))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def deactivate(player_id):
        """Deactivate a player (soft delete)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE players 
            SET is_active = false 
            WHERE id = %s
        ''', (player_id,))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def activate(player_id):
        """Activate a player."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE players 
            SET is_active = true 
            WHERE id = %s
        ''', (player_id,))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get_partner_pairs():
        """Get player partner pairs for statistics."""
        conn = get_db_connection()
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
        conn.close()
        
        # Convert to list of dictionaries for easier use
        partner_pairs = []
        for pair in pairs:
            partner_pairs.append({
                'player1': {'id': pair['player1_id'], 'name': pair['player1_name']},
                'player2': {'id': pair['player2_id'], 'name': pair['player2_name']}
            })
        
        return partner_pairs

    @staticmethod
    def get_availability_stats(player_id):
        """Get availability statistics for a player."""
        conn = get_db_connection()
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
        conn.close()
        
        if result:
            total = result['total_matches'] or 0
            available = result['available'] or 0
            unavailable = result['unavailable'] or 0
            
            return {
                'total_matches': total,
                'available': available,
                'unavailable': unavailable,
                'availability_rate': (available / total * 100) if total > 0 else 0
            }
        else:
            return {
                'total_matches': 0,
                'available': 0,
                'unavailable': 0,
                'availability_rate': 0
            }

    @staticmethod
    def get_availability(player_id, match_id):
        """Get availability for a specific player and match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM player_availability 
            WHERE player_id = %s AND match_id = %s
        ''', (player_id, match_id))
        availability = cursor.fetchone()
        cursor.close()
        conn.close()
        return availability

    @staticmethod
    def set_availability(player_id, match_id, is_available, notes=None):
        """Set availability for a specific player and match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO player_availability (player_id, match_id, is_available, notes)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (player_id, match_id) 
            DO UPDATE SET is_available = %s, notes = %s, updated_at = CURRENT_TIMESTAMP
        ''', (player_id, match_id, is_available, notes, is_available, notes))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get_all_availability(player_id):
        """Get all availability records for a player."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pa.*, m.match_date, m.home_team, m.away_team, m.opponent
            FROM player_availability pa
            JOIN matches m ON pa.match_id = m.id
            WHERE pa.player_id = %s
            ORDER BY m.match_date ASC
        ''', (player_id,))
        availability = cursor.fetchall()
        cursor.close()
        conn.close()
        return availability

    @staticmethod
    def get_match_stats(player_id):
        """Get match statistics for a player."""
        conn = get_db_connection()
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
        conn.close()
        
        if result:
            played = result['played'] or 0
            home_matches = result['home_matches'] or 0
            away_matches = result['away_matches'] or 0
            
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

    @staticmethod
    def get_availability(player_id, match_id):
        """Get player availability for a specific match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT available, notes
            FROM player_availability 
            WHERE player_id = %s AND match_id = %s
        ''', (player_id, match_id))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result

    @staticmethod
    def set_availability(player_id, match_id, available, notes=None):
        """Set player availability for a specific match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO player_availability (player_id, match_id, available, notes)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (player_id, match_id)
            DO UPDATE SET 
                available = EXCLUDED.available,
                notes = EXCLUDED.notes,
                updated_at = CURRENT_TIMESTAMP
        ''', (player_id, match_id, available, notes))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get_all_availability(player_id):
        """Get all availability records for a player."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pa.*, m.date, m.time, m.home_team, m.away_team
            FROM player_availability pa
            JOIN matches m ON pa.match_id = m.id
            WHERE pa.player_id = %s
            ORDER BY m.date, m.time
        ''', (player_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
