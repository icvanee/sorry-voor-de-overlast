import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from app.models.match import Match
from app.models.player import Player
from flask import current_app

class TeamBeheerScraper:
    def __init__(self):
        self.base_url = current_app.config['TEAM_URL']
        self.team_name = current_app.config['TEAM_NAME']
    
    def scrape_matches(self):
        """Scrape matches from teambeheer.nl"""
        try:
            print(f"Scraping matches from: {self.base_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(self.base_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            matches = []
            
            print(f"Page title: {soup.title.string if soup.title else 'No title'}")
            
            # Look specifically for the "Wedstrijden" header
            wedstrijden_header = soup.find('h2', string=re.compile(r'Wedstrijden', re.I))
            if not wedstrijden_header:
                wedstrijden_header = soup.find('h2', class_='ui header', string=re.compile(r'Wedstrijden', re.I))
            
            if wedstrijden_header:
                print("Found 'Wedstrijden' header, looking for match table...")
                
                # Find the table after the wedstrijden header
                current_element = wedstrijden_header
                match_table = None
                
                # Look for the next table element
                for sibling in wedstrijden_header.find_next_siblings():
                    if sibling.name == 'table':
                        match_table = sibling
                        break
                    # Also check for tables within divs
                    table_in_div = sibling.find('table')
                    if table_in_div:
                        match_table = table_in_div
                        break
                
                # If no sibling table, look in parent containers
                if not match_table:
                    parent = wedstrijden_header.parent
                    if parent:
                        match_table = parent.find('table')
                
                if match_table:
                    print("Found match table, processing rows...")
                    rows = match_table.find_all('tr')
                    
                    for row_idx, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            match_data = self._parse_match_row(cells, row_idx)
                            if match_data:
                                matches.append(match_data)
                                print(f"Found match: {match_data['home_team']} vs {match_data['away_team']} on {match_data['date']}")
                else:
                    print("No table found after wedstrijden header")
            else:
                print("'Wedstrijden' header not found, trying general table search...")
                
                # Fallback: Look for tables with match data
                tables = soup.find_all('table')
                print(f"Found {len(tables)} tables")
                
                for i, table in enumerate(tables):
                    print(f"Processing table {i+1}")
                    rows = table.find_all('tr')
                    
                    for row_idx, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            match_data = self._parse_match_row(cells, row_idx)
                            if match_data:
                                matches.append(match_data)
                                print(f"Found match: {match_data['home_team']} vs {match_data['away_team']} on {match_data['date']}")
            
            print(f"Total matches found: {len(matches)}")
            return matches
            
        except Exception as e:
            print(f"Error scraping matches: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def scrape_players(self):
        """Scrape players from teambeheer.nl"""
        try:
            print(f"Scraping players from: {self.base_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(self.base_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            players = []
            
            # Look for the "Spelers" header
            spelers_header = soup.find('h2', string=re.compile(r'Spelers', re.I))
            if not spelers_header:
                spelers_header = soup.find('h2', class_='ui header', string=re.compile(r'Spelers', re.I))
            
            if spelers_header:
                print("Found 'Spelers' header, looking for player table...")
                
                # Find the table after the spelers header
                player_table = None
                
                # Look for the next table element
                for sibling in spelers_header.find_next_siblings():
                    if sibling.name == 'table':
                        player_table = sibling
                        break
                    # Also check for tables within divs
                    table_in_div = sibling.find('table')
                    if table_in_div:
                        player_table = table_in_div
                        break
                
                if player_table:
                    print("Found player table, processing rows...")
                    rows = player_table.find_all('tr')
                    
                    for row_idx, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 1:
                            player_data = self._parse_player_row(cells, row_idx)
                            if player_data:
                                players.append(player_data)
                                print(f"Found player: {player_data['name']}")
            
            print(f"Total players found: {len(players)}")
            return players
            
        except Exception as e:
            print(f"Error scraping players: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_player_row(self, cells, row_idx=0):
        """Parse a single player row from the table"""
        try:
            # Extract text from cells
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            if len(cell_texts) < 1:
                return None
            
            print(f"Player row {row_idx}: {cell_texts}")
            
            # Skip header rows
            if any(header in ' '.join(cell_texts).lower() for header in ['naam', 'speler', 'singles', 'winst']):
                return None
            
            # First cell should be the player name
            raw_name = cell_texts[0].strip()
            
            # Skip empty or invalid names
            if not raw_name or len(raw_name) < 2 or raw_name.lower() in ['totaal', 'total']:
                return None
            
            # Extract role and clean name
            player_name, role = self._parse_player_name_and_role(raw_name)
            
            # Extract additional info if available
            singles_played = None
            wins = None
            
            if len(cell_texts) >= 2:
                try:
                    singles_played = int(cell_texts[1]) if cell_texts[1].isdigit() else None
                except:
                    pass
            
            if len(cell_texts) >= 3:
                try:
                    wins = int(cell_texts[2]) if cell_texts[2].isdigit() else None
                except:
                    pass
            
            return {
                'name': player_name,
                'role': role,
                'singles_played': singles_played,
                'wins': wins
            }
            
        except Exception as e:
            print(f"Error parsing player row {row_idx}: {e}")
            return None
    
    def _parse_player_name_and_role(self, raw_name):
        """Parse player name and extract role from teambeheer.nl format"""
        # Role mappings based on the provided information
        role_mappings = {
            'C': 'Captain',
            'RC': 'Reserve Captain', 
            'Bestuurslid': 'Bestuurslid'
        }
        
        # Clean the name and extract role
        name = raw_name
        role = 'speler'  # Default role
        
        # Check for specific role indicators
        if 'Bestuurslid' in name:
            role = 'Bestuurslid'
            name = name.replace('Bestuurslid', '').strip()
        elif name.endswith('RC'):
            role = 'Reserve Captain'
            name = name[:-2].strip()
        elif name.endswith('C'):
            role = 'Captain'
            name = name[:-1].strip()
        
        # Clean up extra spaces
        name = ' '.join(name.split())
        
        return name, role
    
    def _parse_match_row(self, cells, row_idx=0):
        """Parse a single match row from the table"""
        try:
            # Extract text from cells
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            if len(cell_texts) < 3:
                return None
            
            print(f"Row {row_idx}: {cell_texts}")
            
            # Skip header rows
            if any(header in ' '.join(cell_texts).lower() for header in ['datum', 'wedstrijd', 'team', 'tijd', 'uitslag']):
                return None
            
            # Try different column arrangements
            match_data = None
            
            # Format 1: [ronde, datum, thuis, uit, tijd/uitslag]
            if len(cell_texts) >= 4:
                try:
                    ronde = cell_texts[0]
                    datum = cell_texts[1] 
                    thuis = cell_texts[2]
                    uit = cell_texts[3]
                    
                    if self._is_valid_date(datum) and thuis and uit:
                        match_data = self._create_match_data(ronde, datum, thuis, uit)
                except:
                    pass
            
            # Format 2: [datum, thuis, uit, tijd/uitslag]
            if not match_data and len(cell_texts) >= 3:
                try:
                    datum = cell_texts[0]
                    thuis = cell_texts[1] 
                    uit = cell_texts[2]
                    
                    if self._is_valid_date(datum) and thuis and uit:
                        match_data = self._create_match_data('', datum, thuis, uit)
                except:
                    pass
            
            # Format 3: Look for team names in any position
            if not match_data:
                for i, cell in enumerate(cell_texts):
                    if self.team_name.lower() in cell.lower():
                        # Found our team, look for opponent and date
                        for j, other_cell in enumerate(cell_texts):
                            if i != j and self._is_valid_date(other_cell):
                                # Found date, determine home/away
                                for k, potential_opponent in enumerate(cell_texts):
                                    if k != i and k != j and potential_opponent and len(potential_opponent) > 3:
                                        if i < k:  # Our team listed first = home
                                            match_data = self._create_match_data('', other_cell, cell, potential_opponent)
                                        else:  # Our team listed second = away
                                            match_data = self._create_match_data('', other_cell, potential_opponent, cell)
                                        break
                                break
                        break
            
            return match_data
            
        except Exception as e:
            print(f"Error parsing match row {row_idx}: {e}")
            return None
    
    def _parse_match_div(self, div):
        """Parse match data from a div element"""
        try:
            text = div.get_text(strip=True)
            
            # Look for our team name
            if self.team_name.lower() not in text.lower():
                return None
            
            # Extract date patterns
            date_patterns = re.findall(r'\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?', text)
            
            if date_patterns:
                date_str = date_patterns[0]
                parsed_date = self._parse_date(date_str)
                
                if parsed_date:
                    # Try to extract team names around the date
                    parts = re.split(r'\d{1,2}[-/]\d{1,2}', text)
                    if len(parts) >= 2:
                        before_date = parts[0].strip()
                        after_date = parts[1].strip()
                        
                        # Simple heuristic for home/away
                        if self.team_name in before_date:
                            return self._create_match_data('', parsed_date, self.team_name, after_date)
                        else:
                            return self._create_match_data('', parsed_date, before_date, self.team_name)
            
            return None
            
        except Exception as e:
            print(f"Error parsing match div: {e}")
            return None
    
    def _is_valid_date(self, date_str):
        """Check if string looks like a date"""
        if not date_str:
            return False
        
        # Check for common date patterns
        patterns = [
            r'\d{1,2}[-/]\d{1,2}',          # dd-mm or dd/mm
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', # dd-mm-yyyy
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'    # yyyy-mm-dd
        ]
        
        return any(re.match(pattern, date_str.strip()) for pattern in patterns)
    
    def _create_match_data(self, match_number, date_str, home_team, away_team):
        """Create standardized match data"""
        try:
            # Clean team names
            home_team = home_team.strip()
            away_team = away_team.strip()
            
            # Skip empty or invalid team names
            if not home_team or not away_team or len(home_team) < 2 or len(away_team) < 2:
                return None
            
            # Parse date
            parsed_date = self._parse_date(date_str)
            if not parsed_date:
                return None
            
            # Determine if this is a home match
            is_home = home_team.lower() == self.team_name.lower()
            
            # Determine if it's a cup match (bekerwedstrijd)
            # Cup matches have match numbers starting with 'b' (b1, b2, etc.)
            is_friendly = False
            if match_number:
                match_number_clean = match_number.strip().lower()
                if match_number_clean.startswith('b'):
                    is_friendly = True  # Cup matches are marked as friendly to distinguish from regular competition
                    print(f"Detected cup match (bekerwedstrijd): {match_number}")
            
            return {
                'match_number': match_number or '',
                'date': parsed_date,
                'home_team': home_team,
                'away_team': away_team,
                'is_home': is_home,
                'is_friendly': is_friendly,
                'venue': current_app.config['VENUE'] if is_home else ''
            }
            
        except Exception as e:
            print(f"Error creating match data: {e}")
            return None
    
    def _parse_date(self, date_str):
        """Parse date string to YYYY-MM-DD format"""
        try:
            if not date_str or date_str == 'Vrij':
                return None
            
            # Remove any extra whitespace
            date_str = date_str.strip()
            
            # Handle various date formats
            current_year = datetime.now().year
            
            # Format: dd-mm-yyyy or dd/mm/yyyy
            if re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}', date_str):
                date_str = date_str.replace('/', '-')
                day, month, year = date_str.split('-')
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Format: dd-mm or dd/mm (assume current season)
            elif re.match(r'\d{1,2}[-/]\d{1,2}$', date_str):
                date_str = date_str.replace('/', '-')
                day, month = date_str.split('-')
                
                # Determine year based on month (season runs from Aug to July)
                month_int = int(month)
                if month_int >= 8:  # August or later = current year
                    year = current_year
                else:  # Before August = next year
                    year = current_year + 1
                
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Format: yyyy-mm-dd (already correct)
            elif re.match(r'\d{4}-\d{1,2}-\d{1,2}', date_str):
                parts = date_str.split('-')
                return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            
            # Try to parse with datetime for other formats
            else:
                try:
                    # Try common formats
                    formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m', '%d/%m']
                    for fmt in formats:
                        try:
                            parsed = datetime.strptime(date_str, fmt)
                            if fmt in ['%d-%m', '%d/%m']:
                                # Add year for short formats
                                month = parsed.month
                                if month >= 8:
                                    year = current_year
                                else:
                                    year = current_year + 1
                                parsed = parsed.replace(year=year)
                            return parsed.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
                except:
                    pass
            
            print(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            print(f"Error parsing date {date_str}: {e}")
            return None
    
    def import_matches_to_db(self):
        """Import scraped matches to database"""
        print("Starting match import from teambeheer.nl...")
        
        matches = self.scrape_matches()
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"Found {len(matches)} matches to process")
        
        # Get existing matches once
        existing_matches = Match.get_all()
        existing_keys = set()
        for existing in existing_matches:
            # Convert Row object to dict access
            date = existing['date'] if hasattr(existing, '__getitem__') else existing.date
            home_team = existing['home_team'] if hasattr(existing, '__getitem__') else existing.home_team
            away_team = existing['away_team'] if hasattr(existing, '__getitem__') else existing.away_team
            key = f"{date}_{home_team}_{away_team}"
            existing_keys.add(key)
        
        for match_data in matches:
            try:
                # Create unique key for this match
                match_key = f"{match_data['date']}_{match_data['home_team']}_{match_data['away_team']}"
                
                if match_key not in existing_keys:
                    print(f"Importing: {match_data['home_team']} vs {match_data['away_team']} on {match_data['date']}")
                    
                    Match.create(
                        match_number=match_data['match_number'],
                        date=match_data['date'],
                        home_team=match_data['home_team'],
                        away_team=match_data['away_team'],
                        is_home=match_data['is_home'],
                        is_friendly=match_data['is_friendly'],
                        venue=match_data['venue']
                    )
                    imported_count += 1
                    existing_keys.add(match_key)  # Add to prevent duplicates in this session
                else:
                    print(f"Skipping existing: {match_data['home_team']} vs {match_data['away_team']} on {match_data['date']}")
                    skipped_count += 1
                    
            except Exception as e:
                print(f"Error importing match {match_data}: {e}")
                error_count += 1
        
        print(f"Import completed: {imported_count} imported, {skipped_count} skipped, {error_count} errors")
        return imported_count

# Static data fallback for the current season
STATIC_MATCHES = [
    {'match_number': 'b1', 'date': '2024-09-09', 'home_team': 'Vrijbuiter 5', 'away_team': 'Sorry voor de overlast', 'is_friendly': True},
    {'match_number': '1', 'date': '2024-09-19', 'home_team': 'DVO 3 / Haar, fijne tuinen', 'away_team': 'Sorry voor de overlast', 'is_friendly': False},
    {'match_number': '2', 'date': '2024-09-24', 'home_team': 'Sorry voor de overlast', 'away_team': 'Hovenhuus de worp', 'is_friendly': False},
    {'match_number': '3', 'date': '2024-10-03', 'home_team': 'D.V. Vaassen 2', 'away_team': 'Sorry voor de overlast', 'is_friendly': False},
    {'match_number': '4', 'date': '2024-10-08', 'home_team': 'Sorry voor de overlast', 'away_team': 'Altijd op dreef', 'is_friendly': False},
    {'match_number': 'b2', 'date': '2024-10-15', 'home_team': "'t Kan maar zo", 'away_team': 'Sorry voor de overlast', 'is_friendly': True},
    {'match_number': '5', 'date': '2024-10-24', 'home_team': 'D.B.S. 3', 'away_team': 'Sorry voor de overlast', 'is_friendly': False},
    {'match_number': 'b3', 'date': '2024-10-29', 'home_team': 'Sorry voor de overlast', 'away_team': "No Bull's hit", 'is_friendly': True},
    {'match_number': '6', 'date': '2024-11-05', 'home_team': 'Sorry voor de overlast', 'away_team': 'The Misfire Mavericks', 'is_friendly': False},
    {'match_number': 'b4', 'date': '2024-11-14', 'home_team': 'Boysie 3', 'away_team': 'Sorry voor de overlast', 'is_friendly': True},
    {'match_number': '7', 'date': '2024-11-20', 'home_team': 'Bullgerenk 1', 'away_team': 'Sorry voor de overlast', 'is_friendly': False},
    {'match_number': '8', 'date': '2024-11-26', 'home_team': 'Sorry voor de overlast', 'away_team': 'Eureka No-Stars', 'is_friendly': False},
    {'match_number': 'b5', 'date': '2024-12-03', 'home_team': 'Sorry voor de overlast', 'away_team': 'De Lamme Jatjes', 'is_friendly': True},
    {'match_number': '9', 'date': '2024-12-10', 'home_team': 'Sorry voor de overlast', 'away_team': "De Duppies van Opa '90", 'is_friendly': False},
    {'match_number': '11', 'date': '2025-01-21', 'home_team': 'Sorry voor de overlast', 'away_team': 'D.B.S. 4', 'is_friendly': False},
    {'match_number': '12', 'date': '2025-01-28', 'home_team': 'Sorry voor de overlast', 'away_team': 'DVO 3 / Haar, fijne tuinen', 'is_friendly': False},
    {'match_number': '13', 'date': '2025-02-11', 'home_team': 'Hovenhuus de worp', 'away_team': 'Sorry voor de overlast', 'is_friendly': False},
    {'match_number': '14', 'date': '2025-02-18', 'home_team': 'Sorry voor de overlast', 'away_team': 'D.V. Vaassen 2', 'is_friendly': False},
    {'match_number': '15', 'date': '2025-02-27', 'home_team': 'Altijd op dreef', 'away_team': 'Sorry voor de overlast', 'is_friendly': False},
    {'match_number': '16', 'date': '2025-03-11', 'home_team': 'Sorry voor de overlast', 'away_team': 'D.B.S. 3', 'is_friendly': False},
    {'match_number': '17', 'date': '2025-03-20', 'home_team': 'The Misfire Mavericks', 'away_team': 'Sorry voor de overlast', 'is_friendly': False},
    {'match_number': '18', 'date': '2025-04-01', 'home_team': 'Sorry voor de overlast', 'away_team': 'Bullgerenk 1', 'is_friendly': False},
    {'match_number': '19', 'date': '2025-04-10', 'home_team': 'Eureka No-Stars', 'away_team': 'Sorry voor de overlast', 'is_friendly': False},
    {'match_number': '20', 'date': '2025-04-22', 'home_team': "De Duppies van Opa '90", 'away_team': 'Sorry voor de overlast', 'is_friendly': False},
    {'match_number': '22', 'date': '2025-05-08', 'home_team': 'D.B.S. 4', 'away_team': 'Sorry voor de overlast', 'is_friendly': False},
]

def import_static_matches():
    """Import static match data as fallback"""
    imported_count = 0
    
    for match_data in STATIC_MATCHES:
        try:
            # Check if match already exists
            existing_matches = Match.get_all()
            exists = any(
                existing['date'] == match_data['date'] and 
                existing['home_team'] == match_data['home_team'] and
                existing['away_team'] == match_data['away_team']
                for existing in existing_matches
            )
            
            if not exists:
                is_home = match_data['home_team'] == 'Sorry voor de overlast'
                venue = 'Café De Vrijbuiter' if is_home else ''
                
                Match.create(
                    match_number=match_data['match_number'],
                    date=match_data['date'],
                    home_team=match_data['home_team'],
                    away_team=match_data['away_team'],
                    is_home=is_home,
                    is_friendly=match_data['is_friendly'],
                    venue=venue
                )
                imported_count += 1
                
        except Exception as e:
            print(f"Error importing static match: {e}")
    
    return imported_count
