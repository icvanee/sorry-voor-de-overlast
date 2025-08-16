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
- Dit voorkomt problemen met speciale karakters, emoji's en command line limits
- Gebruik duidelijke, beschrijvende commit messages met emoji's voor leesbaarheid

## Speler Voorkeuren:
- Partner teams (spelen graag samen)
- Beschikbaarheid per datum
- Gelijke verdeling van speeltijd
- Seizoensplanning optimalisatie

## Planning Regels (BELANGRIJK):
- **HARDE REGEL: Maximum 4 spelers per wedstrijd** (darts competitie regel)
- Auto-generate planning moet zich hieraan houden
- Matrix view toont regel overtredingen in rood (table-danger)
- Beschikbaarheid van spelers moet gecontroleerd worden
- Eerlijke verdeling: spelers met minste wedstrijden krijgen prioriteit
