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
        """Get all non-deleted planning versions."""
        conn = get_db_connection()
        versions = conn.execute('''
            SELECT * FROM planning_versions 
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
        ''').fetchall()
        conn.close()
        return versions
    
    @staticmethod
    def get_all_including_deleted():
        """Get all planning versions including soft-deleted ones."""
        conn = get_db_connection()
        versions = conn.execute('''
            SELECT *, 
                   CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END as is_deleted
            FROM planning_versions 
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
        """Mark a planning version as final."""
        conn = get_db_connection()
        
        # First, unmark all other versions
        conn.execute('''
            UPDATE planning_versions SET is_final = FALSE
        ''')
        
        # Mark this version as final
        conn.execute('''
            UPDATE planning_versions SET is_final = TRUE WHERE id = ?
        ''', (version_id,))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def copy_from_version(name, description, source_version_id, pinned_matches=None):
        """Create a new planning version by copying from an existing one."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create new version
        cursor.execute('''
            INSERT INTO planning_versions (name, description) 
            VALUES (?, ?)
        ''', (name, description))
        new_version_id = cursor.lastrowid
        
        # Copy planning from source version
        if pinned_matches is None:
            pinned_matches = []
        
        # Copy all planning entries
        cursor.execute('''
            INSERT INTO match_planning (planning_version_id, match_id, player_id, is_confirmed, actually_played, is_pinned, notes)
            SELECT ?, match_id, player_id, is_confirmed, actually_played, 
                   CASE WHEN match_id IN ({}) THEN TRUE ELSE FALSE END, notes
            FROM match_planning 
            WHERE planning_version_id = ?
        '''.format(','.join('?' * len(pinned_matches)) if pinned_matches else 'NULL'), 
           [new_version_id] + pinned_matches + [source_version_id])
        
        conn.commit()
        conn.close()
        return new_version_id
    
    @staticmethod
    def get_final():
        """Get the final planning version."""
        conn = get_db_connection()
        version = conn.execute('''
            SELECT * FROM planning_versions WHERE is_final = TRUE AND deleted_at IS NULL
        ''').fetchone()
        conn.close()
        return version
    
    @staticmethod
    def soft_delete(version_id):
        """Soft delete a planning version by setting deleted_at timestamp."""
        conn = get_db_connection()
        conn.execute('''
            UPDATE planning_versions 
            SET deleted_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (version_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def restore(version_id):
        """Restore a soft-deleted planning version by clearing deleted_at."""
        conn = get_db_connection()
        conn.execute('''
            UPDATE planning_versions 
            SET deleted_at = NULL 
            WHERE id = ?
        ''', (version_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def is_deleted(version_id):
        """Check if a planning version is soft-deleted."""
        conn = get_db_connection()
        result = conn.execute('''
            SELECT deleted_at FROM planning_versions WHERE id = ?
        ''', (version_id,)).fetchone()
        conn.close()
        return result and result['deleted_at'] is not None

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
                # Handle potential missing match_number column safely
                try:
                    match_number = item['match_number'] or ''
                except (KeyError, IndexError):
                    match_number = ''
                    
                grouped[match_id] = {
                    'match': {
                        'id': match_id,
                        'date': item['date'],
                        'home_team': item['home_team'],
                        'away_team': item['away_team'],
                        'match_number': match_number
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
    def pin_match(version_id, match_id, pinned=True):
        """Pin or unpin a match to preserve its planning."""
        conn = get_db_connection()
        conn.execute('''
            UPDATE match_planning 
            SET is_pinned = ?
            WHERE planning_version_id = ? AND match_id = ?
        ''', (pinned, version_id, match_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_pinned_matches(version_id):
        """Get all pinned matches for a version."""
        conn = get_db_connection()
        matches = conn.execute('''
            SELECT DISTINCT match_id 
            FROM match_planning 
            WHERE planning_version_id = ? AND is_pinned = TRUE
        ''', (version_id,)).fetchall()
        conn.close()
        return [match['match_id'] for match in matches]
    
    @staticmethod
    def is_match_pinned(version_id, match_id):
        """Check if a match is pinned."""
        conn = get_db_connection()
        result = conn.execute('''
            SELECT COUNT(*) as count
            FROM match_planning 
            WHERE planning_version_id = ? AND match_id = ? AND is_pinned = TRUE
        ''', (version_id, match_id)).fetchone()
        conn.close()
        return result['count'] > 0
    
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
        self.max_players = 4  # HARDE REGEL: Maximaal 4 spelers per wedstrijd
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
    
    def generate_planning_selective(self, version_id, exclude_pinned=True):
        """Generate planning for specific matches, optionally excluding pinned ones."""
        all_players = Player.get_all()
        all_matches = Match.get_all()
        
        if exclude_pinned:
            pinned_matches = MatchPlanning.get_pinned_matches(version_id)
            matches_to_plan = [m for m in all_matches if m['id'] not in pinned_matches]
        else:
            matches_to_plan = all_matches
        
        # Get current usage count
        player_match_count = {}
        for player in all_players:
            stats = self.get_current_usage(version_id, player['id'])
            player_match_count[player['id']] = stats
        
        # Generate planning for selected matches
        for match in matches_to_plan:
            available_players = self._get_available_players(match['id'], all_players)
            
            if len(available_players) < self.max_players:
                print(f"Warning: Only {len(available_players)} players available for match {match['id']}")
            
            # Select players based on smart algorithm
            selected_players = self._select_players_smart(
                available_players, player_match_count, match
            )
            
            # Update planning (remove existing first if not pinned)
            if not exclude_pinned or not MatchPlanning.is_match_pinned(version_id, match['id']):
                player_ids = [p['id'] for p in selected_players[:self.max_players]]
                MatchPlanning.set_planning(version_id, match['id'], player_ids)
                
                # Update usage count
                for player_id in player_ids:
                    player_match_count[player_id] += 1
        
        return True
    
    def get_current_usage(self, version_id, player_id):
        """Get current match count for a player in this version."""
        conn = get_db_connection()
        result = conn.execute('''
            SELECT COUNT(*) as count
            FROM match_planning 
            WHERE planning_version_id = ? AND player_id = ?
        ''', (version_id, player_id)).fetchone()
        conn.close()
        return result['count'] if result else 0
    
    def _get_available_players(self, match_id, all_players):
        """Get players available for a match."""
        available = []
        for player in all_players:
            availability = Player.get_availability(player['id'], match_id)
            if not availability or availability['is_available']:
                available.append(player)
        return available
    
    def _select_players_smart(self, available_players, usage_count, match):
        """Smart player selection considering usage and partner preferences with improved balance."""
        if len(available_players) < self.max_players:
            # If not enough available players, use all available ones
            return available_players[:self.max_players]
        
        # Calculate average usage to aim for balance
        total_usage = sum(usage_count.values())
        total_players = len(usage_count)
        average_usage = total_usage / total_players if total_players > 0 else 0
        
        # Sort available players by usage count (lowest first) and then by how much below average they are
        def priority_score(player):
            usage = usage_count[player['id']]
            below_average = max(0, average_usage - usage)  # Prioritize players below average
            return (usage, -below_average)  # Lower usage first, then those most below average
        
        available_players.sort(key=priority_score)
        
        selected = []
        used_player_ids = set()
        
        # Get partner pairs who prefer to play together
        try:
            partner_pairs = Player.get_partner_pairs()
        except:
            partner_pairs = []  # Fallback if method doesn't exist
        
        # First, try to include partner pairs if they're both low on usage
        for pair in partner_pairs:
            if len(selected) >= self.max_players:
                break
                
            player1 = next((p for p in available_players if p['id'] == pair['id1']), None)
            player2 = next((p for p in available_players if p['id'] == pair['id2']), None)
            
            # Check if both players are available and not already selected
            if (player1 and player2 and 
                player1['id'] not in used_player_ids and 
                player2['id'] not in used_player_ids and
                len(selected) + 2 <= self.max_players):
                
                # Only include pair if both have low usage (below or at average)
                usage1 = usage_count[player1['id']]
                usage2 = usage_count[player2['id']]
                
                if usage1 <= average_usage and usage2 <= average_usage:
                    selected.append(player1)
                    selected.append(player2)
                    used_player_ids.add(player1['id'])
                    used_player_ids.add(player2['id'])
        
        # Fill remaining spots with players having the lowest usage
        remaining_players = [p for p in available_players if p['id'] not in used_player_ids]
        remaining_players.sort(key=lambda p: usage_count[p['id']])
        
        for player in remaining_players:
            if len(selected) < self.max_players:
                selected.append(player)
                used_player_ids.add(player['id'])
                
        # Ensure we have exactly max_players (4) if possible
        if len(selected) < self.max_players and len(available_players) >= self.max_players:
            # Add more players if we somehow selected too few
            all_available = [p for p in available_players if p['id'] not in used_player_ids]
            for player in all_available:
                if len(selected) < self.max_players:
                    selected.append(player)
        
        return selected[:self.max_players]  # Ensure exactly max_players
    
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
