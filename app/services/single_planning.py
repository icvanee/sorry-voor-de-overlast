"""
Single Planning System - Issue #22
Simplified planning system with one planning, pinning, regeneration and match tracking.
"""
from app.models.database import get_db_connection
from app.models.player import Player
from app.models.match import Match
from datetime import datetime
import random

class SinglePlanning:
    """
    Single planning system that replaces the multi-version approach.
    Features:
    - One unified planning for all matches
    - Pin individual players or entire matches
    - Regenerate planning while preserving pinned items
    - Track match completion and actual players
    - Support 5th player when needed
    """
    
    @staticmethod
    def get_planning():
        """Get the current single planning for all matches."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                mp.*,
                p.name as player_name,
                p.role,
                m.match_date,
                m.home_team,
                m.away_team,
                m.is_home,
                m.is_played
            FROM match_planning mp
            JOIN players p ON mp.player_id = p.id
            JOIN matches m ON mp.match_id = m.id
            WHERE mp.planning_version_id = 1  -- Single planning uses version_id = 1
            ORDER BY m.match_date, p.name
        ''')
        planning = cursor.fetchall()
        cursor.close()
        conn.close()
        return planning
    
    @staticmethod
    def get_match_planning(match_id):
        """Get planning for a specific match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                mp.*,
                p.name as player_name,
                p.role
            FROM match_planning mp
            JOIN players p ON mp.player_id = p.id
            WHERE mp.planning_version_id = 1 AND mp.match_id = %s
            ORDER BY p.name
        ''', (match_id,))
        planning = cursor.fetchall()
        cursor.close()
        conn.close()
        return planning
    
    @staticmethod
    def set_match_planning(match_id, player_ids, preserve_pinned=True):
        """
        Set planning for a specific match.
        
        Args:
            match_id: ID of the match
            player_ids: List of player IDs to assign
            preserve_pinned: If True, keep existing pinned players
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if preserve_pinned:
            # Get currently pinned players for this match
            cursor.execute('''
                SELECT player_id FROM match_planning
                WHERE planning_version_id = 1 AND match_id = %s AND is_pinned = true
            ''', (match_id,))
            pinned_players = [row['player_id'] for row in cursor.fetchall()]
            
            # Remove only non-pinned players
            cursor.execute('''
                DELETE FROM match_planning 
                WHERE planning_version_id = 1 AND match_id = %s AND is_pinned = false
            ''', (match_id,))
            
            # Add new players (excluding already pinned ones)
            for player_id in player_ids:
                if player_id not in pinned_players:
                    cursor.execute('''
                        INSERT INTO match_planning (planning_version_id, match_id, player_id)
                        VALUES (1, %s, %s)
                        ON CONFLICT (planning_version_id, match_id, player_id) DO NOTHING
                    ''', (match_id, player_id))
        else:
            # Replace all players (ignore pinning)
            cursor.execute('''
                DELETE FROM match_planning 
                WHERE planning_version_id = 1 AND match_id = %s
            ''', (match_id,))
            
            for player_id in player_ids:
                cursor.execute('''
                    INSERT INTO match_planning (planning_version_id, match_id, player_id)
                    VALUES (1, %s, %s)
                ''', (match_id, player_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def pin_player(match_id, player_id, pinned=True):
        """Pin or unpin a specific player for a match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE match_planning 
            SET is_pinned = %s
            WHERE planning_version_id = 1 AND match_id = %s AND player_id = %s
        ''', (pinned, match_id, player_id))
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def pin_match(match_id, pinned=True):
        """Pin or unpin all players for a match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE match_planning 
            SET is_pinned = %s
            WHERE planning_version_id = 1 AND match_id = %s
        ''', (pinned, match_id))
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def set_actually_played(match_id, player_id, actually_played=True):
        """Mark a player as actually played for a match."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE match_planning 
            SET actually_played = %s
            WHERE planning_version_id = 1 AND match_id = %s AND player_id = %s
        ''', (actually_played, match_id, player_id))
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def set_match_played(match_id, played=True):
        """Mark a match as played or not played."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE matches 
            SET is_played = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (played, match_id))
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def get_player_stats(player_id):
        """Get statistics for a player in the current planning."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as matches_planned,
                COUNT(CASE WHEN m.is_home = true THEN 1 END) as home_matches,
                COUNT(CASE WHEN m.is_home = false THEN 1 END) as away_matches,
                COUNT(CASE WHEN mp.actually_played = true THEN 1 END) as matches_played,
                COUNT(CASE WHEN m.is_played = true THEN 1 END) as completed_matches
            FROM match_planning mp
            JOIN matches m ON mp.match_id = m.id
            WHERE mp.planning_version_id = 1 AND mp.player_id = %s
        ''', (player_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                'matches_planned': result['matches_planned'] or 0,
                'home_matches': result['home_matches'] or 0,
                'away_matches': result['away_matches'] or 0,
                'matches_played': result['matches_played'] or 0,
                'completed_matches': result['completed_matches'] or 0
            }
        return {
            'matches_planned': 0,
            'home_matches': 0,
            'away_matches': 0,
            'matches_played': 0,
            'completed_matches': 0
        }
    
    @staticmethod
    def regenerate_planning(exclude_pinned=True):
        """
        🎯 KERNFUNCTIE: Volledige planning regeneratie volgens alle regels
        
        BUSINESS RULES:
        1. PRECIES 4 SPELERS PER WEDSTRIJD (harde regel)
        2. ALLEEN BESCHIKBARE SPELERS (check player_availability)
        3. GEEN DUBBELE PLANNING (speler kan niet 2x op zelfde datum)
        4. EERLIJKE VERDELING (spelers met minste wedstrijden krijgen prioriteit)
        5. VASTGEPINDE SPELERS blijven op hun plek
        6. PARTNER VOORKEUREN waar mogelijk
        7. THUIS/UIT BALANS per speler
        
        Args:
            exclude_pinned: Als True, behoud vastgepinde spelers
        """
        print("=" * 80)
        print("🎯 STARTING COMPLETE PLANNING REGENERATION")
        print("=" * 80)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # === STAP 1: DATA VERZAMELEN ===
            print("\n📊 STEP 1: GATHERING DATA...")
            
            # Get alle matches
            cursor.execute('SELECT * FROM matches ORDER BY match_date, id')
            all_matches = cursor.fetchall()
            unplayed_matches = [m for m in all_matches if not m.get('is_played', False)]
            
            # Get alle active players
            cursor.execute('SELECT * FROM players WHERE is_active = TRUE ORDER BY name')
            active_players = cursor.fetchall()
            
            print(f"   � Total matches: {len(all_matches)} | Unplayed: {len(unplayed_matches)}")
            print(f"   👥 Active players: {len(active_players)}")
            
            if not unplayed_matches or not active_players:
                return {'success': False, 'message': 'Geen wedstrijden of actieve spelers gevonden'}
            
            # === STAP 2: VERZAMEL AVAILABILITY DATA ===
            print("\n📋 STEP 2: COLLECTING AVAILABILITY...")
            
            # Get player availability per match
            cursor.execute('''
                SELECT player_id, match_id, is_available, notes 
                FROM player_availability
            ''')
            availability_data = cursor.fetchall()
            
            # Build availability lookup
            availability = {}
            for avail in availability_data:
                player_id = avail['player_id']
                match_id = avail['match_id']
                if player_id not in availability:
                    availability[player_id] = {}
                availability[player_id][match_id] = avail
            
            print(f"   📊 Availability entries: {len(availability_data)}")
            
            # === STAP 3: VERZAMEL PINNED ASSIGNMENTS ===
            print("\n📌 STEP 3: COLLECTING PINNED ASSIGNMENTS...")
            
            pinned_assignments = {}
            if exclude_pinned:
                cursor.execute('''
                    SELECT match_id, player_id, player_id as pid
                    FROM match_planning mp
                    JOIN players p ON mp.player_id = p.id
                    WHERE mp.planning_version_id = 1 AND mp.is_pinned = TRUE AND p.is_active = TRUE
                ''')
                pinned_data = cursor.fetchall()
                
                for pin in pinned_data:
                    match_id = pin['match_id']
                    player_id = pin['player_id']
                    if match_id not in pinned_assignments:
                        pinned_assignments[match_id] = []
                    pinned_assignments[match_id].append(player_id)
                
                print(f"   📌 Pinned assignments: {sum(len(players) for players in pinned_assignments.values())}")
                for match_id, players in pinned_assignments.items():
                    print(f"      Match {match_id}: {len(players)} pinned players")
            
            # === STAP 4: CLEAR ALLE NON-PINNED ASSIGNMENTS ===
            print("\n🗑️ STEP 4: CLEARING NON-PINNED ASSIGNMENTS...")
            
            if exclude_pinned:
                cursor.execute('''
                    DELETE FROM match_planning 
                    WHERE planning_version_id = 1 AND is_pinned = FALSE
                ''')
                deleted = cursor.rowcount
                print(f"   🗑️ Deleted {deleted} non-pinned assignments")
            else:
                cursor.execute('DELETE FROM match_planning WHERE planning_version_id = 1')
                deleted = cursor.rowcount
                print(f"   🗑️ Deleted {deleted} total assignments")
                pinned_assignments = {}
            
            conn.commit()
            
            # === STAP 5: INITIALIZE PLAYER MATCH COUNTS ===
            print("\n📈 STEP 5: INITIALIZING PLAYER COUNTERS...")
            
            player_match_counts = {p['id']: 0 for p in active_players}
            player_home_counts = {p['id']: 0 for p in active_players}
            player_away_counts = {p['id']: 0 for p in active_players}
            
            # Count pinned matches
            for match_id, player_ids in pinned_assignments.items():
                # Find match info
                match_info = next((m for m in unplayed_matches if m['id'] == match_id), None)
                if match_info:
                    for player_id in player_ids:
                        if player_id in player_match_counts:
                            player_match_counts[player_id] += 1
                            if match_info.get('is_home', False):
                                player_home_counts[player_id] += 1
                            else:
                                player_away_counts[player_id] += 1
            
            print(f"   � Initial match counts (from pinned): {dict(list(player_match_counts.items())[:3])}...")
            
            # === STAP 6: GENERATE COMPLETE PLANNING ===
            print("\n🎯 STEP 6: GENERATING COMPLETE PLANNING...")
            
            regenerated_count = 0
            total_assignments = 0
            rule_violations = []
            
            for match in unplayed_matches:
                match_id = match['id']
                match_date = match.get('match_date')
                is_home = match.get('is_home', False)
                home_team = match.get('home_team', 'Unknown')
                away_team = match.get('away_team', 'Unknown')
                
                print(f"\n   � Processing Match {match_id}: {home_team} vs {away_team}")
                print(f"      📅 Date: {match_date} | {'🏠 Home' if is_home else '✈️ Away'}")
                
                # Get existing pinned players
                existing_pinned = pinned_assignments.get(match_id, [])
                needed_players = 4 - len(existing_pinned)
                
                print(f"      📌 Pinned: {len(existing_pinned)} | Need: {needed_players} more")
                
                if needed_players > 0:
                    # === RULE 1: Filter available players ===
                    candidates = []
                    
                    for player in active_players:
                        player_id = player['id']
                        
                        # Skip if already pinned for this match
                        if player_id in existing_pinned:
                            continue
                            
                        # RULE 2: Check availability
                        player_avail = availability.get(player_id, {}).get(match_id, {})
                        is_available = player_avail.get('is_available', True)  # Default available
                        
                        # RULE 3: Check for date conflicts (no double bookings)
                        date_conflict = False
                        if match_date:
                            # Check if player is already assigned to another match on same date
                            cursor.execute('''
                                SELECT COUNT(*) as conflicts FROM match_planning mp
                                JOIN matches m ON mp.match_id = m.id
                                WHERE mp.planning_version_id = 1 
                                AND mp.player_id = %s 
                                AND m.match_date = %s
                                AND m.id != %s
                            ''', (player_id, match_date, match_id))
                            conflicts = cursor.fetchone()['conflicts']
                            date_conflict = conflicts > 0
                        
                        if is_available and not date_conflict:
                            candidates.append({
                                'player': player,
                                'match_count': player_match_counts[player_id],
                                'home_count': player_home_counts[player_id],
                                'away_count': player_away_counts[player_id],
                                'available': True
                            })
                        else:
                            print(f"         ❌ {player['name']}: {'unavailable' if not is_available else 'date conflict'}")
                    
                    print(f"      ✅ Available candidates: {len(candidates)}")
                    
                    # === RULE 4: Sort by fairness (least matches first) ===
                    candidates.sort(key=lambda c: (
                        c['match_count'],  # Primary: fewest total matches
                        abs(c['home_count'] - c['away_count']) if is_home else -abs(c['home_count'] - c['away_count']),  # Secondary: balance home/away
                        c['player']['name']  # Tertiary: alphabetical for consistency
                    ))
                    
                    # Select the best candidates
                    selected_count = min(needed_players, len(candidates))
                    selected_candidates = candidates[:selected_count]
                    
                    print(f"      ⭐ Selected {selected_count} players:")
                    
                    # Add assignments to database
                    for candidate in selected_candidates:
                        player = candidate['player']
                        player_id = player['id']
                        
                        cursor.execute('''
                            INSERT INTO match_planning (planning_version_id, match_id, player_id, is_pinned, actually_played)
                            VALUES (1, %s, %s, FALSE, FALSE)
                        ''', (match_id, player_id))
                        
                        # Update counters
                        player_match_counts[player_id] += 1
                        if is_home:
                            player_home_counts[player_id] += 1
                        else:
                            player_away_counts[player_id] += 1
                        
                        total_assignments += 1
                        print(f"         ✅ {player['name']} (total: {player_match_counts[player_id]})")
                    
                    # Check for rule violations
                    total_players = len(existing_pinned) + selected_count
                    if total_players != 4:
                        rule_violations.append({
                            'match_id': match_id,
                            'match_name': f"{home_team} vs {away_team}",
                            'player_count': total_players,
                            'issue': f"{'Insufficient players' if total_players < 4 else 'Too many players'}"
                        })
                        print(f"      ⚠️ RULE VIOLATION: {total_players} players (should be 4)")
                
                regenerated_count += 1
            
            conn.commit()
            
            # === STAP 7: FINAL STATISTICS ===
            print("\n" + "=" * 80)
            print("📊 REGENERATION COMPLETE - FINAL STATISTICS")
            print("=" * 80)
            
            print(f"📈 Processed matches: {regenerated_count}")
            print(f"📈 Total new assignments: {total_assignments}")
            print(f"📈 Rule violations: {len(rule_violations)}")
            
            print(f"\n� Final player distribution:")
            for player in active_players:
                player_id = player['id']
                total = player_match_counts[player_id]
                home = player_home_counts[player_id]
                away = player_away_counts[player_id]
                print(f"   {player['name']}: {total} total ({home}H/{away}A)")
            
            if rule_violations:
                print(f"\n⚠️ RULE VIOLATIONS:")
                for violation in rule_violations:
                    print(f"   Match {violation['match_id']} ({violation['match_name']}): {violation['player_count']} players - {violation['issue']}")
            
            cursor.close()
            conn.close()
            
            print("=" * 80)
            print("✅ REGENERATION SUCCESSFULLY COMPLETED")
            print("=" * 80)
            
            return {
                'success': True,
                'message': f'Complete planning regenerated! {regenerated_count} matches processed, {total_assignments} new assignments',
                'regenerated_matches': regenerated_count,
                'new_assignments': total_assignments,
                'rule_violations': rule_violations,
                'player_stats': {p['name']: player_match_counts[p['id']] for p in active_players}
            }
            
        except Exception as e:
            print(f"\n❌ REGENERATION FAILED: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Regeneration failed: {str(e)}'}
    
    
    @staticmethod
    def _select_players_smart(available_players, player_match_counts, match, num_players):
        """
        Smart player selection following the established planning rules.
        
        Args:
            available_players: List of available player dictionaries
            player_match_counts: Dict of player_id -> match_count
            match: Match dictionary with match details
            num_players: Number of players to select
        """
        if len(available_players) <= num_players:
            return available_players
        
        # Rule 1: Check availability (if available)
        available_for_match = []
        for player in available_players:
            # Check if player has marked themselves as unavailable
            availability = Player.get_availability(player['id'], match['id'])
            is_available = not availability or availability.get('is_available', True)
            
            if is_available:
                available_for_match.append(player)
        
        # If not enough available players, use all available + some unavailable
        if len(available_for_match) < num_players:
            unavailable_players = [p for p in available_players if p not in available_for_match]
            unavailable_players.sort(key=lambda p: player_match_counts.get(p['id'], 0))
            needed = num_players - len(available_for_match)
            available_for_match.extend(unavailable_players[:needed])
        
        # Rule 2: Sort by match count for fair distribution (least matches first)
        available_for_match.sort(key=lambda p: player_match_counts.get(p['id'], 0))
        
        # Rule 3: Partner preferences (simplified - would need partner data)
        # TODO: Implement when partner preference logic is needed
        
        # Rule 4: Home/Away balance consideration
        # TODO: Implement home/away balance when needed
        
        # Rule 5: Select players - prioritize those with fewest matches
        # Take top candidates and add some randomness for variety
        candidates = available_for_match[:min(num_players + 2, len(available_for_match))]
        
        if len(candidates) <= num_players:
            return candidates
        else:
            # Randomly select from candidates with slight bias toward fewer matches
            return candidates[:num_players]  # For now, just take the lowest match counts
    
    @staticmethod
    def initialize_planning():
        """Initialize the single planning system by creating initial planning version."""
        # Ensure we have a planning version with ID 1 for the single planning
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if single planning version exists
        cursor.execute('SELECT id FROM planning_versions WHERE id = 1')
        version = cursor.fetchone()
        
        if not version:
            # Create the single planning version
            cursor.execute('''
                INSERT INTO planning_versions (id, name, description, is_final, created_at)
                VALUES (1, 'Master Planning', 'Single unified planning for all matches', false, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO NOTHING
            ''')
            conn.commit()
        
        cursor.close()
        conn.close()
    
    @staticmethod
    def generate_initial_planning():
        """Generate initial planning for all matches."""
        SinglePlanning.initialize_planning()
        return SinglePlanning.regenerate_planning(exclude_pinned=False)
