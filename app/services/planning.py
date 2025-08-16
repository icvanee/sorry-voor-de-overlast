from app.models.database import get_db_connection
from datetime import datetime

class PlanningVersion:
    """Model for managing different planning versions."""
    
    @staticmethod
    def get_all():
        """Get all non-deleted planning versions."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM planning_versions 
            WHERE deleted_at IS NULL 
            ORDER BY created_at DESC
        ''')
        versions = cursor.fetchall()
        cursor.close()
        conn.close()
        return versions
    
    @staticmethod
    def get_by_id(version_id):
        """Get a planning version by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM planning_versions WHERE id = %s
        ''', (version_id,))
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        return version
    
    @staticmethod
    def create(name, description=None):
        """Create a new planning version."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO planning_versions (name, description, created_at)
            VALUES (%s, %s, %s)
            RETURNING id
        ''', (name, description, datetime.now()))
        result = cursor.fetchone()
        version_id = result['id']
        conn.commit()
        cursor.close()
        conn.close()
        return version_id
    
    @staticmethod
    def update(version_id, name=None, description=None):
        """Update a planning version."""
        conn = get_db_connection()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if not updates:
            conn.close()
            return
        
        params.append(version_id)
        query = f'''UPDATE planning_versions SET {", ".join(updates)} WHERE id = %s'''
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def soft_delete(version_id):
        """Soft delete a planning version."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE planning_versions 
            SET deleted_at = %s 
            WHERE id = %s
        ''', (datetime.now(), version_id))
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def restore(version_id):
        """Restore a soft-deleted planning version."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE planning_versions 
            SET deleted_at = NULL 
            WHERE id = %s
        ''', (version_id,))
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def delete(version_id):
        """Hard delete a planning version."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First delete associated match planning
        cursor.execute('DELETE FROM match_planning WHERE planning_version_id = %s', (version_id,))
        
        # Then delete the version
        cursor.execute('DELETE FROM planning_versions WHERE id = %s', (version_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def is_deleted(version_id):
        """Check if a planning version is soft-deleted."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT deleted_at FROM planning_versions WHERE id = %s
        ''', (version_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result and result['deleted_at'] is not None
    
    @staticmethod
    def copy_from_version(source_version_id, name, description=None):
        """Copy planning from one version to create a new version."""
        # Create new version
        new_version_id = PlanningVersion.create(name, description)
        
        # Copy planning data from source version
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO match_planning (planning_version_id, match_id, player_id, is_pinned, actually_played)
            SELECT %s, match_id, player_id, is_pinned, actually_played
            FROM match_planning 
            WHERE planning_version_id = %s
        ''', (new_version_id, source_version_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return new_version_id
    
    @staticmethod
    def get_final():
        """Get the final (definitive) planning version."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM planning_versions 
            WHERE is_final = true AND deleted_at IS NULL 
            ORDER BY created_at DESC 
            LIMIT 1
        ''')
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        return version
    
    @staticmethod
    def get_active():
        """Get the most recent non-final planning version (considered 'active')."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM planning_versions 
            WHERE is_final = false AND deleted_at IS NULL 
            ORDER BY created_at DESC 
            LIMIT 1
        ''')
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        return version
    
    @staticmethod
    def set_final(version_id):
        """Set a version as the final (definitive) planning."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First, unset any existing final version
        cursor.execute('''
            UPDATE planning_versions SET is_final = false
        ''')
        
        # Set the new final version
        cursor.execute('''
            UPDATE planning_versions 
            SET is_final = true 
            WHERE id = %s
        ''', (version_id,))
        
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def set_active(version_id):
        """Set a version as the active planning (non-final but current)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # For now, we consider the most recent non-final version as active
        # This could be enhanced later with an explicit is_active column
        # Currently active status is determined by get_active() method
        
        # Verify the version exists and is not final
        cursor.execute('''
            SELECT id FROM planning_versions 
            WHERE id = %s AND is_final = false AND deleted_at IS NULL
        ''', (version_id,))
        
        version = cursor.fetchone()
        if not version:
            cursor.close()
            conn.close()
            raise ValueError("Version not found or is final/deleted")
        
        # Update the version's timestamp to make it most recent (hence active)
        cursor.execute('''
            UPDATE planning_versions 
            SET created_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (version_id,))
        
        conn.commit()
        cursor.close()
        conn.close()


class MatchPlanning:
    """Model for managing player assignments to matches within planning versions."""
    
    @staticmethod
    def get_planning(version_id, match_id):
        """Get planning for a specific match in a specific version."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT mp.*, p.name as player_name, p.role
            FROM match_planning mp
            JOIN players p ON mp.player_id = p.id
            WHERE mp.planning_version_id = %s AND mp.match_id = %s
            ORDER BY p.name
        ''', (version_id, match_id))
        planning = cursor.fetchall()
        cursor.close()
        conn.close()
        return planning
    
    @staticmethod
    def get_version_planning(version_id):
        """Get all planning for a specific version."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT mp.*, p.name as player_name, p.role, m.match_date, m.home_team, m.away_team
            FROM match_planning mp
            JOIN players p ON mp.player_id = p.id
            JOIN matches m ON mp.match_id = m.id
            WHERE mp.planning_version_id = %s
            ORDER BY m.match_date, p.name
        ''', (version_id,))
        planning = cursor.fetchall()
        cursor.close()
        conn.close()
        return planning
    
    @staticmethod
    def set_planning(version_id, match_id, player_ids):
        """Set planning for a specific match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Remove existing planning for this match in this version
        cursor.execute('''
            DELETE FROM match_planning 
            WHERE planning_version_id = %s AND match_id = %s
        ''', (version_id, match_id))
        
        # Add new planning
        for player_id in player_ids:
            cursor.execute('''
                INSERT INTO match_planning (planning_version_id, match_id, player_id) 
                VALUES (%s, %s, %s)
            ''', (version_id, match_id, player_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def pin_match(version_id, match_id, pinned=True):
        """Pin or unpin a match to preserve its planning."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE match_planning 
            SET is_pinned = %s
            WHERE planning_version_id = %s AND match_id = %s
        ''', (pinned, version_id, match_id))
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def get_pinned_matches(version_id):
        """Get all pinned matches for a version."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT match_id 
            FROM match_planning 
            WHERE planning_version_id = %s AND is_pinned = TRUE
        ''', (version_id,))
        matches = cursor.fetchall()
        cursor.close()
        conn.close()
        return [match['match_id'] for match in matches]
    
    @staticmethod
    def clear_planning(version_id, match_id=None):
        """Clear planning for a version (optionally for specific match)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if match_id:
            cursor.execute('''
                DELETE FROM match_planning 
                WHERE planning_version_id = %s AND match_id = %s
            ''', (version_id, match_id))
        else:
            cursor.execute('''
                DELETE FROM match_planning 
                WHERE planning_version_id = %s
            ''', (version_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def get_player_stats(version_id, player_id):
        """Get statistics for a player in a specific version."""
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
            WHERE mp.planning_version_id = %s AND mp.player_id = %s
        ''', (version_id, player_id))
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


class AutoPlanningService:
    """Service for automatic planning generation."""
    
    @staticmethod
    def generate_planning(version_id, constraints=None):
        """Generate automatic planning for a version following planning rules."""
        from app.models.match import Match
        from app.models.player import Player
        
        # Get all matches for this planning version
        matches = Match.get_all()
        if not matches:
            return {
                'status': 'error',
                'message': 'No matches found to plan',
                'matches_planned': 0
            }
        
        # Get all active players
        players = Player.get_all()
        if not players:
            return {
                'status': 'error', 
                'message': 'No players found to assign',
                'matches_planned': 0
            }
        
        # Initialize match counts per player for fair distribution
        player_match_counts = {}
        for player in players:
            player_match_counts[player['id']] = 0
        
        matches_planned = 0
        
        # Process each match according to planning rules
        for match in matches:
            # Apply planning rules for this match
            selected_players = AutoPlanningService._select_players_for_match(
                match, players, player_match_counts
            )
            
            if len(selected_players) > 0:
                # Set the planning for this match
                player_ids = [p['id'] for p in selected_players]
                MatchPlanning.set_planning(version_id, match['id'], player_ids)
                
                # Update match counts for fair distribution
                for player in selected_players:
                    player_match_counts[player['id']] += 1
                
                matches_planned += 1
        
        return {
            'status': 'success',
            'message': f'Planning generated for {matches_planned} matches following planning rules',
            'matches_planned': matches_planned
        }
    
    @staticmethod
    def generate_planning_selective(version_id, exclude_pinned=False):
        """Generate planning selectively following planning rules, optionally excluding pinned matches."""
        from app.models.match import Match
        from app.models.player import Player
        
        # Get all matches for this planning version
        matches = Match.get_all()
        if not matches:
            return {
                'status': 'error',
                'message': 'No matches found to plan',
                'matches_planned': 0
            }
        
        # Get all active players
        players = Player.get_all()
        if not players:
            return {
                'status': 'error', 
                'message': 'No players found to assign',
                'matches_planned': 0
            }
        
        # Get pinned matches if we need to exclude them
        pinned_match_ids = set()
        if exclude_pinned:
            pinned_matches = MatchPlanning.get_pinned_matches(version_id)
            pinned_match_ids = {row['match_id'] for row in pinned_matches}
        
        # Get current match counts per player for fair distribution
        player_match_counts = {}
        existing_planning = MatchPlanning.get_version_planning(version_id)
        
        # Initialize counts
        for player in players:
            player_match_counts[player['id']] = 0
        
        # Count existing matches per player
        for planning_entry in existing_planning:
            player_id = planning_entry['player_id']
            if player_id in player_match_counts:
                player_match_counts[player_id] += 1
        
        matches_planned = 0
        
        # Process each match according to planning rules
        for match in matches:
            # Skip pinned matches if requested
            if exclude_pinned and match['id'] in pinned_match_ids:
                continue
            
            # Apply planning rules for this match
            selected_players = AutoPlanningService._select_players_for_match(
                match, players, player_match_counts
            )
            
            if len(selected_players) > 0:
                # Set the planning for this match
                player_ids = [p['id'] for p in selected_players]
                MatchPlanning.set_planning(version_id, match['id'], player_ids)
                
                # Update match counts for fair distribution
                for player in selected_players:
                    player_match_counts[player['id']] += 1
                
                matches_planned += 1
        
        return {
            'status': 'success',
            'message': f'Planning generated for {matches_planned} matches following planning rules',
            'matches_planned': matches_planned
        }

    @staticmethod
    def _select_players_for_match(match, all_players, player_match_counts):
        """Select exactly 4 players for a match following planning rules."""
        import random
        from datetime import datetime, date
        from app.models.player import Player
        
        # Rule 1: Filter available players based on player availability
        available_players = []
        for player in all_players:
            # Check if player has marked themselves as unavailable for this match
            availability = Player.get_availability(player['id'], match['id'])
            is_available = not availability or availability.get('is_available', True)
            
            if is_available:
                available_players.append(player)
        
        if len(available_players) < 4:
            # Not enough available players - add some unavailable ones to reach minimum
            unavailable_players = [p for p in all_players if p not in available_players]
            # Sort unavailable by lowest match count
            unavailable_players.sort(key=lambda p: player_match_counts.get(p['id'], 0))
            
            # Add unavailable players to reach 4 total if possible
            needed = 4 - len(available_players)
            available_players.extend(unavailable_players[:needed])
        
        # Rule 2: Sort players by match count for fair distribution (least matches first)
        available_players.sort(key=lambda p: player_match_counts.get(p['id'], 0))
        
        # Rule 3: Partner preferences (simplified - would need partner data from database)
        # TODO: Implement partner preference logic when partner data is available
        
        # Rule 4: Home/Away balance - prefer players who need more of this match type
        is_home_match = match.get('is_home', True)
        # TODO: Implement home/away balance logic when match history is available
        
        # Rule 5: Select exactly 4 players - prioritize those with fewest matches
        # Take the 6 players with fewest matches, then randomly select 4 from them
        # This balances fair distribution with some randomness
        candidates = available_players[:min(6, len(available_players))]
        
        if len(candidates) <= 4:
            return candidates
        else:
            # Randomly select 4 from the candidates with lowest match counts
            return random.sample(candidates, 4)
    
    @staticmethod
    def optimize_planning(version_id):
        """Optimize existing planning to improve fairness and constraints."""
        # Implementation would go here
        return {
            'status': 'success',
            'message': 'Planning optimization not yet implemented',
            'improvements': 0
        }
