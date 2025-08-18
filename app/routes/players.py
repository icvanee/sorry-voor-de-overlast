from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.utils.auth import login_required, roles_required, get_current_user
from app.models.player import Player
from app.models.match import Match
from app.services.single_planning import SinglePlanning

players = Blueprint('players', __name__)

@players.route('/')
@login_required
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
@roles_required('captain', 'reserve captain')
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
            # Create player (use named args to avoid param order issues)
            new_player_id = Player.create(name=name, role=role, partner_id=partner_id)
            # Set default password and force change on next login
            try:
                Player.set_password(new_player_id, 'svdo@2025', force_change=True)
            except Exception:
                # Non-fatal; startup seeding will cover this
                pass
            # If partner selected, set bidirectional link
            if partner_id:
                Player.set_partner_bidirectional(new_player_id, partner_id)
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
@roles_required('captain', 'reserve captain')
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
            # Update basic fields first (without changing partner here)
            Player.update(player_id, name=name, role=role)
            # Update partner bidirectionally
            Player.set_partner_bidirectional(player_id, partner_id)
            # Update partner preference mirrored to partner
            Player.set_partner_preference_bidirectional(player_id, prefer_partner_together)
            
            flash(f'Player {name} updated successfully!', 'success')
            return redirect(url_for('players.list_players'))
        except Exception as e:
            flash(f'Error updating player: {e}', 'error')
    
    # Get available players for partner selection: allow current partner and otherwise only unpaired players
    available_players = []
    all_unpaired = Player.get_available_for_partnership(exclude_player_id=player_id)
    # Include current partner if any, so it's selectable
    if player.get('partner_id'):
        partner = Player.get_by_id(player['partner_id'])
        if partner and partner['is_active']:
            available_players.append(partner)
    # Add all other unpaired players
    available_players.extend(all_unpaired)
    return render_template('players/edit.html', player=player, available_players=available_players)

@players.route('/deactivate/<int:player_id>')
@roles_required('captain', 'reserve captain')
def deactivate_player(player_id):
    """Deactivate a player."""
    try:
        Player.deactivate(player_id)
        flash('Player deactivated successfully!', 'success')
    except Exception as e:
        flash(f'Error deactivating player: {e}', 'error')
    
    return redirect(url_for('players.list_players'))

@players.route('/<int:player_id>/availability', methods=['GET', 'POST'])
@login_required
def player_availability(player_id):
    """Show and manage player availability."""
    player = Player.get_by_id(player_id)
    if not player:
        flash('Player not found!', 'error')
        return redirect(url_for('players.list_players'))
    
    # Only owner or captain can modify
    current = get_current_user()
    can_edit = current and ((current.get('id') == player_id) or (current.get('role','').lower() in ('captain','reserve captain')))

    if request.method == 'POST':
        if not can_edit:
            return jsonify({'success': False, 'error': 'Geen permissie om beschikbaarheid te wijzigen'}), 403
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
                         availability_data=availability_data,
                         can_edit=can_edit)

@players.route('/<int:player_id>/stats')
@login_required
def player_stats(player_id):
    """Show player statistics."""
    player = Player.get_by_id(player_id)
    if not player:
        flash('Player not found!', 'error')
        return redirect(url_for('players.list_players'))
    
    # Collect statistics
    sp_stats = SinglePlanning.get_player_stats(player_id)  # active planning stats
    availability = Player.get_availability_stats(player_id)
    history = Player.get_match_stats(player_id)  # actually played over time

    # Compute simple ratios
    planned = sp_stats.get('matches_planned', 0) if sp_stats else 0
    played = sp_stats.get('matches_played', 0) if sp_stats else 0
    percent_played = round((played / planned * 100), 0) if planned > 0 else 0

    return render_template('players/stats.html', 
                           player=player, 
                           sp_stats=sp_stats,
                           availability=availability,
                           history=history,
                           percent_played=int(percent_played))


# Password management by captains
@players.route('/<int:player_id>/password/reset', methods=['POST'])
@roles_required('captain', 'reserve captain')
def reset_password(player_id):
    """Reset a player's password to a random temporary one and force change on next login.
    Returns JSON with the temporary password so the captain can communicate it.
    """
    import secrets, string
    player = Player.get_by_id(player_id)
    if not player:
        return jsonify({'success': False, 'error': 'Speler niet gevonden'}), 404
    alphabet = string.ascii_letters + string.digits
    temp = 'T' + ''.join(secrets.choice(alphabet) for _ in range(9)) + '!'
    Player.set_password(player_id, temp, force_change=True)
    return jsonify({'success': True, 'temporary_password': temp})


@players.route('/<int:player_id>/password/set', methods=['POST'])
@roles_required('captain', 'reserve captain')
def set_password(player_id):
    """Set a specific password and optionally force change on next login."""
    data = request.get_json(silent=True) or {}
    new_password = data.get('password') or request.form.get('password')
    force_change = str(data.get('force_change') or request.form.get('force_change') or 'true').lower() in ('1','true','yes','on')
    if not new_password or len(new_password) < 8:
        return jsonify({'success': False, 'error': 'Wachtwoord minimaal 8 tekens.'}), 400
    player = Player.get_by_id(player_id)
    if not player:
        return jsonify({'success': False, 'error': 'Speler niet gevonden'}), 404
    Player.set_password(player_id, new_password, force_change=force_change)
    return jsonify({'success': True})
