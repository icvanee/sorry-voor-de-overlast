import pytest
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.player import Player
# Legacy planning imports removed - single planning system doesn't need these
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


# Legacy planning tests removed - single planning system doesn't need these classes
# TestPlanningVersion and TestMatchPlanning are obsolete

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
        tables_to_check = ['players', 'matches', 'match_planning', 'player_availability']
        
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
