from app.models.database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

class Player:
    def __init__(self, id=None, name=None, email=None, phone=None):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
    
    @staticmethod
    def get_all():
        """Get all active players with partner names."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, partner.name as partner_name
            FROM players p
            LEFT JOIN players partner ON p.partner_id = partner.id AND partner.is_active = true
            WHERE p.is_active = true
            ORDER BY p.name
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
    def get_by_email(email):
        """Get a player by email (case-insensitive)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM players WHERE LOWER(email) = LOWER(%s)
        ''', (email,))
        player = cursor.fetchone()
        cursor.close()
        conn.close()
        return player

    @staticmethod
    def set_password(player_id, raw_password, force_change=False):
        """Set password hash and optionally enforce change on next login."""
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed = generate_password_hash(raw_password)
        cursor.execute('''
            UPDATE players
            SET password_hash = %s,
                force_password_change = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (hashed, force_change, player_id))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def clear_force_change(player_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE players
            SET force_password_change = false,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (player_id,))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def verify_password(player, raw_password) -> bool:
        """Verify a raw password against the player's stored hash."""
        ph = (player or {}).get('password_hash')
        if not ph:
            return False
        try:
            return check_password_hash(ph, raw_password)
        except Exception:
            return False
    
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
    def set_partner_bidirectional(player_id, partner_id):
        """Set or clear a partner relationship for a player and mirror it on the partner.

        Rules:
        - When linking A -> B, we also set B -> A.
        - If A had an old partner C, we clear C -> A.
        - If B had an old partner D (and D != A), we clear B -> D and D -> B if it was reciprocal.
        - When unlinking (partner_id is None), we clear A -> None and clear B -> None if B was pointing to A.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Prevent self-link
            if partner_id == player_id:
                partner_id = None

            # Lock rows for consistency
            cursor.execute('SELECT partner_id FROM players WHERE id = %s FOR UPDATE', (player_id,))
            row = cursor.fetchone()
            current_partner = row['partner_id'] if row else None

            # Unlink from current partner if changing
            if current_partner and current_partner != partner_id:
                # Clear old partner's link if it points back
                cursor.execute('SELECT partner_id FROM players WHERE id = %s FOR UPDATE', (current_partner,))
                old_partner_row = cursor.fetchone()
                if old_partner_row and old_partner_row['partner_id'] == player_id:
                    cursor.execute('UPDATE players SET partner_id = NULL WHERE id = %s', (current_partner,))

            if partner_id:
                # Lock new partner row
                cursor.execute('SELECT partner_id FROM players WHERE id = %s FOR UPDATE', (partner_id,))
                partner_row = cursor.fetchone()
                partner_current_partner = partner_row['partner_id'] if partner_row else None

                # If partner currently linked to someone else, clear that reciprocal link
                if partner_current_partner and partner_current_partner != player_id:
                    # Clear the other person's link if it points to this partner
                    cursor.execute('SELECT partner_id FROM players WHERE id = %s FOR UPDATE', (partner_current_partner,))
                    other_row = cursor.fetchone()
                    if other_row and other_row['partner_id'] == partner_id:
                        cursor.execute('UPDATE players SET partner_id = NULL WHERE id = %s', (partner_current_partner,))

                # Set both sides
                cursor.execute('UPDATE players SET partner_id = %s WHERE id = %s', (partner_id, player_id))
                cursor.execute('UPDATE players SET partner_id = %s WHERE id = %s', (player_id, partner_id))
            else:
                # Unlink A and clear B if reciprocal
                cursor.execute('UPDATE players SET partner_id = NULL WHERE id = %s', (player_id,))
                if current_partner:
                    cursor.execute('SELECT partner_id FROM players WHERE id = %s FOR UPDATE', (current_partner,))
                    cp_row = cursor.fetchone()
                    if cp_row and cp_row['partner_id'] == player_id:
                        cursor.execute('UPDATE players SET partner_id = NULL WHERE id = %s', (current_partner,))

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def set_partner_preference_bidirectional(player_id, prefer_together=True):
        """Set prefer_partner_together for player and mirror to their partner if present."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE players SET prefer_partner_together = %s WHERE id = %s', (prefer_together, player_id))
            # Mirror to partner if any
            cursor.execute('SELECT partner_id FROM players WHERE id = %s', (player_id,))
            row = cursor.fetchone()
            if row and row['partner_id']:
                cursor.execute('UPDATE players SET prefer_partner_together = %s WHERE id = %s', (prefer_together, row['partner_id']))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_available_for_partnership(exclude_player_id=None):
        """Get active players who currently have no partner (optionally excluding one)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        if exclude_player_id:
            cursor.execute('''
                SELECT id, name FROM players 
                WHERE is_active = true AND partner_id IS NULL AND id <> %s
                ORDER BY name
            ''', (exclude_player_id,))
        else:
            cursor.execute('''
                SELECT id, name FROM players 
                WHERE is_active = true AND partner_id IS NULL
                ORDER BY name
            ''')
        players = cursor.fetchall()
        cursor.close()
        conn.close()
        return players
    
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
    def get_active_planning_stats(player_id):
        """Get match statistics for a player from the single planning system."""
        # Single planning system - get stats directly from match_planning with planning_version_id = 1
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as matches_planned,
                COUNT(CASE WHEN m.is_home = true THEN 1 END) as home_matches,
                COUNT(CASE WHEN m.is_home = false THEN 1 END) as away_matches,
                COUNT(CASE WHEN mp.actually_played = true THEN 1 END) as matches_played
            FROM match_planning mp
            JOIN matches m ON mp.match_id = m.id
            WHERE mp.player_id = %s AND mp.planning_version_id = 1
        ''', (player_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                'matches_planned': result['matches_planned'] or 0,
                'home_matches': result['home_matches'] or 0,
                'away_matches': result['away_matches'] or 0,
                'matches_played': result['matches_played'] or 0
            }
        else:
            return {
                'matches_planned': 0,
                'home_matches': 0,
                'away_matches': 0,
                'matches_played': 0
            }

    @staticmethod
    def get_availability(player_id, match_id):
        """Get player availability for a specific match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT is_available, notes
            FROM player_availability 
            WHERE player_id = %s AND match_id = %s
        ''', (player_id, match_id))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result

    @staticmethod
    def set_availability(player_id, match_id, is_available, notes=None):
        """Set player availability for a specific match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO player_availability (player_id, match_id, is_available, notes)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (player_id, match_id)
            DO UPDATE SET 
                is_available = EXCLUDED.is_available,
                notes = EXCLUDED.notes,
                updated_at = CURRENT_TIMESTAMP
        ''', (player_id, match_id, is_available, notes))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def update_role(player_id, role):
        """Update a player's role."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE players 
            SET role = %s 
            WHERE id = %s
        ''', (role, player_id))
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
