from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.services.planning import PlanningVersion, MatchPlanning, AutoPlanningService
from app.models.player import Player
from app.models.match import Match
from datetime import datetime

planning = Blueprint('planning', __name__)

@planning.route('/rules')
def planning_rules():
    """Show planning rules and guidelines."""
    return render_template('planning/rules.html')

@planning.route('/')
def list_versions():
    """List all planning versions."""
    versions = PlanningVersion.get_all()
    final_version = PlanningVersion.get_final()
    active_version = PlanningVersion.get_active()
    return render_template('planning/list.html', 
                         versions=versions, 
                         final_version=final_version,
                         active_version=active_version)

@planning.route('/create', methods=['GET', 'POST'])
def create_version():
    """Create a new planning version."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        auto_generate = request.form.get('auto_generate') == 'true'
        copy_from = request.form.get('copy_from')
        pinned_matches = request.form.getlist('pinned_matches')
        
        if not name:
            flash('Planning name is required!', 'error')
            return redirect(url_for('planning.create_version'))
        
        try:
            if copy_from:
                # Copy from existing version with pinned matches
                version_id = PlanningVersion.copy_from_version(
                    name, description, int(copy_from), 
                    [int(m) for m in pinned_matches] if pinned_matches else None
                )
                flash(f'Planning "{name}" created by copying from existing version!', 'success')
            else:
                # Create new version
                version_id = PlanningVersion.create(name, description)
                flash(f'Planning "{name}" created successfully!', 'success')
            
            if auto_generate and not copy_from:
                # Auto-generate planning for new version
                AutoPlanningService.generate_planning(version_id)
                flash('Automatic planning generated!', 'info')
            elif auto_generate and copy_from:
                # Auto-generate only for non-pinned matches
                AutoPlanningService.generate_planning_selective(version_id, exclude_pinned=True)
                flash('Automatic planning generated for non-pinned matches!', 'info')
            
            return redirect(url_for('planning.view_version', version_id=version_id))
        except Exception as e:
            flash(f'Error creating planning: {e}', 'error')
    
    # GET request - show form
    existing_versions = PlanningVersion.get_all()
    return render_template('planning/create.html', existing_versions=existing_versions)

@planning.route('/<int:version_id>')
def view_version(version_id):
    """View a specific planning version."""
    version = PlanningVersion.get_by_id(version_id)
    if not version:
        flash('Planning version not found!', 'error')
        return redirect(url_for('planning.list_versions'))
    
    # Get planning data and transform it for the template
    planning_raw = MatchPlanning.get_version_planning(version_id)
    
    # Transform flat planning data into grouped structure expected by template
    planning_data = {}
    for row in planning_raw:
        match_id = row['match_id']
        
        if match_id not in planning_data:
            # Create match object with proper structure
            planning_data[match_id] = {
                'match': {
                    'id': match_id,
                    'match_date': row['match_date'], 
                    'home_team': row['home_team'],
                    'away_team': row['away_team'],
                    'match_number': row.get('match_number', None)  # Add if available
                },
                'players': []
            }
        
        # Add player to this match
        planning_data[match_id]['players'].append({
            'id': row['player_id'],
            'name': row['player_name'],
            'role': row['role']
        })
    
    # Convert to list for template iteration
    planning_list = list(planning_data.values())
    
    return render_template('planning/view.html', version=version, planning_data=planning_list)

@planning.route('/<int:version_id>/make_final')
def make_final(version_id):
    """Make a planning version final."""
    try:
        PlanningVersion.set_final(version_id)
        flash('Planning version set as final!', 'success')
    except Exception as e:
        flash(f'Error setting final version: {e}', 'error')
    
    return redirect(url_for('planning.view_version', version_id=version_id))

@planning.route('/<int:version_id>/pin_match/<int:match_id>', methods=['POST'])
def pin_match(version_id, match_id):
    """Pin or unpin a match in planning."""
    try:
        pinned = request.form.get('pinned') == 'true'
        MatchPlanning.pin_match(version_id, match_id, pinned)
        action = 'pinned' if pinned else 'unpinned'
        flash(f'Match {action} successfully!', 'success')
    except Exception as e:
        flash(f'Error pinning match: {e}', 'error')
    
    return redirect(url_for('planning.view_version', version_id=version_id))

@planning.route('/<int:version_id>/regenerate', methods=['POST'])
def regenerate_planning(version_id):
    """Regenerate planning for non-pinned matches."""
    try:
        AutoPlanningService.generate_planning_selective(version_id, exclude_pinned=True)
        flash('Planning regenerated for non-pinned matches!', 'success')
    except Exception as e:
        flash(f'Error regenerating planning: {e}', 'error')
    
    return redirect(url_for('planning.view_version', version_id=version_id))

@planning.route('/<int:version_id>/duplicate')
def duplicate_version(version_id):
    """Duplicate a planning version."""
    try:
        original = PlanningVersion.get_by_id(version_id)
        if not original:
            flash('Original planning not found!', 'error')
            return redirect(url_for('planning.list_versions'))
        
        new_name = f"Copy of {original['name']}"
        new_id = PlanningVersion.create(new_name, f"Duplicated from: {original['description']}")
        
        # TODO: Copy all planning data
        flash(f'Planning duplicated successfully!', 'success')
        return redirect(url_for('planning.view_version', version_id=new_id))
    except Exception as e:
        flash(f'Error duplicating planning: {e}', 'error')
        return redirect(url_for('planning.list_versions'))

@planning.route('/match/<int:match_id>')
def match_planning(match_id):
    """Show planning options for a specific match."""
    match = Match.get_by_id(match_id)
    if not match:
        flash('Match not found!', 'error')
        return redirect(url_for('matches.list_matches'))
    
    versions = PlanningVersion.get_all()
    return render_template('planning/match_planning.html', match=match, versions=versions)
    matches = Match.get_all()
    
    # Group planning by match
    match_planning = {}
    for item in planning_data:
        match_id = item['match_id']
        if match_id not in match_planning:
            match_planning[match_id] = {
                'match': next((m for m in matches if m['id'] == match_id), None),
                'players': []
            }
        match_planning[match_id]['players'].append(item)
    
    # Get player statistics
    planner = AutoPlanningService()
    player_stats = planner.get_player_statistics(version_id)
    
    return render_template('planning/view.html', 
                         version=version, 
                         match_planning=match_planning,
                         player_stats=player_stats)

@planning.route('/<int:version_id>/match/<int:match_id>')
def edit_match_planning(version_id, match_id):
    """Edit planning for a specific match."""
    version = PlanningVersion.get_by_id(version_id)
    match = Match.get_by_id(match_id)
    
    if not version or not match:
        flash('Planning version or match not found!', 'error')
        return redirect(url_for('planning.list_versions'))
    
    # Get current planning for this match
    current_planning = MatchPlanning.get_planning(version_id, match_id)
    selected_player_ids = [p['player_id'] for p in current_planning]
    
    # Get all players and their availability
    all_players = Player.get_all()
    player_data = []
    
    for player in all_players:
        availability = Player.get_availability(player['id'], match_id)
        is_available = not availability or availability['is_available']
        is_selected = player['id'] in selected_player_ids
        
        player_data.append({
            'player': player,
            'is_available': is_available,
            'is_selected': is_selected,
            'availability_notes': availability['notes'] if availability else ''
        })
    
    return render_template('planning/edit_match.html',
                         version=version,
                         match=match,
                         player_data=player_data)

@planning.route('/<int:version_id>/match/<int:match_id>/save', methods=['POST'])
def save_match_planning(version_id, match_id):
    """Save planning for a specific match."""
    try:
        selected_players = request.form.getlist('selected_players')
        player_ids = [int(pid) for pid in selected_players]
        
        if len(player_ids) < 4:
            flash('At least 4 players must be selected!', 'error')
            return redirect(url_for('planning.edit_match_planning', 
                                  version_id=version_id, match_id=match_id))
        
        if len(player_ids) > 6:
            flash('Maximum 6 players can be selected!', 'error')
            return redirect(url_for('planning.edit_match_planning', 
                                  version_id=version_id, match_id=match_id))
        
        MatchPlanning.set_planning(version_id, match_id, player_ids)
        flash('Match planning saved successfully!', 'success')
        
    except Exception as e:
        flash(f'Error saving planning: {e}', 'error')
    
    return redirect(url_for('planning.view_version', version_id=version_id))

@planning.route('/<int:version_id>/set_final')
def set_final(version_id):
    """Set a planning version as final."""
    try:
        PlanningVersion.set_final(version_id)
        flash('Planning version set as final!', 'success')
    except Exception as e:
        flash(f'Error setting planning as final: {e}', 'error')
    
    return redirect(url_for('planning.view_version', version_id=version_id))

@planning.route('/api/<int:version_id>/confirm/<int:match_id>/<int:player_id>', methods=['POST'])
def confirm_player(version_id, match_id, player_id):
    """Confirm a player for a match via API."""
    try:
        confirmed = request.json.get('confirmed', False)
        MatchPlanning.confirm_player(version_id, match_id, player_id, confirmed)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@planning.route('/api/<int:version_id>/played/<int:match_id>/<int:player_id>', methods=['POST'])
def mark_played(version_id, match_id, player_id):
    """Mark a player as having played via API."""
    try:
        played = request.json.get('played', False)
        MatchPlanning.mark_played(version_id, match_id, player_id, played)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@planning.route('/compare')
def compare_versions():
    """Compare different planning versions."""
    versions = PlanningVersion.get_all()
    
    selected_versions = request.args.getlist('versions')
    comparison_data = {}
    
    if selected_versions:
        for version_id in selected_versions:
            version_id = int(version_id)
            version = PlanningVersion.get_by_id(version_id)
            if version:
                planner = AutoPlanningService()
                stats = planner.get_player_statistics(version_id)
                comparison_data[version_id] = {
                    'version': version,
                    'stats': stats
                }
    
    return render_template('planning/compare.html', 
                         versions=versions,
                         comparison_data=comparison_data,
                         selected_versions=selected_versions)

@planning.route('/<int:version_id>/delete', methods=['POST'])
def delete_version(version_id):
    """Soft delete a planning version."""
    version = PlanningVersion.get_by_id(version_id)
    if not version:
        flash('Planning versie niet gevonden.', 'error')
        return redirect(url_for('planning.list_versions'))
    
    # Check if it's the final version
    if version['is_final']:
        flash('De definitieve planning kan niet worden verwijderd.', 'error')
        return redirect(url_for('planning.list_versions'))
    
    # Confirmation check
    confirm = request.form.get('confirm')
    if confirm != 'true':
        flash('Verwijdering geannuleerd.', 'info')
        return redirect(url_for('planning.list_versions'))
    
    try:
        PlanningVersion.soft_delete(version_id)
        flash(f'Planning "{version["name"]}" is verwijderd. Deze kan nog worden teruggehaald.', 'success')
    except Exception as e:
        flash(f'Fout bij verwijderen: {str(e)}', 'error')
    
    return redirect(url_for('planning.list_versions'))

@planning.route('/<int:version_id>/restore', methods=['POST'])
def restore_version(version_id):
    """Restore a soft-deleted planning version."""
    try:
        # Check if version exists and is deleted
        if not PlanningVersion.is_deleted(version_id):
            flash('Planning versie is niet verwijderd of bestaat niet.', 'error')
            return redirect(url_for('planning.list_versions'))
        
        PlanningVersion.restore(version_id)
        version = PlanningVersion.get_by_id(version_id)
        flash(f'Planning "{version["name"]}" is succesvol teruggehaald.', 'success')
    except Exception as e:
        flash(f'Fout bij terughalen: {str(e)}', 'error')
    
    return redirect(url_for('planning.list_versions'))

@planning.route('/deleted')
def list_deleted_versions():
    """Show deleted planning versions for restore."""
    versions = PlanningVersion.get_all_including_deleted()
    deleted_versions = [v for v in versions if v.get('is_deleted', 0)]
    
    return render_template('planning/deleted.html', versions=deleted_versions)

@planning.route('/<int:version_id>/set_active', methods=['POST'])
def set_active_version(version_id):
    """Set a planning version as the active one."""
    version = PlanningVersion.get_by_id(version_id)
    if not version:
        flash('Planning versie niet gevonden.', 'error')
        return redirect(url_for('planning.list_versions'))
    
    # Check if version is deleted
    if PlanningVersion.is_deleted(version_id):
        flash('Een verwijderde planning kan niet actief worden gemaakt.', 'error')
        return redirect(url_for('planning.list_versions'))
    
    try:
        PlanningVersion.set_active(version_id)
        flash(f'Planning "{version["name"]}" is nu de actieve planning.', 'success')
    except Exception as e:
        flash(f'Fout bij activeren: {str(e)}', 'error')
    
    return redirect(url_for('planning.list_versions'))
