from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.utils.auth import login_required, roles_required
from app.models.match import Match
from app.models.player import Player

matches = Blueprint('matches', __name__)

@matches.route('/')
@login_required
def list_matches():
    """List all matches."""
    all_matches = Match.get_all()
    upcoming_matches = Match.get_upcoming()
    return render_template('matches/list.html', matches=all_matches, upcoming_matches=upcoming_matches)

@matches.route('/add', methods=['GET', 'POST'])
@roles_required('captain', 'reserve captain')
def add_match():
    """Add a new match."""
    if request.method == 'POST':
        match_number = request.form.get('match_number')
        date = request.form.get('date')
        home_team = request.form.get('home_team')
        away_team = request.form.get('away_team')
        is_home = request.form.get('is_home') == 'true'
        is_friendly = request.form.get('is_friendly') == 'true'
        venue = request.form.get('venue', '')
        
        if not all([date, home_team, away_team]):
            flash('Date, home team, and away team are required!', 'error')
            return redirect(url_for('matches.add_match'))
        
        try:
            Match.create(match_number, date, home_team, away_team, is_home, is_friendly, venue)
            flash(f'Match added successfully!', 'success')
            return redirect(url_for('matches.list_matches'))
        except Exception as e:
            flash(f'Error adding match: {e}', 'error')
    
    return render_template('matches/add.html')

@matches.route('/edit/<int:match_id>', methods=['GET', 'POST'])
@roles_required('captain', 'reserve captain')
def edit_match(match_id):
    """Edit a match."""
    match = Match.get_by_id(match_id)
    if not match:
        flash('Match not found!', 'error')
        return redirect(url_for('matches.list_matches'))
    
    if request.method == 'POST':
        match_number = request.form.get('match_number')
        date = request.form.get('date')
        home_team = request.form.get('home_team')
        away_team = request.form.get('away_team')
        is_home = request.form.get('is_home') == 'true'
        is_friendly = request.form.get('is_friendly') == 'true'
        venue = request.form.get('venue', '')
        
        if not all([date, home_team, away_team]):
            flash('Date, home team, and away team are required!', 'error')
            return redirect(url_for('matches.edit_match', match_id=match_id))
        
        try:
            Match.update(match_id, match_number, date, home_team, away_team, is_home, is_friendly, venue)
            flash(f'Match updated successfully!', 'success')
            return redirect(url_for('matches.list_matches'))
        except Exception as e:
            flash(f'Error updating match: {e}', 'error')
    
    return render_template('matches/edit.html', match=match)

@matches.route('/delete/<int:match_id>')
@roles_required('captain', 'reserve captain')
def delete_match(match_id):
    """Delete a match."""
    try:
        Match.delete(match_id)
        flash('Match deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting match: {e}', 'error')
    
    return redirect(url_for('matches.list_matches'))

@matches.route('/<int:match_id>/availability')
@login_required
def match_availability(match_id):
    """Show player availability for a specific match."""
    match = Match.get_by_id(match_id)
    if not match:
        flash('Match not found!', 'error')
        return redirect(url_for('matches.list_matches'))
    
    players = Player.get_all()
    availability_data = []
    
    for player in players:
        availability = Player.get_availability(player['id'], match_id)
        availability_data.append({
            'player': player,
            'availability': availability
        })
    
    return render_template('matches/availability.html', 
                         match=match, 
                         availability_data=availability_data)

# Removed old match detail route. Details live at single_planning.match_detail
