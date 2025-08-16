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
        """Generate automatic planning for a version based on constraints."""
        # Implementation would go here - this is a complex algorithm
        # For now, return a simple result
        return {
            'status': 'success',
            'message': 'Auto planning not yet implemented',
            'matches_planned': 0
        }
    
    @staticmethod
    def optimize_planning(version_id):
        """Optimize existing planning to improve fairness and constraints."""
        # Implementation would go here
        return {
            'status': 'success',
            'message': 'Planning optimization not yet implemented',
            'improvements': 0
        }
