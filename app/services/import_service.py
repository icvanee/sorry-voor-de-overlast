"""
General import service for importing matches and players from teambeheer.nl
Deze service bevat algemene import functies die overal aangeroepen kunnen worden
"""

from app.models.match import Match
from app.models.player import Player
from app.services.scraper import TeamBeheerScraper
from flask import current_app
import traceback

class ImportService:
    """Service voor het importeren van wedstrijden en spelers"""
    
    def __init__(self):
        self.scraper = TeamBeheerScraper()
    
    def import_matches(self, use_static_fallback=True):
        """
        Importeer wedstrijden van teambeheer.nl
        
        Args:
            use_static_fallback (bool): Gebruik statische data als scraping faalt
            
        Returns:
            dict: Resultaat met aantal geïmporteerd, geskipt en errors
        """
        result = {
            'imported': 0,
            'skipped': 0,
            'errors': 0,
            'messages': [],
            'success': False
        }
        
        try:
            # Probeer eerst web scraping
            result['messages'].append("Starting match import from teambeheer.nl...")
            
            matches = self.scraper.scrape_matches()
            result['messages'].append(f"Found {len(matches)} matches to process")
            
            if len(matches) == 0:
                # Geen matches gevonden via scraping
                if use_static_fallback:
                    result['messages'].append("No matches found via scraping, trying static fallback...")
                    return self._import_static_matches(result)
                else:
                    result['messages'].append("No matches found via scraping and static fallback disabled")
                    return result
            
            # Importeer gevonden matches
            result = self._import_scraped_matches(matches, result)
            
            if result['imported'] == 0 and use_static_fallback:
                result['messages'].append("No new matches imported via scraping, trying static fallback...")
                return self._import_static_matches(result)
            
            result['success'] = True
            result['messages'].append(f"Import completed: {result['imported']} imported, {result['skipped']} skipped, {result['errors']} errors")
            
        except Exception as e:
            result['messages'].append(f"Error during scraping: {str(e)}")
            result['errors'] += 1
            
            # Probeer static fallback bij error
            if use_static_fallback:
                result['messages'].append("Trying static fallback due to scraping error...")
                return self._import_static_matches(result)
        
        return result
    
    def _import_scraped_matches(self, matches, result):
        """Importeer gescrapte wedstrijden naar database"""
        try:
            # Haal bestaande matches op
            existing_matches = Match.get_all()
            existing_keys = set()
            
            for existing in existing_matches:
                try:
                    # Handige manier om met zowel dict als Row objecten om te gaan
                    if hasattr(existing, '__getitem__'):
                        date = existing['match_date'] if 'match_date' in existing else existing['date']
                        home_team = existing['home_team']
                        away_team = existing['away_team']
                    else:
                        date = existing.match_date if hasattr(existing, 'match_date') else existing.date
                        home_team = existing.home_team
                        away_team = existing.away_team
                    
                    key = f"{date}_{home_team}_{away_team}"
                    existing_keys.add(key)
                except Exception as e:
                    result['messages'].append(f"Warning: Could not process existing match: {e}")
            
            # Importeer nieuwe matches
            for match_data in matches:
                try:
                    # Maak unieke key
                    match_key = f"{match_data['date']}_{match_data['home_team']}_{match_data['away_team']}"
                    
                    if match_key not in existing_keys:
                        result['messages'].append(f"Importing: {match_data['home_team']} vs {match_data['away_team']} on {match_data['date']}")
                        
                        Match.create(
                            home_team=match_data['home_team'],
                            away_team=match_data['away_team'],
                            match_date=match_data['date'],
                            is_home=match_data['is_home'],
                            is_cup_match=match_data['is_cup_match'],
                            location=match_data['venue']
                        )
                        result['imported'] += 1
                        existing_keys.add(match_key)
                    else:
                        result['messages'].append(f"Skipping existing: {match_data['home_team']} vs {match_data['away_team']} on {match_data['date']}")
                        result['skipped'] += 1
                        
                except Exception as e:
                    result['messages'].append(f"Error importing match {match_data}: {e}")
                    result['errors'] += 1
                    
        except Exception as e:
            result['messages'].append(f"Error processing scraped matches: {e}")
            result['errors'] += 1
            
        return result
    
    def _import_static_matches(self, result):
        """Importeer statische wedstrijden als fallback"""
        try:
            from app.services.scraper import STATIC_MATCHES
            
            for match_data in STATIC_MATCHES:
                try:
                    # Check of match al bestaat
                    existing_matches = Match.get_all()
                    exists = False
                    
                    for existing in existing_matches:
                        try:
                            if hasattr(existing, '__getitem__'):
                                existing_date = existing['match_date'] if 'match_date' in existing else existing['date']
                                existing_home = existing['home_team']
                                existing_away = existing['away_team']
                            else:
                                existing_date = existing.match_date if hasattr(existing, 'match_date') else existing.date
                                existing_home = existing.home_team
                                existing_away = existing.away_team
                            
                            if (str(existing_date) == match_data['date'] and 
                                existing_home == match_data['home_team'] and
                                existing_away == match_data['away_team']):
                                exists = True
                                break
                        except Exception as e:
                            result['messages'].append(f"Warning: Could not compare existing match: {e}")
                    
                    if not exists:
                        is_home = match_data['home_team'] == 'Sorry voor de overlast'
                        venue = 'Café De Vrijbuiter' if is_home else ''
                        
                        Match.create(
                            home_team=match_data['home_team'],
                            away_team=match_data['away_team'],
                            match_date=match_data['date'],
                            is_home=is_home,
                            is_cup_match=match_data.get('is_friendly', False),
                            location=venue
                        )
                        result['imported'] += 1
                        result['messages'].append(f"Imported static match: {match_data['home_team']} vs {match_data['away_team']}")
                    else:
                        result['skipped'] += 1
                        
                except Exception as e:
                    result['messages'].append(f"Error importing static match: {e}")
                    result['errors'] += 1
            
            result['success'] = True
            
        except Exception as e:
            result['messages'].append(f"Error importing static matches: {e}")
            result['errors'] += 1
            
        return result
    
    def import_players(self):
        """
        Importeer spelers van teambeheer.nl
        
        Returns:
            dict: Resultaat met aantal geïmporteerd, geskipt en errors
        """
        result = {
            'imported': 0,
            'skipped': 0,
            'errors': 0,
            'messages': [],
            'success': False
        }
        
        try:
            result['messages'].append("Starting player import from teambeheer.nl...")
            
            players = self.scraper.scrape_players()
            result['messages'].append(f"Found {len(players)} players to process")
            
            if len(players) == 0:
                result['messages'].append("No players found via scraping")
                return result
            
            # Haal bestaande spelers op
            existing_players = Player.get_all()
            existing_names = set()
            
            for existing in existing_players:
                try:
                    if hasattr(existing, '__getitem__'):
                        name = existing['name']
                    else:
                        name = existing.name
                    existing_names.add(name.lower().strip())
                except Exception as e:
                    result['messages'].append(f"Warning: Could not process existing player: {e}")
            
            # Importeer nieuwe spelers
            for player_data in players:
                try:
                    player_name = player_data['name'].strip()
                    player_role = player_data.get('role', 'speler')
                    
                    if player_name.lower() not in existing_names:
                        result['messages'].append(f"Importing player: {player_name} ({player_role})")
                        
                        Player.create(
                            name=player_name,
                            role=player_role,
                            is_active=True
                        )
                        result['imported'] += 1
                        existing_names.add(player_name.lower())
                    else:
                        # Update role van bestaande speler als deze anders is
                        try:
                            existing_player = None
                            for existing in existing_players:
                                if hasattr(existing, '__getitem__'):
                                    if existing['name'].lower().strip() == player_name.lower():
                                        existing_player = existing
                                        break
                                else:
                                    if existing.name.lower().strip() == player_name.lower():
                                        existing_player = existing
                                        break
                            
                            if existing_player:
                                existing_role = existing_player['role'] if hasattr(existing_player, '__getitem__') else existing_player.role
                                if existing_role != player_role:
                                    Player.update_role(existing_player['id'] if hasattr(existing_player, '__getitem__') else existing_player.id, player_role)
                                    result['messages'].append(f"Updated role for {player_name}: {existing_role} -> {player_role}")
                                else:
                                    result['messages'].append(f"Skipping existing player: {player_name} ({player_role})")
                        except Exception as e:
                            result['messages'].append(f"Warning: Could not update role for {player_name}: {e}")
                        
                        result['skipped'] += 1
                        
                except Exception as e:
                    result['messages'].append(f"Error importing player {player_data}: {e}")
                    result['errors'] += 1
            
            result['success'] = True
            result['messages'].append(f"Player import completed: {result['imported']} imported, {result['skipped']} skipped, {result['errors']} errors")
            
        except Exception as e:
            result['messages'].append(f"Error during player import: {str(e)}")
            result['errors'] += 1
            traceback.print_exc()
        
        return result

# Convenience functions voor backwards compatibility
def import_matches(use_static_fallback=True):
    """Convenience function voor het importeren van wedstrijden"""
    service = ImportService()
    return service.import_matches(use_static_fallback)

def import_players():
    """Convenience function voor het importeren van spelers"""
    service = ImportService()
    return service.import_players()
