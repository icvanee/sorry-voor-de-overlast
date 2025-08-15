from app.models.database import get_db_connection
from app.models.player import Player
from app.models.match import Match
import random
from datetime import datetime

class PlanningVersion:
    def __init__(self, id=None, name=None, description='', is_final=False):
        self.id = id
        self.name = name
        self.description = description
        self.is_final = is_final
    
    @staticmethod
    def get_all():
        """Get all planning versions."""
        conn = get_db_connection()
        versions = conn.execute('''
            SELECT * FROM planning_versions 
            ORDER BY created_at DESC
        ''').fetchall()
        conn.close()
        return versions
    
    @staticmethod
    def get_by_id(version_id):
        """Get a planning version by ID."""
        conn = get_db_connection()
        version = conn.execute('''
            SELECT * FROM planning_versions WHERE id = ?
        ''', (version_id,)).fetchone()
        conn.close()
        return version
    
    @staticmethod
    def create(name, description=''):
        """Create a new planning version."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO planning_versions (name, description) 
            VALUES (?, ?)
        ''', (name, description))
        version_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return version_id
    
    @staticmethod
    def set_final(version_id):
        """Set a planning version as final."""
        conn = get_db_connection()
        # First unset all other versions as final
        conn.execute('UPDATE planning_versions SET is_final = FALSE')
        # Set this version as final
        conn.execute('UPDATE planning_versions SET is_final = TRUE WHERE id = ?', (version_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_final():
        """Get the final planning version."""
        conn = get_db_connection()
        version = conn.execute('''
            SELECT * FROM planning_versions WHERE is_final = TRUE
        ''').fetchone()
        conn.close()
        return version

class MatchPlanning:
    @staticmethod
    def get_planning(version_id, match_id=None):
        """Get planning for a version and optionally a specific match."""
        conn = get_db_connection()
        if match_id:
            planning = conn.execute('''
                SELECT mp.*, p.name as player_name, m.date, m.home_team, m.away_team
                FROM match_planning mp
                JOIN players p ON mp.player_id = p.id
                JOIN matches m ON mp.match_id = m.id
                WHERE mp.planning_version_id = ? AND mp.match_id = ?
                ORDER BY p.name
            ''', (version_id, match_id)).fetchall()
        else:
            planning = conn.execute('''
                SELECT mp.*, p.name as player_name, m.date, m.home_team, m.away_team, m.match_number
                FROM match_planning mp
                JOIN players p ON mp.player_id = p.id
                JOIN matches m ON mp.match_id = m.id
                WHERE mp.planning_version_id = ?
                ORDER BY m.date, p.name
            ''', (version_id,)).fetchall()
        conn.close()
        return planning
    
    @staticmethod
    def get_version_planning(version_id):
        """Get all planning for a version grouped by match."""
        planning = MatchPlanning.get_planning(version_id)
        grouped = {}
        
        for item in planning:
            match_id = item['match_id']
            if match_id not in grouped:
                grouped[match_id] = {
                    'match': {
                        'id': match_id,
                        'date': item['date'],
                        'home_team': item['home_team'],
                        'away_team': item['away_team'],
                        'match_number': item.get('match_number', '')
                    },
                    'players': []
                }
            grouped[match_id]['players'].append({
                'id': item['player_id'],
                'name': item['player_name'],
                'is_confirmed': item['is_confirmed'],
                'actually_played': item['actually_played']
            })
        
        return list(grouped.values())
    
    @staticmethod
    def set_planning(version_id, match_id, player_ids):
        """Set planning for a specific match."""
        conn = get_db_connection()
        
        # Remove existing planning for this match in this version
        conn.execute('''
            DELETE FROM match_planning 
            WHERE planning_version_id = ? AND match_id = ?
        ''', (version_id, match_id))
        
        # Add new planning
        for player_id in player_ids:
            conn.execute('''
                INSERT INTO match_planning (planning_version_id, match_id, player_id) 
                VALUES (?, ?, ?)
            ''', (version_id, match_id, player_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def confirm_player(version_id, match_id, player_id, confirmed=True):
        """Confirm a player for a match."""
        conn = get_db_connection()
        conn.execute('''
            UPDATE match_planning 
            SET is_confirmed = ?
            WHERE planning_version_id = ? AND match_id = ? AND player_id = ?
        ''', (confirmed, version_id, match_id, player_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def mark_played(version_id, match_id, player_id, played=True):
        """Mark a player as having actually played."""
        conn = get_db_connection()
        conn.execute('''
            UPDATE match_planning 
            SET actually_played = ?
            WHERE planning_version_id = ? AND match_id = ? AND player_id = ?
        ''', (played, version_id, match_id, player_id))
        conn.commit()
        conn.close()

class AutoPlanner:
    def __init__(self):
        self.min_players = 4
        self.max_players = 6
        self.target_matches_per_player = 12
    
    def generate_planning(self, version_id):
        """Generate automatic planning for all matches."""
        matches = Match.get_all()
        players = Player.get_all()
        
        if not matches or not players:
            return False
        
        # Track player usage
        player_match_count = {player['id']: 0 for player in players}
        
        for match in matches:
            # Get available players for this match
            available_players = self._get_available_players(match['id'], players)
            
            if len(available_players) < self.min_players:
                # Not enough players, use all available + some unavailable
                selected_players = available_players[:self.max_players]
                needed = self.min_players - len(selected_players)
                if needed > 0:
                    unavailable = [p for p in players if p not in available_players]
                    selected_players.extend(unavailable[:needed])
            else:
                # Select players based on usage and preferences
                selected_players = self._select_players_smart(
                    available_players, player_match_count, match
                )
            
            # Update planning
            player_ids = [p['id'] for p in selected_players[:self.max_players]]
            MatchPlanning.set_planning(version_id, match['id'], player_ids)
            
            # Update usage count
            for player_id in player_ids:
                player_match_count[player_id] += 1
        
        return True
    
    def _get_available_players(self, match_id, all_players):
        """Get players available for a match."""
        available = []
        for player in all_players:
            availability = Player.get_availability(player['id'], match_id)
            if not availability or availability['is_available']:
                available.append(player)
        return available
    
    def _select_players_smart(self, available_players, usage_count, match):
        """Smart player selection considering usage and preferences."""
        # Sort by usage count (lowest first)
        available_players.sort(key=lambda p: usage_count[p['id']])
        
        selected = []
        
        # First, try to include partners together if both are available
        partner_pairs = Player.get_partner_pairs()
        for pair in partner_pairs:
            player1 = next((p for p in available_players if p['id'] == pair['id1']), None)
            player2 = next((p for p in available_players if p['id'] == pair['id2']), None)
            
            if player1 and player2 and len(selected) + 2 <= self.max_players:
                if player1 not in selected:
                    selected.append(player1)
                if player2 not in selected:
                    selected.append(player2)
        
        # Fill remaining spots with lowest usage players
        for player in available_players:
            if player not in selected and len(selected) < self.max_players:
                selected.append(player)
        
        return selected
    
    def get_player_statistics(self, version_id):
        """Get statistics for players in this planning version."""
        conn = get_db_connection()
        stats = conn.execute('''
            SELECT p.id, p.name, 
                   COUNT(mp.id) as total_matches,
                   SUM(CASE WHEN mp.is_confirmed THEN 1 ELSE 0 END) as confirmed_matches,
                   SUM(CASE WHEN mp.actually_played THEN 1 ELSE 0 END) as played_matches
            FROM players p
            LEFT JOIN match_planning mp ON p.id = mp.player_id AND mp.planning_version_id = ?
            WHERE p.is_active = TRUE
            GROUP BY p.id, p.name
            ORDER BY total_matches DESC, p.name
        ''', (version_id,)).fetchall()
        conn.close()
        return stats
