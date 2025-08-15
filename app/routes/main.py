from flask import Blueprint, render_template, flash, redirect, url_for
from app.models.player import Player
from app.models.match import Match
from app.services.scraper import TeamBeheerScraper, import_static_matches

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Homepage with overview."""
    players = Player.get_all()
    upcoming_matches = Match.get_upcoming()[:5]  # Next 5 matches
    
    return render_template('index.html', 
                         players=players, 
                         upcoming_matches=upcoming_matches)

@main.route('/import_matches')
def import_matches():
    """Import matches from teambeheer.nl"""
    try:
        # Try web scraping first
        scraper = TeamBeheerScraper()
        imported_count = scraper.import_matches_to_db()
        
        # If no matches imported via scraping, use static data
        if imported_count == 0:
            imported_count = import_static_matches()
            
        if imported_count > 0:
            flash(f'Successfully imported {imported_count} matches!', 'success')
        else:
            flash('No new matches found to import.', 'info')
            
    except Exception as e:
        # Fallback to static data
        imported_count = import_static_matches()
        if imported_count > 0:
            flash(f'Imported {imported_count} matches from static data (scraping failed: {str(e)}).', 'warning')
        else:
            flash(f'Error importing matches: {e}', 'error')
    
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

@main.route('/dashboard')
def dashboard():
    """Dashboard with team statistics."""
    players = Player.get_all()
    matches = Match.get_all()
    home_matches = Match.get_home_matches()
    away_matches = Match.get_away_matches()
    
    stats = {
        'total_players': len(players),
        'total_matches': len(matches),
        'home_matches': len(home_matches),
        'away_matches': len(away_matches),
        'partner_pairs': Player.get_partner_pairs()
    }
    
    return render_template('dashboard.html', stats=stats)
