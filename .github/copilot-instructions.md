# Teamplanning Programma - Sorry voor de Overlast

Dit is een Python applicatie voor het beheren van teamplanning voor het dartsteam "Sorry voor de Overlast".

## Functionaliteiten:
- Importeren van wedstrijdschema van teambeheer.nl
- Beheren van spelergegevens en beschikbaarheid
- Automatische planning met rekening houden van voorkeuren
- Versiebeheer van planningen
- Definitieve planning bijhouden

## Tech Stack:
- Python 3.8+
- SQLite database
- Flask web interface
- HTML/CSS/JavaScript frontend

## Development Guidelines:
- Gebruik modulaire code structuur
- Implementeer error handling
- Schrijf tests voor belangrijke functionaliteiten
- Houd rekening met Nederlandse datumformaten
- Zorg voor goede logging

## Git & Commit Best Practices:
- Voor lange commit messages: gebruik tijdelijk .md bestand om parser errors te voorkomen
  ```bash
  # 1. Maak tijdelijk commit-message.md bestand
  # 2. git commit -F commit-message.md
  # 3. rm commit-message.md
  ```
- Voor GitHub PR's met lange beschrijvingen: gebruik tijdelijk .md bestand
  ```bash
  # 1. Maak tijdelijk pr-body.md bestand met volledige PR beschrijving
  # 2. gh pr create --title "PR Title" --body-file pr-body.md
  # 3. rm pr-body.md
  ```
- Dit voorkomt problemen met speciale karakters, emoji's en command line limits
- Gebruik duidelijke, beschrijvende commit messages met emoji's voor leesbaarheid

## 🆕 Issue #22: Single Planning System

### Nieuwe Architectuur:
- **Eén planning** in plaats van meerdere versies
- **Planning Version ID = 1** voor alle single planning functionaliteit
- **Legacy system** blijft bestaan voor backwards compatibility

### Kernfunctionaliteiten:
- **SinglePlanning service** - Centrale planning logic
- **Pin systeem** - Spelers/wedstrijden vastpinnen
- **Actually played** - Registratie wie daadwerkelijk heeft gespeeld
- **Match status** - Bijhouden of wedstrijd is gespeeld (matches.is_played)
- **5e speler** - Extra spelers toevoegen en automatisch pinnen
- **Regeneratie** - Behoud gepinde items, herplan de rest

### Database Uitbreidingen:
- `matches.is_played` - Boolean voor wedstrijd status
- Gebruik bestaande `match_planning.is_pinned` en `match_planning.actually_played`
- Single planning gebruikt altijd `planning_version_id = 1`

### Routes:
- `/planning/single/` - Nieuw dashboard
- `/planning/single/match/<id>` - Match details
- API endpoints voor pin/unpin, actually_played, regeneration

### Migratie Strategie:
- Legacy planning systeem blijft werken
- Nieuwe functionaliteit via Single Planning
- Geleidelijke overgang mogelijk

## Planning Regels (KRITIEKE BUSINESS LOGIC):

### 🎯 Harde Regels (NOOIT overtreden):
- **PRECIES 4 SPELERS PER WEDSTRIJD** - Darts competitie voorschrift
- **ALLEEN BESCHIKBARE SPELERS** - Check player_availability tabel (bij auto-generate)
- **GEEN DUBBELE PLANNING** - Speler kan niet 2x op zelfde datum

### ⚖️ Soft Regels (optimalisatie doelen):
- **Eerlijke verdeling** - Spelers met minste wedstrijden krijgen prioriteit
- **Partner teams** - Rekening houden met voorkeurspartners
- **Gelijke speeltijd** - Seizoensplanning optimaliseren
- **Evenredige uit/thuis verdeling** - Balans tussen uit- en thuiswedstrijden per speler

### 🎮 Manual Override Regels:
- **Handmatige matrix editing** kan ALTIJD alle regels overrulen
- **Auto-generate** houdt zich aan beschikbaarheid en 4-speler regel
- **Bij te weinig beschikbaren** - auto-generate doet zijn best, handmatig aanpassen mogelijk

### 🔍 Visuele Feedback Systeem:
- **ROOD (table-danger)** - ≠4 spelers = REGEL OVERTREDING (>4 of <4)
- **ORANJE** - Waarschuwing bij bijna vol/leeg
- **GROEN** - Optimale planning (precies 4 spelers)
- **GRIJS** - Niet beschikbare spelers

### 🤖 Auto-Generate Logic:
1. **Filter beschikbare spelers** (player_availability.is_available = TRUE)
2. **Selecteer PRECIES 4 spelers** per wedstrijd
3. **Bij <4 beschikbaren** - selecteer alle beschikbaren (handmatige aanpassing nodig)
4. **Prioriteer spelers** met minste wedstrijden
5. **Respecteer partner voorkeuren** indien mogelijk
6. **Balanceer uit/thuis verdeling** per speler zoveel mogelijk
7. **Valideer eindresultaat** - streef naar 4 spelers per match

### 🚨 Implementatie Checks:
- AutoPlanningService._select_players_for_match() MOET precies 4 spelers selecteren
- Matrix view MOET visuele feedback tonen (rood voor ≠4 spelers)
- API endpoints MOETEN handmatige overrides toestaan
- Auto-generate RESPECTEERT beschikbaarheid, handmatig OVERSCHRIJFT alles
- Database constraints VOORKOMEN dubbele planning op zelfde datum
