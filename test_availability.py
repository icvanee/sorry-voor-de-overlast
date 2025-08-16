#!/usr/bin/env python3
"""
Test script voor Issue #4 - Availability Endpoint Bug
Test de Player.get_availability en Player.set_availability methoden direct.
"""

from app.models.player import Player
from app.models.match import Match
from app.models.database import get_db_connection

def test_availability_methods():
    print("🧪 Test Issue #4 - Availability Endpoint Bug")
    print("=" * 60)
    
    # Test 1: Check if player exists
    print("\n1. Testing Player.get_by_id()...")
    player = Player.get_by_id(1)
    if player:
        print(f"   ✅ Player found: {player['name']} ({player['role']})")
    else:
        print("   ❌ Player ID=1 not found!")
        return False
    
    # Test 2: Check if matches exist
    print("\n2. Testing Match.get_all()...")
    matches = Match.get_all()
    if matches:
        print(f"   ✅ Found {len(matches)} matches")
        first_match = matches[0]
        print(f"   First match: ID={first_match['id']}, {first_match['home_team']} vs {first_match['away_team']}")
    else:
        print("   ❌ No matches found!")
        return False
    
    # Test 3: Test get_availability (before setting any)
    print("\n3. Testing Player.get_availability() - before setting...")
    player_id = 1
    match_id = first_match['id']
    availability = Player.get_availability(player_id, match_id)
    print(f"   Current availability for player {player_id}, match {match_id}: {availability}")
    
    # Test 4: Test set_availability
    print("\n4. Testing Player.set_availability()...")
    try:
        Player.set_availability(player_id, match_id, True, "Test beschikbaarheid via script")
        print("   ✅ set_availability() succeeded")
    except Exception as e:
        print(f"   ❌ set_availability() failed: {e}")
        return False
    
    # Test 5: Test get_availability (after setting)
    print("\n5. Testing Player.get_availability() - after setting...")
    availability = Player.get_availability(player_id, match_id)
    if availability:
        print(f"   ✅ Availability retrieved: is_available={availability['is_available']}, notes='{availability['notes']}'")
    else:
        print("   ❌ get_availability() returned None after setting!")
        return False
    
    # Test 6: Direct database check
    print("\n6. Direct database verification...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT player_id, match_id, is_available, notes 
        FROM player_availability 
        WHERE player_id = %s AND match_id = %s
    ''', (player_id, match_id))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        print(f"   ✅ Direct DB query: player_id={result['player_id']}, match_id={result['match_id']}")
        print(f"      is_available={result['is_available']}, notes='{result['notes']}'")
    else:
        print("   ❌ Direct DB query returned no results!")
        return False
    
    print("\n🎉 All availability method tests passed!")
    return True

if __name__ == "__main__":
    test_availability_methods()
