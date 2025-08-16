#!/usr/bin/env python3
"""
Test script voor de regeneratie functie
Direct test zonder web interface
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.single_planning import SinglePlanning

def test_regeneration():
    """Test de regeneratie functie direct"""
    print("🧪 TESTING REGENERATION FUNCTION")
    print("=" * 50)
    
    try:
        # Call regeneration function
        result = SinglePlanning.regenerate_planning(exclude_pinned=True)
        
        print("\n📊 RESULT:")
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        
        if result['success']:
            print(f"Matches processed: {result.get('regenerated_matches', 0)}")
            print(f"New assignments: {result.get('new_assignments', 0)}")
            print(f"Rule violations: {len(result.get('rule_violations', []))}")
            
            if result.get('rule_violations'):
                print("\n⚠️ RULE VIOLATIONS:")
                for violation in result['rule_violations']:
                    print(f"  - {violation}")
            
            print(f"\n👥 PLAYER STATS:")
            for name, count in result.get('player_stats', {}).items():
                print(f"  - {name}: {count} matches")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_regeneration()
    exit(0 if success else 1)
