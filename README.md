# Teamplanning Programma - Sorry voor de Overlast

Een Python applicatie voor het beheren van teamplanning voor het dartsteam "Sorry voor de Overlast".

## Features

- **Wedstrijdschema Import**: Automatisch importeren van wedstrijden van teambeheer.nl
- **Spelersbeheer**: Beheer van spelergegevens met voorkeuren en beschikbaarheid
- **Slimme Planning**: Automatische planning met rekening houden van:
  - Speler beschikbaarheid
  - Partner voorkeuren (koppels die graag samen spelen)
  - Gelijke verdeling van speeltijd
  - Seizoensplanning optimalisatie
- **Versiebeheer**: Verschillende versies van planningen vergelijken
- **Definitieve Planning**: Bijhouden wie er daadwerkelijk heeft gespeeld

## Tech Stack

- **Backend**: Python 3.8+ met Flask
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript met Bootstrap 5
- **Data Parsing**: BeautifulSoup voor web scraping

## Project Structuur

```
sorry-voor-de-overlast/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models/              # Database modellen
│   │   ├── database.py      # Database configuratie
│   │   ├── player.py        # Speler model
│   │   └── match.py         # Wedstrijd model
│   ├── routes/              # Flask routes
│   │   ├── main.py          # Hoofd routes
│   │   ├── players.py       # Speler routes
│   │   ├── matches.py       # Wedstrijd routes
│   │   └── planning.py      # Planning routes
│   ├── services/            # Business logic
│   │   ├── planning.py      # Planning algoritmes
│   │   └── scraper.py       # Web scraping
│   └── templates/           # HTML templates
├── data/
│   └── database.db          # SQLite database
├── venv/                    # Virtual environment
├── config.py                # Configuratie
├── run.py                   # App starter
├── init_db.py              # Database initialisatie
└── requirements.txt         # Python dependencies
```

## Installatie

1. Clone de repository:
```bash
git clone <repository-url>
cd sorry-voor-de-overlast
```

2. Maak een virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Op Windows: venv\Scripts\activate
```

3. Installeer dependencies:
```bash
pip install -r requirements.txt
```

4. Initialiseer de database:
```bash
python init_db.py
```

## Gebruik

1. Start de applicatie:
```bash
source venv/bin/activate
python run.py
```

2. Open je browser en ga naar: `http://localhost:5001`

3. Begin met het importeren van wedstrijden:
   - Klik op "Import Wedstrijden" in het hoofdmenu
   - De applicatie probeert automatisch wedstrijden te importeren van teambeheer.nl
   - Als dat niet lukt, wordt fallback data gebruikt

4. Beheer je team:
   - Ga naar "Spelers" om teamleden toe te voegen/bewerken
   - Stel partner koppels in (bijv. Anita & Dirk, Jaap & Marise)
   - Beheer beschikbaarheid per speler per wedstrijd

5. Maak planningen:
   - Ga naar "Planning" om nieuwe planningen aan te maken
   - Gebruik automatische planning voor een snelle start
   - Pas handmatig aan waar nodig

## Kernfunctionaliteiten

### Spelersbeheer
- Toevoegen/bewerken van spelers
- Partner koppels voor voorkeursplanningen
- Rollen (Captain, Reserve Captain, etc.)
- Actief/inactief status

### Wedstrijdbeheer
- Import van teambeheer.nl
- Handmatig toevoegen van wedstrijden
- Thuis/uit wedstrijden
- Competitie vs vriendschappelijke wedstrijden

### Planning
- Automatische planning algoritmes
- Meerdere planning versies
- Definitieve vs concept planningen
- Vergelijking tussen planningen
- Beschikbaarheid tracking

### Dashboard
- Overzicht van team statistieken
- Aankomende wedstrijden
- Partner koppels overzicht
- Snelle acties

## Team Informatie

- **Team**: Sorry voor de Overlast
- **Competitie**: 4A
- **Seizoen**: 2025-2026
- **Thuisbasis**: Café De Vrijbuiter
- **Huidige Spelers**: 8 actieve spelers
- **Partner Koppels**: 2 vaste koppels

## Development

De applicatie is gebouwd met modulaire componenten:

- **Models**: Database interactie via SQLite
- **Routes**: Flask blueprints voor verschillende modules
- **Services**: Business logic (planning algoritmes, scraping)
- **Templates**: Bootstrap-based responsive UI

## Support

Voor vragen of problemen, neem contact op met de ontwikkelaar of maak een issue aan in de repository.

## Toekomstige Features

- [ ] Email notificaties voor spelers
- [ ] Mobile app ondersteuning
- [ ] Statistieken en rapportages
- [ ] Export naar kalenderapps
- [ ] Integratie met externe dartsborden
- [ ] Automatische resultaat import
```bash
python -m venv venv
source venv/bin/activate  # Op Windows: venv\Scripts\activate
```

3. Installeer dependencies:
```bash
pip install -r requirements.txt
```

4. Start de applicatie:
```bash
python run.py
```

## Gebruik

1. Open je browser en ga naar `http://localhost:5000`
2. Importeer het wedstrijdschema van teambeheer.nl
3. Voeg spelers toe met hun voorkeuren
4. Genereer automatische planningen
5. Bekijk en vergelijk verschillende versies
6. Zet de definitieve planning vast

## Team Info

- **Team**: Sorry voor de Overlast
- **Competitie**: 4A
- **Locatie**: Café De Vrijbuiter, Schubertplein 12, 7333 CV Apeldoorn
- **Seizoen**: 2025-2026

## Spelers

- Bea Brummel (C)
- Dion Nijland
- Anita Boomgaard-de Groot
- Dirk Boomgaard
- Iwan van Ee (RC)
- Jaap Draaijer (Bestuurslid)
- Marise Draaijer-Holierhoek
- Ruben Brem

## License

MIT License
