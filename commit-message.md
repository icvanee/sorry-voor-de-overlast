🎯 Implementeer general import service en variatie algoritme

## 🚀 General Import Service
- Nieuwe ImportService klasse voor herbruikbare import functies
- Import wedstrijden: teambeheer.nl scraping + static fallback
- Import spelers: met rol detectie (Captain, Reserve Captain, etc.)
- Betere error handling en gebruikersfeedback
- Clear all matches functie voor development

## 🎲 Regeneration Variatie Algoritme
- Smart scoring systeem: match_count + recent_penalty
- Recent play tracking (laatste 3 wedstrijden)
- Randomized selection binnen score groepen
- Graduated selection: minder uit hogere score groepen
- Voorkomt voorspelbare 4-4 patronen

## 🔧 Legacy Cleanup & Bug Fixes
- Verwijderd oude planning service imports
- Player model aangepast voor single planning
- Test files gerepareerd
- selected_count bug fix in regeneration

## 🎨 UI Improvements
- Import buttons in dashboard, sidebar en matches list
- Clear all matches met dubbele bevestiging
- Betere flash messages met details
- Beide import functies toegankelijk

Klaar voor Railway deployment voorbereiding!
