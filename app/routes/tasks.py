from flask import Blueprint, jsonify, request, abort
import os
from app.models.match import Match
from app.models.player import Player
from app.services.single_planning import SinglePlanning
from app.services.email_service import EmailService


tasks = Blueprint('tasks', __name__, url_prefix='/tasks')


def _check_task_token():
    token = request.headers.get('X-Task-Token') or request.args.get('token')
    expected = os.environ.get('TASKS_SECRET')
    if not expected or token != expected:
        abort(401)


def _render_match_email_html(match, players):
    loc = 'Thuis' if match['is_home'] else 'Uit'
    date_str = match['match_date'].strftime('%Y-%m-%d') if match.get('match_date') else ''
    names = ', '.join([p['name'] for p in players]) if players else 'Nog geen selectie'
    location = match.get('location') or ''
    cup = ' (Beker)' if match.get('is_cup_match') else ''
    return f"""
    <h3>Aankondiging wedstrijd{cup}</h3>
    <p><strong>{match['home_team']}</strong> vs <strong>{match['away_team']}</strong></p>
    <ul>
      <li>Datum: {date_str}</li>
      <li>Locatie: {loc}{' - ' + location if location else ''}</li>
      <li>Spelers: {names}</li>
    </ul>
    <p>Succes en veel plezier!<br>Teamplanning – Sorry voor de Overlast</p>
    """


@tasks.route('/send-weekly-reminder', methods=['POST', 'GET'])
def send_weekly_reminder():
    """Send an email on Saturday evening with next week's match info to all players.
    Secured via TASKS_SECRET. Can be invoked by Railway cron.
    """
    _check_task_token()

    if not EmailService.is_enabled():
        return jsonify({'success': False, 'message': 'Email not configured'}), 400

    # Find the next match (today or later)
    upcoming = Match.get_upcoming(limit=1)
    if not upcoming:
        return jsonify({'success': True, 'message': 'No upcoming match'}), 200

    match = upcoming[0]

    # Get planning for that match
    planning = SinglePlanning.get_match_planning(match['id'])
    players = [{'id': p['player_id'], 'name': p['player_name'], 'email': None} for p in planning]

    # Fallback: include all players as recipients
    all_players = Player.get_all()
    recipient_emails = []
    for p in all_players:
        email = (p.get('email') or '').strip()
        if email:
            recipient_emails.append(email)

    date_str = match['match_date'].strftime('%d-%m-%Y') if match.get('match_date') else ''
    subject = f"Wedstrijd aankondiging: {match['home_team']} vs {match['away_team']} – {date_str}"
    html = _render_match_email_html(match, players)
    text = (
        f"Aankondiging wedstrijd\n"
        f"{match['home_team']} vs {match['away_team']}\n"
        f"Datum: {match['match_date']}\n"
        f"Locatie: {'Thuis' if match['is_home'] else 'Uit'}\n"
    )

    EmailService.send_email(recipient_emails, subject, html, text_body=text)
    return jsonify({'success': True, 'sent_to': len(recipient_emails)})
