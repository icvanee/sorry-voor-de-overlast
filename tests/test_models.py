import pytest
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.player import Player
from app.services.planning import PlanningVersion, MatchPlanning
from app.models.match import Match
from app.models.database import get_db_connection

class TestPlayer:
    """Test suite for Player model - PostgreSQL only"""
    
    def test_get_all_players(self):
        """Test getting all active players"""
        players = Player.get_all()
        assert isinstance(players, list)
        # Should only return active players
        for player in players:
            assert player.get('is_active') is True or player.get('is_active') == True
    
    def test_get_player_by_id(self):
        """Test getting a specific player by ID"""
        players = Player.get_all()
        if players:
            player_id = players[0]['id']
            player = Player.get_by_id(player_id)
            assert player is not None
            assert player['id'] == player_id
    
    def test_create_and_update_player(self):
        """Test creating and updating a player"""
        # Create test player
        player_id = Player.create(
            name="Test Speler",
            email="test@example.com",
            role="speler"
        )
        assert player_id is not None
        
        # Verify created player
        player = Player.get_by_id(player_id)
        assert player['name'] == "Test Speler"
        assert player['email'] == "test@example.com"
        assert player['role'] == "speler"
        
        # Update player
        Player.update(player_id, name="Updated Speler", role="captain")
        
        # Verify update
        updated_player = Player.get_by_id(player_id)
        assert updated_player['name'] == "Updated Speler"
        assert updated_player['role'] == "captain"
        
        # Clean up
        Player.delete(player_id)
    
    def test_partner_preference(self):
        """Test partner preference functionality"""
        # Create test player
        player_id = Player.create(name="Test Partner Preference")
        
        # Test setting preference
        Player.set_partner_preference(player_id, False)
        preference = Player.get_partner_preference(player_id)
        assert preference is False
        
        Player.set_partner_preference(player_id, True)
        preference = Player.get_partner_preference(player_id)
        assert preference is True
        
        # Clean up
        Player.delete(player_id)
    
    def test_deactivate_activate_player(self):
        """Test player deactivation and activation"""
        # Create test player
        player_id = Player.create(name="Test Deactivation")
        
        # Deactivate
        Player.deactivate(player_id)
        player = Player.get_by_id(player_id)
        assert player['is_active'] is False
        
        # Should not appear in get_all() (active only)
        active_players = Player.get_all()
        active_ids = [p['id'] for p in active_players]
        assert player_id not in active_ids
        
        # Activate
        Player.activate(player_id)
        player = Player.get_by_id(player_id)
        assert player['is_active'] is True
        
        # Clean up
        Player.delete(player_id)


class TestPlanningVersion:
    """Test suite for PlanningVersion model - PostgreSQL only"""
    
    def test_get_all_versions(self):
        """Test getting all planning versions"""
        versions = PlanningVersion.get_all()
        assert isinstance(versions, list)
    
    def test_create_and_get_version(self):
        """Test creating and retrieving a planning version"""
        # Create test version
        version_id = PlanningVersion.create(
            name="Test Version",
            description="Test planning version"
        )
        assert version_id is not None
        
        # Retrieve version
        version = PlanningVersion.get_by_id(version_id)
        assert version is not None
        assert version['name'] == "Test Version"
        assert version['description'] == "Test planning version"
        assert version['deleted_at'] is None
        
        # Clean up
        PlanningVersion.delete(version_id)
    
    def test_soft_delete_and_restore(self):
        """Test soft delete and restore functionality"""
        # Create test version
        version_id = PlanningVersion.create(name="Test Soft Delete")
        
        # Soft delete
        PlanningVersion.soft_delete(version_id)
        assert PlanningVersion.is_deleted(version_id) is True
        
        # Restore
        PlanningVersion.restore(version_id)
        assert PlanningVersion.is_deleted(version_id) is False
        
        # Clean up
        PlanningVersion.delete(version_id)
    
    def test_copy_version(self):
        """Test copying a planning version"""
        # Create source version
        source_id = PlanningVersion.create(name="Source Version")
        
        # Copy version
        new_id = PlanningVersion.copy_from_version(
            source_version_id=source_id,
            name="Copied Version",
            description="Copied from source"
        )
        assert new_id is not None
        assert new_id != source_id
        
        # Verify copied version
        copied_version = PlanningVersion.get_by_id(new_id)
        assert copied_version['name'] == "Copied Version"
        assert copied_version['description'] == "Copied from source"
        
        # Clean up
        PlanningVersion.delete(source_id)
        PlanningVersion.delete(new_id)


class TestMatchPlanning:
    """Test suite for MatchPlanning model - PostgreSQL only"""
    
    def test_get_and_set_planning(self):
        """Test getting and setting match planning"""
        # Get a test version and match
        versions = PlanningVersion.get_all()
        matches = Match.get_all()
        players = Player.get_all()
        
        if not versions or not matches or not players:
            pytest.skip("No test data available")
        
        version_id = versions[0]['id']
        match_id = matches[0]['id']
        player_ids = [players[0]['id'], players[1]['id']] if len(players) > 1 else [players[0]['id']]
        
        # Set planning
        MatchPlanning.set_planning(version_id, match_id, player_ids)
        
        # Get planning
        planning = MatchPlanning.get_planning(version_id, match_id)
        planning_player_ids = [p['player_id'] for p in planning]
        
        for player_id in player_ids:
            assert player_id in planning_player_ids
    
    def test_pin_match(self):
        """Test pinning and unpinning matches"""
        # Get test data
        versions = PlanningVersion.get_all()
        matches = Match.get_all()
        
        if not versions or not matches:
            pytest.skip("No test data available")
        
        version_id = versions[0]['id']
        match_id = matches[0]['id']
        
        # Pin match
        MatchPlanning.pin_match(version_id, match_id, True)
        pinned_matches = MatchPlanning.get_pinned_matches(version_id)
        assert match_id in pinned_matches
        
        # Unpin match
        MatchPlanning.pin_match(version_id, match_id, False)
        pinned_matches = MatchPlanning.get_pinned_matches(version_id)
        assert match_id not in pinned_matches


class TestDatabaseConnection:
    """Test database connection and basic queries"""
    
    def test_connection(self):
        """Test that we can connect to PostgreSQL"""
        conn = get_db_connection()
        assert conn is not None
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        assert result['test'] == 1
        
        cursor.close()
        conn.close()
    
    def test_tables_exist(self):
        """Test that required tables exist"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check key tables exist
        tables_to_check = ['players', 'matches', 'planning_versions', 'match_planning', 'player_availability']
        
        for table in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table,))
            result = cursor.fetchone()
            exists = result['exists']
            assert exists, f"Table {table} does not exist"
        
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
