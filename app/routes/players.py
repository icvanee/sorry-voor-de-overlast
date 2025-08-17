from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.models.player import Player
from app.models.match import Match

players = Blueprint('players', __name__)

@players.route('/')
def list_players():
    """List all players."""
    # Single planning system - no need for planning versions
    
    all_players = Player.get_all()
    partner_pairs = Player.get_partner_pairs()
    
    # Single planning system info
    active_planning_name = "Single Planning System"
    
    # Get availability and match stats for each player
    players_with_stats = []
    for player in all_players:
        availability_stats = Player.get_availability_stats(player['id'])
        match_stats = Player.get_match_stats(player['id'])  # Played matches (all time)
        active_planning_stats = Player.get_active_planning_stats(player['id'])  # Planned matches (active only)
        
        player_dict = dict(player)
        player_dict['availability_stats'] = availability_stats
        player_dict['match_stats'] = match_stats
        player_dict['active_planning_stats'] = active_planning_stats  # Add active planning stats
        players_with_stats.append(player_dict)

    return render_template('players/list.html', 
                         players=players_with_stats, 
                         partner_pairs=partner_pairs,
                         active_planning_name=active_planning_name)

@players.route('/add', methods=['GET', 'POST'])
def add_player():
    """Add a new player."""
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role', '')
        partner_id = request.form.get('partner_id')
        
        if not name:
            flash('Player name is required!', 'error')
            return redirect(url_for('players.add_player'))
        
        try:
            partner_id = int(partner_id) if partner_id else None
            Player.create(name, role, partner_id)
            flash(f'Player {name} added successfully!', 'success')
            return redirect(url_for('players.list_players'))
        except Exception as e:
            flash(f'Error adding player: {e}', 'error')
    
    # Get available players for partner selection (excluding partners)
    available_partners = Player.get_available_for_partnership()
    existing_players = Player.get_all()
    return render_template('players/add.html', 
                         available_partners=available_partners,
                         existing_players=existing_players)

@players.route('/edit/<int:player_id>', methods=['GET', 'POST'])
def edit_player(player_id):
    """Edit a player."""
    player = Player.get_by_id(player_id)
    if not player:
        flash('Player not found!', 'error')
        return redirect(url_for('players.list_players'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role', '')
        partner_id = request.form.get('partner_id')
        prefer_partner_together = request.form.get('prefer_partner_together') == 'true'
        
        if not name:
            flash('Player name is required!', 'error')
            return redirect(url_for('players.edit_player', player_id=player_id))
        
        try:
            partner_id = int(partner_id) if partner_id else None
            Player.update(player_id, name, role, partner_id)
            
            # Update partner preference
            Player.set_partner_preference(player_id, prefer_partner_together)
            
            flash(f'Player {name} updated successfully!', 'success')
            return redirect(url_for('players.list_players'))
        except Exception as e:
            flash(f'Error updating player: {e}', 'error')
    
    # Get available players for partner selection (excluding current player)
    available_players = [p for p in Player.get_all() if p['id'] != player_id]
    return render_template('players/edit.html', player=player, available_players=available_players)

@players.route('/deactivate/<int:player_id>')
def deactivate_player(player_id):
    """Deactivate a player."""
    try:
        Player.deactivate(player_id)
        flash('Player deactivated successfully!', 'success')
    except Exception as e:
        flash(f'Error deactivating player: {e}', 'error')
    
    return redirect(url_for('players.list_players'))

@players.route('/<int:player_id>/availability', methods=['GET', 'POST'])
def player_availability(player_id):
    """Show and manage player availability."""
    player = Player.get_by_id(player_id)
    if not player:
        flash('Player not found!', 'error')
        return redirect(url_for('players.list_players'))
    
    if request.method == 'POST':
        # Handle AJAX request for updating availability
        if request.is_json:
            try:
                data = request.get_json()
                updates = data.get('updates', [])
                
                for update in updates:
                    match_id = update.get('match_id')
                    is_available = update.get('is_available', False)
                    notes = update.get('notes', '')
                    
                    Player.set_availability(player_id, match_id, is_available, notes)
                
                return jsonify({'success': True, 'message': f'Beschikbaarheid bijgewerkt voor {len(updates)} wedstrijden'})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        # Handle regular form submission
        for key, value in request.form.items():
            if key.startswith('availability_'):
                match_id = key.replace('availability_', '')
                is_available = value == 'on'
                notes = request.form.get(f'notes_{match_id}', '')
                Player.set_availability(player_id, match_id, is_available, notes)
        
        flash('Beschikbaarheid succesvol bijgewerkt!', 'success')
        return redirect(url_for('players.player_availability', player_id=player_id))
    
    # GET request - show availability form
    matches = Match.get_all()
    
    # Get current availability data
    availability_data = {}
    for match in matches:
        availability = Player.get_availability(player_id, match['id'])
        if availability:
            availability_data[match['id']] = availability
    
    return render_template('players/availability.html', 
                         player=player, 
                         matches=matches,
                         availability_data=availability_data)

@players.route('/<int:player_id>/stats')
def player_stats(player_id):
    """Show player statistics."""
    player = Player.get_by_id(player_id)
    if not player:
        flash('Player not found!', 'error')
        return redirect(url_for('players.list_players'))
    
    # TODO: Calculate actual statistics
    stats = {
        'matches_played': 0,
        'matches_planned': 0,
        'availability_percentage': 100
    }
    return render_template('players/stats.html', player=player, stats=stats)
