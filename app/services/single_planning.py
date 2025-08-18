"""
Single Planning System - Issue #22
Simplified planning system with one planning, pinning, regeneration and match tracking.
"""
from app.models.database import get_db_connection
from app.models.player import Player
from app.models.match import Match
from datetime import datetime
import random
from collections import defaultdict, deque

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
    def regenerate_planning(exclude_pinned=True, plan_mode='all', cutoff_date=None):
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
            plan_mode: 'all' | 'until_date' | 'from_date' (alias: 'rest')
            cutoff_date: str of datetime.date (YYYY-MM-DD) als grensdatum
        """
        print("=" * 80)
        print("🎯 STARTING COMPLETE PLANNING REGENERATION")
        print("=" * 80)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Ensure undo tables exist and snapshot current planning before any changes
            SinglePlanning._create_undo_tables(cursor)
            SinglePlanning._create_undo_snapshot(cursor, plan_mode, cutoff_date)
            conn.commit()
            
            # === STAP 1: DATA VERZAMELEN ===
            print("\n📊 STEP 1: GATHERING DATA...")
            
            # Get alle matches
            cursor.execute('SELECT * FROM matches ORDER BY match_date, id')
            all_matches = cursor.fetchall()
            unplayed_all = [m for m in all_matches if not m.get('is_played', False)]

            # Parse cutoff_date if provided
            cutoff_dt = None
            if cutoff_date:
                try:
                    if isinstance(cutoff_date, str):
                        cutoff_dt = datetime.strptime(cutoff_date, '%Y-%m-%d').date()
                    else:
                        cutoff_dt = cutoff_date
                except Exception as e:
                    print(f"   ⚠️ Invalid cutoff_date provided: {cutoff_date} ({e}) - ignoring")
                    cutoff_dt = None

            # Bepaal doel-wedstrijden op basis van plan_mode
            def match_in_scope(m):
                if not cutoff_dt:
                    return True
                mdate = m.get('match_date')
                try:
                    # mdate kan datetime of date zijn; normaliseer naar date
                    mdate_d = mdate.date() if hasattr(mdate, 'date') else mdate
                except Exception:
                    mdate_d = mdate
                if plan_mode in ('until_date',):
                    return mdate_d is None or (mdate_d <= cutoff_dt)
                if plan_mode in ('from_date', 'rest'):
                    return mdate_d is None or (mdate_d >= cutoff_dt)
                return True

            if plan_mode not in ('all', 'until_date', 'from_date', 'rest'):
                print(f"   ⚠️ Unknown plan_mode '{plan_mode}', defaulting to 'all'")
                plan_mode = 'all'

            target_matches = [m for m in unplayed_all if (plan_mode == 'all' or match_in_scope(m))]

            # Get alle active players
            cursor.execute('SELECT * FROM players WHERE is_active = TRUE ORDER BY name')
            active_players = cursor.fetchall()
            # Quick lookup by id for partner/preference checks
            players_by_id = {p['id']: p for p in active_players}
            
            print(f"   � Total matches: {len(all_matches)} | Unplayed: {len(unplayed_all)} | In scope: {len(target_matches)} (mode={plan_mode}, cutoff={cutoff_dt})")
            print(f"   👥 Active players: {len(active_players)}")
            
            if not target_matches or not active_players:
                return {'success': False, 'message': 'Geen wedstrijden of actieve spelers gevonden'}

            # === (OPTIONEEL) TUSSENSTAP: CLEAN AFTER CUTOFF FOR UNTIL_DATE MODE ===
            if plan_mode == 'until_date' and cutoff_dt:
                print("\n🧹 STEP 2b: CLEANING ASSIGNMENTS AFTER CUTOFF DATE (inclusive pinnen)...")
                cursor.execute('''
                    DELETE FROM match_planning mp
                    USING matches m
                    WHERE mp.planning_version_id = 1
                      AND mp.match_id = m.id
                      AND m.match_date > %s
                ''', (cutoff_dt,))
                cleaned = cursor.rowcount
                conn.commit()
                print(f"   🧹 Deleted {cleaned} assignments after {cutoff_dt}")
            
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
            
            # Beperk verwijdering tot doelwedstrijden om buiten scope niets te wijzigen
            target_match_ids = [m['id'] for m in target_matches]
            if target_match_ids:
                if exclude_pinned:
                    cursor.execute('''
                        DELETE FROM match_planning 
                        WHERE planning_version_id = 1 AND is_pinned = FALSE AND match_id = ANY(%s)
                    ''', (target_match_ids,))
                    deleted = cursor.rowcount
                    print(f"   🗑️ Deleted {deleted} non-pinned assignments in scope")
                else:
                    cursor.execute('''
                        DELETE FROM match_planning 
                        WHERE planning_version_id = 1 AND match_id = ANY(%s)
                    ''', (target_match_ids,))
                    deleted = cursor.rowcount
                    print(f"   🗑️ Deleted {deleted} total assignments in scope")
                    pinned_assignments = {k: v for k, v in pinned_assignments.items() if k not in set(target_match_ids)}
            
            conn.commit()
            
            # === STAP 5: INITIALIZE PLAYER MATCH COUNTS & RECENT PLAY TRACKING ===
            print("\n📈 STEP 5: INITIALIZING PLAYER COUNTERS...")
            
            player_match_counts = {p['id']: 0 for p in active_players}
            player_home_counts = {p['id']: 0 for p in active_players}
            player_away_counts = {p['id']: 0 for p in active_players}
            
            # Track recent matches for variatie (last 3 matches played by each player)
            recent_matches_by_player = {p['id']: [] for p in active_players}
            
            # Count pinned matches across alle ongespeelde wedstrijden (niet alleen scope)
            for match_id, player_ids in pinned_assignments.items():
                # Find match info in alle ongespeelde
                match_info = next((m for m in unplayed_all if m['id'] == match_id), None)
                if match_info:
                    for player_id in player_ids:
                        if player_id in player_match_counts:
                            player_match_counts[player_id] += 1
                            if match_info.get('is_home', False):
                                player_home_counts[player_id] += 1
                            else:
                                player_away_counts[player_id] += 1
            
            print(f"   � Initial match counts (from pinned): {dict(list(player_match_counts.items())[:3])}...")
            
            # === STAP 5b: FAIRNESS CAPS PER SPELER (BINNEN SCOPE) ===
            print("\n⚖️ STEP 5b: COMPUTING FAIRNESS CAPS...")
            total_slots_target = len(target_matches) * 4
            pinned_in_target_total = sum(len(pinned_assignments.get(m['id'], [])) for m in target_matches)
            # Maximalen per speler binnen scope (ceil)
            num_players_active = max(1, len(active_players))
            max_per_player_target = (total_slots_target + num_players_active - 1) // num_players_active
            # Huidige tellers per speler voor scope (start met gepinden in scope)
            fairness_counts = {p['id']: 0 for p in active_players}
            for m in target_matches:
                for pid in pinned_assignments.get(m['id'], []):
                    if pid in fairness_counts:
                        fairness_counts[pid] += 1
            print(f"   🎯 Target slots: {total_slots_target}, pinned in scope: {pinned_in_target_total}, cap per speler: {max_per_player_target}")

            # === STAP 6: GENERATE COMPLETE PLANNING ===
            print("\n🎯 STEP 6: GENERATING COMPLETE PLANNING...")

            # Index matches to balance spacing over time and avoid long streaks
            match_index_by_id = {m['id']: i for i, m in enumerate(target_matches)}
            last_play_idx = {p['id']: None for p in active_players}  # last index where player was assigned (pinned or selected)
            pair_cooccur = defaultdict(int)  # unordered pair (min_id, max_id) -> times played together so far in this regen
            # Keep short memory of recent full team quartets to increase diversity
            quartet_memory_size = 3  # consider last N lineups as recent
            recent_quartets = deque(maxlen=quartet_memory_size)
            # Weights and bonuses (tunable)
            recent_weight = 0.5
            spacing_weight = 1.2
            synergy_weight = 0.8
            synergy_weight_for_partners = 0.3  # a bit lighter to keep partners together more often
            partner_pair_bonus = 1.5           # stronger bonus for selecting a true partner pair
            partner_with_selected_bonus = 0.8  # slightly stronger bonus when partner already present
            
            regenerated_count = 0
            total_assignments = 0
            rule_violations = []
            
            for idx, match in enumerate(target_matches):
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

                # Progressive fairness cap up to this point (prevents front-loading the same players)
                # Allowed max for now = ceil(4 * matches_processed_so_far / num_players)
                matches_so_far_inclusive = idx + 1
                allowed_now_cap = (4 * matches_so_far_inclusive + num_players_active - 1) // num_players_active
                print(f"      ⚖️ Progressive cap until now: {allowed_now_cap} per player")

                # Ensure pinned players count toward spacing tracking for subsequent matches
                for pid in existing_pinned:
                    last_play_idx[pid] = idx
                
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
                            # Calculate recent play penalty (more recent = higher penalty)
                            recent_matches = recent_matches_by_player[player_id]
                            recent_penalty = len(recent_matches)  # 0-3 penalty based on recent matches

                            # Spacing penalty to avoid consecutive or near-consecutive appearances
                            lp = last_play_idx.get(player_id)
                            if lp is None:
                                spacing_penalty = 0
                            else:
                                gap = idx - lp
                                # penalize if played very recently (gap 1->2, 2->1)
                                spacing_penalty = 2 if gap <= 1 else (1 if gap == 2 else 0)
                            
                            candidates.append({
                                'player': player,
                                'match_count': player_match_counts[player_id],
                                'home_count': player_home_counts[player_id],
                                'away_count': player_away_counts[player_id],
                                'recent_penalty': recent_penalty,
                                'spacing_penalty': spacing_penalty,
                                'available': True
                            })
                        else:
                            print(f"         ❌ {player['name']}: {'unavailable' if not is_available else 'date conflict'}")
                    
                    print(f"      ✅ Available candidates: {len(candidates)}")

                    # === NEW: PARTNER PRIORITY SELECTION ===
                    selected_candidates = []
                    selected_ids = set()
                    remaining_needed = needed_players

                    # Build quick index by player id for candidates
                    candidates_by_id = {c['player']['id']: c for c in candidates}

                    # 6a. Add partners of pinned players first (if both prefer together and partner is available)
                    for pinned_id in existing_pinned:
                        if remaining_needed <= 0:
                            break
                        pinned_player = players_by_id.get(pinned_id)
                        if not pinned_player:
                            continue
                        partner_id = pinned_player.get('partner_id')
                        if not partner_id or partner_id in existing_pinned:
                            continue
                        partner = players_by_id.get(partner_id)
                        # Both should prefer playing together
                        if partner and pinned_player.get('prefer_partner_together', True) and partner.get('prefer_partner_together', True):
                            # Partner must be an eligible candidate for this match
                            cand = candidates_by_id.get(partner_id)
                            # FAIRNESS FIRST: don't exceed cap (both global cap and progressive cap) and avoid back-to-back if possible
                            lp_partner = last_play_idx.get(partner_id)
                            gap_ok = (lp_partner is None) or ((idx - lp_partner) >= 2)  # prefer at least one match between
                            within_cap = fairness_counts.get(partner_id, 0) < max_per_player_target
                            within_progress = fairness_counts.get(partner_id, 0) < allowed_now_cap
                            if cand and partner_id not in selected_ids and within_cap and (within_progress or remaining_needed >= (4 - len(existing_pinned))) and gap_ok:
                                selected_candidates.append(cand)
                                selected_ids.add(partner_id)
                                remaining_needed -= 1
                                fairness_counts[partner_id] = fairness_counts.get(partner_id, 0) + 1
                                print(f"         🤝 Added partner of pinned: {partner.get('name')} (for {pinned_player.get('name')})")

                    # 6b. Form partner pairs among remaining candidates (both prefer together)
                    if remaining_needed > 0:
                        # Collect pair options (avoid duplicates)
                        pairs = []  # each item: (combined_score, (cand_a, cand_b))
                        seen_pairs = set()
                        for cid, cand in candidates_by_id.items():
                            if cid in selected_ids:
                                continue
                            player = cand['player']
                            partner_id = player.get('partner_id')
                            if not partner_id:
                                continue
                            if partner_id in existing_pinned:
                                # Partner already pinned; this case handled earlier
                                continue
                            # Both sides should be candidates and prefer together
                            partner_cand = candidates_by_id.get(partner_id)
                            partner_player = players_by_id.get(partner_id)
                            if not partner_cand or not partner_player:
                                continue
                            if not (player.get('prefer_partner_together', True) and partner_player.get('prefer_partner_together', True)):
                                continue
                            # FAIRNESS FIRST: skip pairs that would break caps
                            if not (fairness_counts.get(cid, 0) < max_per_player_target and fairness_counts.get(partner_id, 0) < max_per_player_target):
                                continue
                            # Progressive cap and spacing: avoid pairing if any of them just played last match
                            lp_a = last_play_idx.get(cid)
                            lp_b = last_play_idx.get(partner_id)
                            if (lp_a is not None and (idx - lp_a) <= 1) or (lp_b is not None and (idx - lp_b) <= 1):
                                continue
                            if not (fairness_counts.get(cid, 0) < allowed_now_cap and fairness_counts.get(partner_id, 0) < allowed_now_cap):
                                continue
                            # Create an order-independent key to avoid duplicates
                            pair_key = tuple(sorted([cid, partner_id]))
                            if pair_key in seen_pairs:
                                continue
                            seen_pairs.add(pair_key)
                            # Compute a fairness-oriented combined score (lower is better)
                            combined_score = (
                                cand['match_count'] + partner_cand['match_count'] +
                                recent_weight * (cand['recent_penalty'] + partner_cand['recent_penalty']) +
                                spacing_weight * (cand.get('spacing_penalty', 0) + partner_cand.get('spacing_penalty', 0))
                            )
                            # Add synergy penalty: how often A-B have been together + with currently pinned players
                            a_id = cid
                            b_id = partner_id
                            key_ab = (a_id, b_id) if a_id < b_id else (b_id, a_id)
                            synergy = pair_cooccur[key_ab]
                            for pid in existing_pinned:
                                k1 = (a_id, pid) if a_id < pid else (pid, a_id)
                                k2 = (b_id, pid) if b_id < pid else (pid, b_id)
                                synergy += pair_cooccur[k1] + pair_cooccur[k2]
                            # Prefer true partners slightly more often: lighter synergy penalty and apply bonus
                            combined_score += (synergy_weight_for_partners if players_by_id.get(a_id, {}).get('partner_id') == b_id else synergy_weight) * synergy
                            if players_by_id.get(a_id, {}).get('partner_id') == b_id and \
                               players_by_id.get(a_id, {}).get('prefer_partner_together', True) and \
                               players_by_id.get(b_id, {}).get('prefer_partner_together', True):
                                combined_score -= partner_pair_bonus
                            pairs.append((combined_score, (cand, partner_cand)))

                        # Sort pairs by best combined score
                        pairs.sort(key=lambda x: x[0])

                        for _, (cand_a, cand_b) in pairs:
                            if remaining_needed < 2:
                                break
                            a_id = cand_a['player']['id']
                            b_id = cand_b['player']['id']
                            if a_id in selected_ids or b_id in selected_ids:
                                continue
                            selected_candidates.extend([cand_a, cand_b])
                            selected_ids.update([a_id, b_id])
                            remaining_needed -= 2
                            fairness_counts[a_id] = fairness_counts.get(a_id, 0) + 1
                            fairness_counts[b_id] = fairness_counts.get(b_id, 0) + 1
                            print(f"         👥 Added partner pair: {cand_a['player']['name']} + {cand_b['player']['name']}")

                    # === RULE 4: Sort by fairness with VARIATIE! for remaining slots ===
                    remaining_candidates_all = [c for c in candidates if c['player']['id'] not in selected_ids]
                    # Apply fairness caps: strong preference to progressive cap, then global cap
                    under_progressive = [c for c in remaining_candidates_all if fairness_counts.get(c['player']['id'], 0) < allowed_now_cap]
                    under_global = [c for c in remaining_candidates_all if fairness_counts.get(c['player']['id'], 0) < max_per_player_target]
                    # Start with progressive set; if too small, use global; else fallback to all
                    remaining_candidates = under_progressive if len(under_progressive) >= remaining_needed else (under_global if len(under_global) >= remaining_needed else remaining_candidates_all)

                    if len(remaining_candidates) > remaining_needed and remaining_needed > 0:
                        # Group candidates by combined score (match_count + recent_penalty + spacing + synergy)
                        candidates_by_score = {}
                        for c in remaining_candidates:
                            # Combined score: total matches + recent + spacing + synergy; include partner bonus if partner already present
                            pid_c = c['player']['id']
                            synergy = 0
                            partner_bonus = 0
                            partner_id = players_by_id.get(pid_c, {}).get('partner_id')
                            for pid in list(selected_ids) + list(existing_pinned):
                                key = (pid_c, pid) if pid_c < pid else (pid, pid_c)
                                synergy += pair_cooccur[key]
                                if partner_id and pid == partner_id and \
                                   players_by_id.get(pid_c, {}).get('prefer_partner_together', True) and \
                                   players_by_id.get(partner_id, {}).get('prefer_partner_together', True):
                                    partner_bonus += partner_with_selected_bonus
                            # Lighter synergy penalty if the partner is present (true partners)
                            effective_synergy_weight = synergy_weight_for_partners if partner_id and partner_id in (list(selected_ids) + list(existing_pinned)) else synergy_weight
                            score = c['match_count'] + (c['recent_penalty'] * recent_weight) + (c.get('spacing_penalty', 0) * spacing_weight) + (effective_synergy_weight * synergy) - partner_bonus
                            score_key = round(score, 1)
                            
                            if score_key not in candidates_by_score:
                                candidates_by_score[score_key] = []
                            candidates_by_score[score_key].append(c)
                        
                        # Select with variatie: prioritize lower scores, add randomness
                        sorted_scores = sorted(candidates_by_score.keys())
                        
                        print(f"         📊 Candidate distribution by score: {[(s, len(candidates_by_score[s])) for s in sorted_scores]}")
                        
                        for score in sorted_scores:
                            group = candidates_by_score[score]
                            if remaining_needed <= 0:
                                break
                            
                            # Add variatie: shuffle within same score group
                            random.shuffle(group)
                            
                            # For lowest score: prefer more selections
                            if score == sorted_scores[0]:  # Best (lowest) score
                                take = min(remaining_needed, len(group))
                            else:
                                # Gradual reduction for higher scores
                                reduction_factor = 0.7  # Take 70% from higher score groups
                                max_take = max(1, int(remaining_needed * reduction_factor)) if remaining_needed > 1 else remaining_needed
                                take = min(max_take, len(group), remaining_needed)
                            
                            # Secondary sort: balance home/away, then random for variatie
                            group.sort(key=lambda c: (
                                abs(c['home_count'] - c['away_count']) if is_home else -abs(c['home_count'] - c['away_count']),
                                random.random()  # Extra randomness for variatie!
                            ))
                            
                            selected_candidates.extend(group[:take])
                            selected_ids.update([x['player']['id'] for x in group[:take]])
                            for x in group[:take]:
                                fairness_counts[x['player']['id']] = fairness_counts.get(x['player']['id'], 0) + 1
                            remaining_needed -= take
                            
                            print(f"         🎲 From {len(group)} players with score {score}: selected {take}")
                    else:
                        # Not enough candidates or exact fit - take what's left up to remaining_needed
                        if remaining_needed > 0:
                            # Prefer under-cap, then if still needed, allow over-cap with best fairness
                            # Sort remaining by score including synergy with pinned/selected
                            def compute_score(c):
                                pid_c = c['player']['id']
                                synergy = 0
                                partner_bonus = 0
                                partner_id = players_by_id.get(pid_c, {}).get('partner_id')
                                for pid in list(selected_ids) + list(existing_pinned):
                                    key = (pid_c, pid) if pid_c < pid else (pid, pid_c)
                                    synergy += pair_cooccur[key]
                                    if partner_id and pid == partner_id and \
                                       players_by_id.get(pid_c, {}).get('prefer_partner_together', True) and \
                                       players_by_id.get(partner_id, {}).get('prefer_partner_together', True):
                                        partner_bonus += partner_with_selected_bonus
                                effective_synergy_weight = synergy_weight_for_partners if partner_id and partner_id in (list(selected_ids) + list(existing_pinned)) else synergy_weight
                                return c['match_count'] + (c['recent_penalty'] * recent_weight) + (c.get('spacing_penalty', 0) * spacing_weight) + (effective_synergy_weight * synergy) - partner_bonus
                            remaining_candidates.sort(key=compute_score)
                            take_from_under = min(remaining_needed, len(remaining_candidates))
                            chosen = remaining_candidates[:take_from_under]
                            selected_candidates.extend(chosen)
                            selected_ids.update([x['player']['id'] for x in chosen])
                            for x in chosen:
                                fairness_counts[x['player']['id']] = fairness_counts.get(x['player']['id'], 0) + 1
                            remaining_needed -= take_from_under
                            if remaining_needed > 0:
                                # Allow picking from all remaining ignoring cap, choose by lowest match_count
                                overflow_pool = [c for c in remaining_candidates_all if c['player']['id'] not in selected_ids]
                                overflow_pool.sort(key=compute_score)
                                take_overflow = min(remaining_needed, len(overflow_pool))
                                selected_candidates.extend(overflow_pool[:take_overflow])
                                selected_ids.update([x['player']['id'] for x in overflow_pool[:take_overflow]])
                                for x in overflow_pool[:take_overflow]:
                                    fairness_counts[x['player']['id']] = fairness_counts.get(x['player']['id'], 0) + 1
                                remaining_needed -= take_overflow
                    
                    # FINAL BACKFILL: ensure we reach 4 if enough available candidates exist
                    missing = max(0, 4 - (len(existing_pinned) + len(selected_candidates)))
                    if missing > 0:
                        # Take from any remaining eligible candidates (ignoring fairness/partner), best fairness-first
                        leftovers = [c for c in candidates if c['player']['id'] not in selected_ids]
                        if len(leftovers) >= missing:
                            def compute_score(c):
                                pid_c = c['player']['id']
                                synergy = 0
                                partner_bonus = 0
                                partner_id = players_by_id.get(pid_c, {}).get('partner_id')
                                for pid in list(selected_ids) + list(existing_pinned):
                                    key = (pid_c, pid) if pid_c < pid else (pid, pid_c)
                                    synergy += pair_cooccur[key]
                                    if partner_id and pid == partner_id and \
                                       players_by_id.get(pid_c, {}).get('prefer_partner_together', True) and \
                                       players_by_id.get(partner_id, {}).get('prefer_partner_together', True):
                                        partner_bonus += partner_with_selected_bonus
                                effective_synergy_weight = synergy_weight_for_partners if partner_id and partner_id in (list(selected_ids) + list(existing_pinned)) else synergy_weight
                                return c['match_count'] + (c['recent_penalty'] * recent_weight) + (c.get('spacing_penalty', 0) * spacing_weight) + (effective_synergy_weight * synergy) - partner_bonus
                            leftovers.sort(key=compute_score)
                            add = leftovers[:missing]
                            selected_candidates.extend(add)
                            selected_ids.update([x['player']['id'] for x in add])
                            for x in add:
                                fairness_counts[x['player']['id']] = fairness_counts.get(x['player']['id'], 0) + 1
                            missing = 0

                    # Quartet diversity memory: avoid repeating exact same quartet as in last few matches
                    team_ids_preview = list(existing_pinned) + [c['player']['id'] for c in selected_candidates]
                    if len(team_ids_preview) == 4:
                        current_team_set = frozenset(team_ids_preview)
                        if current_team_set in recent_quartets:
                            print(f"         🔁 Quartet matches one of the last {quartet_memory_size} lineups; trying to diversify...")
                            # Try a soft swap: replace one selected (non-pinned) with an alternative candidate
                            leftovers = [c for c in candidates if c['player']['id'] not in selected_ids]

                            # Scoring helper reused from fairness logic with synergy
                            def _compute_score(c):
                                pid_c = c['player']['id']
                                synergy = 0
                                for pid in list(selected_ids) + list(existing_pinned):
                                    key = (pid_c, pid) if pid_c < pid else (pid, pid_c)
                                    synergy += pair_cooccur[key]
                                return c['match_count'] + (c['recent_penalty'] * 0.5) + (c.get('spacing_penalty', 0) * 1.2) + (0.8 * synergy)

                            leftovers.sort(key=_compute_score)

                            swapped = False
                            # Iterate alternatives first to find a good new face
                            for alt in leftovers:
                                alt_id = alt['player']['id']
                                # Respect caps when possible
                                if not (fairness_counts.get(alt_id, 0) < max_per_player_target and fairness_counts.get(alt_id, 0) < allowed_now_cap):
                                    continue
                                # Try swapping out one of the currently selected players
                                for i, rem in enumerate(selected_candidates):
                                    rem_id = rem['player']['id']
                                    # Propose new selected id set
                                    new_selected_ids = (selected_ids - {rem_id}) | {alt_id}
                                    new_team_set = frozenset(list(existing_pinned) + list(new_selected_ids))
                                    if new_team_set not in recent_quartets:
                                        # Apply swap
                                        selected_candidates[i] = alt
                                        selected_ids.remove(rem_id)
                                        selected_ids.add(alt_id)
                                        # Adjust fairness counters for cap accounting within scope
                                        fairness_counts[rem_id] = max(0, fairness_counts.get(rem_id, 0) - 1)
                                        fairness_counts[alt_id] = fairness_counts.get(alt_id, 0) + 1
                                        current_team_set = new_team_set
                                        print(f"         🔄 Diversity swap: replaced {rem['player']['name']} with {alt['player']['name']}")
                                        swapped = True
                                        break
                                if swapped:
                                    break
                            if not swapped:
                                print("         ℹ️ Kept lineup (no safe swap found within caps)")

                    print(f"      ⭐ Selected {len(selected_candidates)} players:")
                    
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
                        
                        # Update recent matches tracking (keep last 3 matches)
                        recent_matches_by_player[player_id].append(match_id)
                        if len(recent_matches_by_player[player_id]) > 3:
                            recent_matches_by_player[player_id].pop(0)  # Remove oldest
                        
                        # Update spacing tracker
                        last_play_idx[player_id] = idx
                        
                        total_assignments += 1
                        print(f"         ✅ {player['name']} (total: {player_match_counts[player_id]}, recent: {len(recent_matches_by_player[player_id])})")
                    
                    # Update pair co-occurrence counts for full team (pinned + selected)
                    team_ids = list(existing_pinned) + [c['player']['id'] for c in selected_candidates]
                    for i in range(len(team_ids)):
                        for j in range(i + 1, len(team_ids)):
                            a, b = team_ids[i], team_ids[j]
                            key = (a, b) if a < b else (b, a)
                            pair_cooccur[key] += 1

                    # Add this quartet to the recent memory for diversity tracking
                    if len(team_ids) == 4:
                        recent_quartets.append(frozenset(team_ids))

                    # Check for rule violations
                    total_players = len(existing_pinned) + len(selected_candidates)
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
    def _create_undo_tables(cursor):
        """Create undo snapshot tables if they don't exist."""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planning_undo_stack (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                plan_mode TEXT,
                cutoff_date DATE,
                note TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planning_undo_items (
                undo_id INTEGER REFERENCES planning_undo_stack(id) ON DELETE CASCADE,
                match_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                is_pinned BOOLEAN DEFAULT FALSE,
                actually_played BOOLEAN DEFAULT FALSE,
                UNIQUE (undo_id, match_id, player_id)
            )
        ''')

    @staticmethod
    def _create_undo_snapshot(cursor, plan_mode, cutoff_date):
        """Snapshot the entire current single planning (version_id=1) before changes."""
        # Create stack entry
        cursor.execute('''
            INSERT INTO planning_undo_stack (plan_mode, cutoff_date, note)
            VALUES (%s, %s, %s)
            RETURNING id
        ''', (plan_mode, cutoff_date if isinstance(cutoff_date, str) or cutoff_date is None else getattr(cutoff_date, 'isoformat', lambda: cutoff_date)(), 'Auto snapshot before regeneration'))
        undo_id = cursor.fetchone()['id']
        # Copy all current assignments into items
        cursor.execute('''
            INSERT INTO planning_undo_items (undo_id, match_id, player_id, is_pinned, actually_played)
            SELECT %s, mp.match_id, mp.player_id, mp.is_pinned, mp.actually_played
            FROM match_planning mp
            WHERE mp.planning_version_id = 1
        ''', (undo_id,))
        return undo_id

    @staticmethod
    def undo_last_snapshot():
        """Restore the most recent snapshot of the single planning and pop it from the stack."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            SinglePlanning._create_undo_tables(cursor)

            # Get latest snapshot
            cursor.execute('SELECT id FROM planning_undo_stack ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return {'success': False, 'message': 'Geen undo beschikbaar'}
            undo_id = row['id']

            # Clear current planning and restore from snapshot
            cursor.execute('DELETE FROM match_planning WHERE planning_version_id = 1')
            cursor.execute('''
                INSERT INTO match_planning (planning_version_id, match_id, player_id, is_pinned, actually_played)
                SELECT 1, match_id, player_id, is_pinned, actually_played
                FROM planning_undo_items
                WHERE undo_id = %s
            ''', (undo_id,))
            restored = cursor.rowcount

            # Pop the snapshot
            cursor.execute('DELETE FROM planning_undo_stack WHERE id = %s', (undo_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return {'success': True, 'restored': restored}
        except Exception as e:
            return {'success': False, 'message': f'Undo failed: {e}'}
    
    
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
