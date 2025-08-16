"""
Test script for Issue #22 Single Planning System
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.single_planning import SinglePlanning
from app.models.player import Player
from app.models.match import Match

def test_single_planning():
    """Test the single planning system functionality."""
    print("🧪 Testing Single Planning System...")
    
    try:
        # Test 1: Initialize planning
        print("\n1. Initializing single planning...")
        SinglePlanning.initialize_planning()
        print("✅ Planning initialized")
        
        # Test 2: Get all players and matches
        print("\n2. Getting players and matches...")
        players = Player.get_all()
        matches = Match.get_all()
        print(f"✅ Found {len(players)} players and {len(matches)} matches")
        
        if not matches:
            print("❌ No matches found. Please import matches first.")
            return False
        
        if len([p for p in players if p.get('is_active', True)]) < 4:
            print("❌ Need at least 4 active players for testing.")
            return False
        
        # Test 3: Generate initial planning
        print("\n3. Generating initial planning...")
        result = SinglePlanning.generate_initial_planning()
        print(f"✅ Initial planning generated: {result}")
        
        # Test 4: Get planning
        print("\n4. Getting current planning...")
        planning = SinglePlanning.get_planning()
        print(f"✅ Retrieved planning with {len(planning)} entries")
        
        # Test 5: Test match planning
        if matches:
            match_id = matches[0]['id']
            print(f"\n5. Testing match planning for match {match_id}...")
            
            match_planning = SinglePlanning.get_match_planning(match_id)
            print(f"✅ Match has {len(match_planning)} players assigned")
            
            if match_planning:
                player_id = match_planning[0]['player_id']
                
                # Test pinning
                print(f"   - Testing pin player {player_id}...")
                SinglePlanning.pin_player(match_id, player_id, True)
                
                # Test actually played
                print(f"   - Testing actually played for player {player_id}...")
                SinglePlanning.set_actually_played(match_id, player_id, True)
                
                # Test match played status
                print(f"   - Testing match played status...")
                SinglePlanning.set_match_played(match_id, True)
                
                print("✅ All match operations completed")
        
        # Test 6: Get player stats
        if players:
            player_id = players[0]['id']
            print(f"\n6. Getting stats for player {player_id}...")
            stats = SinglePlanning.get_player_stats(player_id)
            print(f"✅ Player stats: {stats}")
        
        # Test 7: Test regeneration
        print("\n7. Testing planning regeneration...")
        result = SinglePlanning.regenerate_planning(exclude_pinned=True)
        print(f"✅ Regeneration result: {result}")
        
        print("\n🎉 All tests passed! Single Planning System is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_single_planning()
    sys.exit(0 if success else 1)
