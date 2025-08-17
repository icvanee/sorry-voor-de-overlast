from flask import Blueprint, render_template, flash, redirect, url_for
from app.utils.auth import roles_required, login_required
from app.models.player import Player
from app.models.match import Match
from app.services.import_service import ImportService
from app.services.scraper import TeamBeheerScraper
from app.services.single_planning import SinglePlanning

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    """Homepage with overview."""
    players = Player.get_all()
    upcoming_matches = Match.get_upcoming()[:5]  # Next 5 matches
    # Fetch planned players for each upcoming match
    planning_by_match = {}
    try:
        for m in upcoming_matches:
            match_id = m.id if hasattr(m, 'id') else m.get('id')
            if match_id is not None:
                planning_by_match[match_id] = SinglePlanning.get_match_planning(match_id)
    except Exception:
        # Fail-safe: if planning fetch fails, leave it empty to not break homepage
        planning_by_match = {}
    
    return render_template('index.html', 
                         players=players, 
                         upcoming_matches=upcoming_matches,
                         planning_by_match=planning_by_match)

@main.route('/import_matches')
@roles_required('captain', 'reserve captain')
def import_matches():
    """Import matches from teambeheer.nl"""
    try:
        service = ImportService()
        result = service.import_matches(use_static_fallback=True)
        
        if result['success']:
            if result['imported'] > 0:
                flash(f"Successfully imported {result['imported']} matches! (Skipped {result['skipped']} existing)", 'success')
            else:
                flash('No new matches found to import.', 'info')
        else:
            error_msg = result['messages'][-1] if result['messages'] else 'Unknown error occurred'
            flash(f'Error importing matches: {error_msg}', 'error')
            
    except Exception as e:
        flash(f'Error importing matches: {str(e)}', 'error')
    
    return redirect(url_for('main.index'))

@main.route('/import_players')
@roles_required('captain', 'reserve captain')
def import_players():
    """Import players from teambeheer.nl"""
    try:
        service = ImportService()
        result = service.import_players()
        
        if result['success']:
            if result['imported'] > 0:
                flash(f"Successfully imported {result['imported']} players! (Skipped {result['skipped']} existing)", 'success')
            else:
                flash('No new players found to import.', 'info')
        else:
            error_msg = result['messages'][-1] if result['messages'] else 'Unknown error occurred'
            flash(f'Error importing players: {error_msg}', 'error')
            
    except Exception as e:
        flash(f'Error importing players: {str(e)}', 'error')
    
    return redirect(url_for('main.index'))

@main.route('/clear_all_matches', methods=['POST'])
@roles_required('captain', 'reserve captain')
def clear_all_matches():
    """Clear all matches from the database (development only)"""
    try:
        # Delete all match planning first (foreign key constraint)
        from app.models.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete match planning entries
        cursor.execute('DELETE FROM match_planning')
        deleted_planning = cursor.rowcount
        
        # Delete player availability entries
        cursor.execute('DELETE FROM player_availability')
        deleted_availability = cursor.rowcount
        
        # Delete matches
        cursor.execute('DELETE FROM matches')
        deleted_matches = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Successfully cleared all data: {deleted_matches} matches, {deleted_planning} planning entries, {deleted_availability} availability entries', 'success')
        
    except Exception as e:
        flash(f'Error clearing matches: {str(e)}', 'error')
    
    return redirect(url_for('main.index'))

@main.route('/debug_scraper')
def debug_scraper():
    """Debug the scraper (development only)"""
    try:
        scraper = TeamBeheerScraper()
        matches = scraper.scrape_matches()
        
        debug_info = {
            'url': scraper.base_url,
            'team_name': scraper.team_name,
            'matches_found': len(matches),
            'matches': matches[:10]  # First 10 matches for debugging
        }
        
        return f"<pre>{debug_info}</pre>"
        
    except Exception as e:
        import traceback
        return f"<pre>Error: {e}\n\nTraceback:\n{traceback.format_exc()}</pre>"

# Dashboard removed: no longer in use
