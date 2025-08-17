"""
Single Planning Routes - Issue #22
Routes for the simplified single planning system.
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app.services.single_planning import SinglePlanning
from app.models.database import get_db_connection
from app.models.match import Match
from app.models.player import Player

single_planning = Blueprint('single_planning', __name__, url_prefix='/planning')

@single_planning.route('/')
def dashboard():
    """Main dashboard for single planning system."""
    try:
        # Get all planning data
        planning_data = SinglePlanning.get_planning()
        
        # Group planning by match
        matches = {}
        for row in planning_data:
            match_id = row['match_id']
            if match_id not in matches:
                matches[match_id] = {
                    'match': {
                        'id': match_id,
                        'date': row['match_date'],
                        'home_team': row['home_team'],
                        'away_team': row['away_team'],
                        'is_home': row['is_home'],
                        'is_played': row['is_played']
                    },
                    'players': []
                }
            
            matches[match_id]['players'].append({
                'id': row['player_id'],
                'name': row['player_name'],
                'role': row['role'],
                'is_pinned': row['is_pinned'],
                'actually_played': row['actually_played']
            })
        
        # Get player statistics
        all_players = Player.get_all()
        player_stats = {}
        for player in all_players:
            if player.get('is_active', True):
                player_stats[player['id']] = SinglePlanning.get_player_stats(player['id'])
        
        return render_template('single_planning/dashboard.html', 
                             matches=matches, 
                             player_stats=player_stats,
                             all_players=all_players)
    
    except Exception as e:
        flash(f'Error loading planning dashboard: {str(e)}', 'error')
        return render_template('single_planning/dashboard.html', 
                             matches={}, 
                             player_stats={},
                             all_players=[])

@single_planning.route('/match/<int:match_id>')
def match_detail(match_id):
    """Detail view for a specific match."""
    try:
        # Get match details
        match = Match.get_by_id(match_id)
        if not match:
            flash('Match not found!', 'error')
            return redirect(url_for('single_planning.dashboard'))
        
        # Get planning for this match
        planning = SinglePlanning.get_match_planning(match_id)
        
        # Get all active players for potential additions
        all_players = Player.get_all()
        active_players = [p for p in all_players if p.get('is_active', True)]
        
        # Get players not currently in this match
        assigned_player_ids = [p['player_id'] for p in planning]
        available_players = [p for p in active_players if p['id'] not in assigned_player_ids]
        
        return render_template('single_planning/match_detail.html',
                             match=match,
                             planning=planning,
                             available_players=available_players)
    
    except Exception as e:
        flash(f'Error loading match details: {str(e)}', 'error')
        return redirect(url_for('single_planning.dashboard'))

@single_planning.route('/api/match/<int:match_id>/players', methods=['POST'])
def update_match_players(match_id):
    """API endpoint to update players for a match."""
    try:
        data = request.get_json()
        match_id = data.get('match_id')
        player_ids = data.get('player_ids', [])
        preserve_pinned = data.get('preserve_pinned', True)
        
        if not match_id:
            return jsonify({'success': False, 'message': 'Match ID required'}), 400
        
        SinglePlanning.set_match_planning(match_id, player_ids, preserve_pinned)
        
        return jsonify({
            'success': True, 
            'message': f'Updated players for match {match_id}'
        })
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error updating match players: {str(e)}'
        }), 500

@single_planning.route('/api/player/<int:player_id>/pin', methods=['POST'])
def toggle_player_pin(player_id):
    """API endpoint to pin/unpin a player for a match."""
    try:
        data = request.get_json()
        player_id = data.get('player_id')
        match_id = data.get('match_id')
        pinned = data.get('pinned', True)
        
        if not player_id or not match_id:
            return jsonify({'success': False, 'message': 'Player ID and Match ID required'}), 400
        
        SinglePlanning.pin_player(match_id, player_id, pinned)
        
        status = 'pinned' if pinned else 'unpinned'
        return jsonify({
            'success': True, 
            'message': f'Player {status} successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error updating player pin status: {str(e)}'
        }), 500

@single_planning.route('/api/match/<int:match_id>/pin', methods=['POST'])
def toggle_match_pin(match_id):
    """API endpoint to pin/unpin all players for a match."""
    try:
        data = request.get_json()
        match_id = data.get('match_id')
        pinned = data.get('pinned', True)
        
        if not match_id:
            return jsonify({'success': False, 'message': 'Match ID required'}), 400
        
        SinglePlanning.pin_match(match_id, pinned)
        
        status = 'pinned' if pinned else 'unpinned'
        return jsonify({
            'success': True, 
            'message': f'Match {status} successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error updating match pin status: {str(e)}'
        }), 500

@single_planning.route('/api/player/<int:player_id>/actually_played', methods=['POST'])
def toggle_actually_played(player_id):
    """API endpoint to mark a player as actually played."""
    try:
        data = request.get_json()
        player_id = data.get('player_id')
        match_id = data.get('match_id')
        actually_played = data.get('actually_played', True)
        
        if not player_id or not match_id:
            return jsonify({'success': False, 'message': 'Player ID and Match ID required'}), 400
        
        SinglePlanning.set_actually_played(match_id, player_id, actually_played)
        
        status = 'marked as played' if actually_played else 'marked as not played'
        return jsonify({
            'success': True, 
            'message': f'Player {status} successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error updating actually played status: {str(e)}'
        }), 500

@single_planning.route('/api/match/<int:match_id>/played', methods=['POST'])
def toggle_match_played(match_id):
    """API endpoint to mark a match as played."""
    try:
        data = request.get_json()
        match_id = data.get('match_id')
        played = data.get('played', True)
        
        if not match_id:
            return jsonify({'success': False, 'message': 'Match ID required'}), 400
        
        SinglePlanning.set_match_played(match_id, played)
        
        status = 'marked as played' if played else 'marked as not played'
        return jsonify({
            'success': True, 
            'message': f'Match {status} successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error updating match played status: {str(e)}'
        }), 500

@single_planning.route('/api/regenerate', methods=['POST'])
def api_regenerate():
    """API: Regenerate planning while preserving pinned players."""
    try:
        print("🔄 Starting regeneration...")
        data = request.get_json(silent=True) or {}
        plan_mode = data.get('plan_mode', 'all')  # 'all' | 'until_date' | 'from_date'/'rest'
        cutoff_date = data.get('cutoff_date')     # 'YYYY-MM-DD' or None

        # Call the static method correctly
        result = SinglePlanning.regenerate_planning(
            exclude_pinned=True,
            plan_mode=plan_mode,
            cutoff_date=cutoff_date
        )
        
        print(f"🎯 Regeneration result: {result}")
        
        if result.get('success', True):  # Assume success if no explicit result
            message = f"Planning geregenereerd! {result.get('regenerated_matches', 0)} wedstrijden bijgewerkt."
            return jsonify({
                'success': True, 
                'message': message,
                'regenerated_matches': result.get('regenerated_matches', 0)
            })
        else:
            return jsonify({
                'success': False, 
                'error': result.get('message', 'Onbekende fout bij regenereren')
            }), 500
    except Exception as e:
        print(f"❌ Error in regeneration: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@single_planning.route('/matrix')
def matrix():
    """Alias for matrix_view to make it the main matrix route."""
    return matrix_view()

@single_planning.route('/matrix_view')  
def matrix_view():
    """Show matrix view of single planning."""
    try:
        print("🔍 Starting matrix view...")
        service = SinglePlanning()
        
        # Get all matches and players
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("📅 Getting matches...")
        # Get matches
        cursor.execute('''
            SELECT id, match_date, home_team, away_team, is_home, round_name, is_played
            FROM matches 
            ORDER BY match_date, id
        ''')
        matches = cursor.fetchall()
        print(f"Found {len(matches)} matches")
        
        print("👥 Getting players...")
        # Get players
        cursor.execute('''
            SELECT id, name, email 
            FROM players 
            WHERE is_active = TRUE 
            ORDER BY name
        ''')
        players = cursor.fetchall()
        print(f"Found {len(players)} players")
        
        print("📋 Getting planning assignments...")
        # Get single planning assignments (version_id = 1)
        cursor.execute('''
            SELECT 
                mp.match_id,
                mp.player_id,
                mp.is_pinned,
                mp.actually_played,
                p.name
            FROM match_planning mp
            JOIN players p ON mp.player_id = p.id
            WHERE mp.planning_version_id = 1
            ORDER BY mp.match_id, p.name
        ''')
        assignments = cursor.fetchall()
        print(f"Found {len(assignments)} planning assignments")
        
        print("📊 Getting availability data...")
        # Get player availability data
        cursor.execute('''
            SELECT 
                pa.player_id,
                pa.match_id,
                pa.is_available,
                pa.notes
            FROM player_availability pa
            WHERE EXISTS (
                SELECT 1 FROM matches m WHERE m.id = pa.match_id
            )
        ''')
        availability_data = cursor.fetchall()
        print(f"Found {len(availability_data)} availability entries")
        cursor.close()
        conn.close()
        
        print("🔧 Building matrix structure...")
        # Build matrix structure
        player_assignments = {}
        pinned_assignments = {}
        actually_played = {}
        
        for assignment in assignments:
            match_id = assignment['match_id']
            player_id = assignment['player_id']
            
            if player_id not in player_assignments:
                player_assignments[player_id] = set()
                pinned_assignments[player_id] = set()
                actually_played[player_id] = set()
            
            player_assignments[player_id].add(match_id)
            
            if assignment['is_pinned']:
                pinned_assignments[player_id].add(match_id)
            
            if assignment['actually_played']:
                actually_played[player_id].add(match_id)
        
        # Build availability structure
        availability_map = {}
        for avail in availability_data:
            player_id = avail['player_id']
            match_id = avail['match_id']
            
            if player_id not in availability_map:
                availability_map[player_id] = {}
            availability_map[player_id][match_id] = {
                'is_available': avail['is_available'],
                'notes': avail['notes']
            }
        
        print("📈 Calculating statistics...")
        # Calculate statistics
        player_stats = {}
        for player in players:
            player_id = player['id']
            total_matches = len(player_assignments.get(player_id, set()))
            total_possible_matches = len(matches)
            percentage = (total_matches / total_possible_matches * 100) if total_possible_matches > 0 else 0
            total_pinned = len(pinned_assignments.get(player_id, set()))
            total_played = len(actually_played.get(player_id, set()))
            
            player_stats[player_id] = {
                'total_matches': total_matches,
                'percentage': percentage,
                'total_pinned': total_pinned,
                'total_played': total_played
            }
        
        matrix_data = {
            'matches': matches,
            'players': players,
            'assignments': player_assignments,
            'pinned_assignments': pinned_assignments,
            'actually_played': actually_played,
            'availability': availability_map,
            'stats': player_stats
        }
        
        print("🎭 Creating version object...")
        # Create fake version object for compatibility with matrix template
        from types import SimpleNamespace
        version = SimpleNamespace()
        version.id = 1
        version.name = "Team Planning (Single System)"
        version.description = "Geïntegreerde planning met pin en regeneratie functionaliteit"
        version.is_final = False
        version.created_at = "Altijd actief"
        
        print("✅ Rendering matrix template...")
        return render_template('single_planning/matrix.html', 
                             version=version, 
                             matrix_data=matrix_data)
                             
    except Exception as e:
        print(f"❌ Error in matrix_view: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Fout bij laden matrix: {e}', 'error')
        return redirect(url_for('single_planning.dashboard'))

@single_planning.route('/matrix/edit', methods=['POST'])
def edit_matrix_cell():
    """Cycle through player assignment states: niet -> wel -> pinned -> niet."""
    try:
        service = SinglePlanning()
        
        player_id = request.json.get('player_id')
        match_id = request.json.get('match_id')
        action = request.json.get('action', 'cycle')  # Default to cycle
        
        if not player_id or not match_id:
            return jsonify({'error': 'Player ID and Match ID required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check current assignment state (version_id = 1 for single planning)
        cursor.execute('''
            SELECT id, is_pinned, actually_played FROM match_planning 
            WHERE planning_version_id = 1 AND match_id = %s AND player_id = %s
        ''', (match_id, player_id))
        
        existing = cursor.fetchone()
        
        # Cycle through states: niet -> wel -> pinned -> niet
        if not existing:
            # State 1: niet -> wel (assigned, not pinned)
            cursor.execute('''
                INSERT INTO match_planning (planning_version_id, match_id, player_id, is_pinned, actually_played)
                VALUES (1, %s, %s, FALSE, FALSE)
            ''', (match_id, player_id))
            assigned = True
            is_pinned = False
            actually_played = False
            state = 'assigned'
            
        elif existing and not existing['is_pinned']:
            # State 2: wel -> pinned (assigned and pinned)
            cursor.execute('''
                UPDATE match_planning 
                SET is_pinned = TRUE, actually_played = FALSE
                WHERE planning_version_id = 1 AND match_id = %s AND player_id = %s
            ''', (match_id, player_id))
            assigned = True
            is_pinned = True
            actually_played = False
            state = 'pinned'
            
        else:
            # State 3: pinned -> niet (remove assignment)
            cursor.execute('''
                DELETE FROM match_planning 
                WHERE planning_version_id = 1 AND match_id = %s AND player_id = %s
            ''', (match_id, player_id))
            assigned = False
            is_pinned = False
            actually_played = False
            state = 'not_assigned'
        
        conn.commit()
        
        # Check if this match now has more than 4 players (rule violation)
        cursor.execute('''
            SELECT COUNT(*) as player_count FROM match_planning 
            WHERE planning_version_id = 1 AND match_id = %s
        ''', (match_id,))
        match_player_count = cursor.fetchone()['player_count']
        
        # Get updated statistics for this player
        cursor.execute('''
            SELECT COUNT(*) as total FROM match_planning mp
            WHERE mp.planning_version_id = 1 AND mp.player_id = %s
        ''', (player_id,))
        total_matches = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT COUNT(*) as total_pinned FROM match_planning mp
            WHERE mp.planning_version_id = 1 AND mp.player_id = %s AND mp.is_pinned = TRUE
        ''', (player_id,))
        total_pinned = cursor.fetchone()['total_pinned']
        
        cursor.execute('''
            SELECT COUNT(*) as total_played FROM match_planning mp
            WHERE mp.planning_version_id = 1 AND mp.player_id = %s AND mp.actually_played = TRUE
        ''', (player_id,))
        total_played = cursor.fetchone()['total_played']
        
        cursor.execute('SELECT COUNT(*) as total FROM matches')
        total_possible = cursor.fetchone()['total']
        percentage = (total_matches / total_possible * 100) if total_possible > 0 else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'assigned': assigned,
            'is_pinned': is_pinned,
            'actually_played': actually_played,
            'state': state,
            'match_player_count': match_player_count,
            'rule_violation': match_player_count > 4,
            'stats': {
                'total_matches': total_matches,
                'total_pinned': total_pinned,
                'total_played': total_played,
                'percentage': percentage
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@single_planning.route('/api/generate_initial', methods=['POST'])
def generate_initial_planning():
    """API endpoint to generate initial planning."""
    try:
        result = SinglePlanning.generate_initial_planning()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error generating initial planning: {str(e)}'
        }), 500

@single_planning.route('/api/player/<int:player_id>/add_to_match/<int:match_id>', methods=['POST'])
def add_player_to_match(player_id, match_id):
    """API endpoint to add a player to a match (for 5th player functionality)."""
    try:
        # Get current players for the match
        current_planning = SinglePlanning.get_match_planning(match_id)
        current_player_ids = [p['player_id'] for p in current_planning]
        
        # Add the new player
        if player_id not in current_player_ids:
            updated_player_ids = current_player_ids + [player_id]
            SinglePlanning.set_match_planning(match_id, updated_player_ids, preserve_pinned=True)
            
            # Automatically pin and mark as played (as per Issue #22 requirement)
            SinglePlanning.pin_player(match_id, player_id, True)
            SinglePlanning.set_actually_played(match_id, player_id, True)
            
            return jsonify({
                'success': True, 
                'message': f'Player added to match and marked as played'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Player is already in this match'
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error adding player to match: {str(e)}'
        }), 500

# Legacy redirect routes for backwards compatibility
@single_planning.route('/single/')
def single_dashboard():
    """Redirect single/ to main dashboard."""
    return redirect(url_for('single_planning.dashboard'))

@single_planning.route('/single/matrix')
def single_matrix():
    """Redirect single/matrix to main matrix."""
    return redirect(url_for('single_planning.matrix_view'))
