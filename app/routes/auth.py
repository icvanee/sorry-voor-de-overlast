from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.player import Player
from app.utils.auth import login_user, logout_user, get_current_user

auth = Blueprint('auth', __name__)


@auth.app_context_processor
def inject_user():
    user = get_current_user()
    def has_role(*roles):
        if not user:
            return False
        role = (user.get('role') or 'speler').lower()
        return role in {r.lower() for r in roles}
    return {
        'current_user': user,
        'has_role': has_role
    }


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        # Simple password-less login for initial MVP: email match
        # Extend later with real password hashing
        players = Player.get_all()
        found = next((p for p in players if (p.get('email') or '').strip().lower() == email), None)
        if found:
            login_user(found['id'])
            flash('Succesvol ingelogd.', 'success')
            next_url = request.args.get('next') or url_for('main.index')
            return redirect(next_url)
        else:
            flash('Onjuiste e-mail of geen account gevonden.', 'error')
    return render_template('auth/login.html')


@auth.route('/logout')
def logout():
    logout_user()
    flash('Uitgelogd.', 'info')
    return redirect(url_for('auth.login'))
