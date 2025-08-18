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
        user = Player.get_by_email(email)
        if not user:
            flash('Onjuiste e-mail of geen account gevonden.', 'error')
            return render_template('auth/login.html')
        if not Player.verify_password(user, password):
            flash('Onjuist wachtwoord.', 'error')
            return render_template('auth/login.html')
        login_user(user['id'])
        # If user must change password, redirect there
        if user.get('force_password_change'):
            flash('Stel een nieuw wachtwoord in om door te gaan.', 'warning')
            return redirect(url_for('auth.change_password'))
        flash('Succesvol ingelogd.', 'success')
        next_url = request.args.get('next') or url_for('main.index')
        return redirect(next_url)
    return render_template('auth/login.html')


@auth.route('/logout')
def logout():
    logout_user()
    flash('Uitgelogd.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/change-password', methods=['GET', 'POST'])
def change_password():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login', next=url_for('auth.change_password')))
    if request.method == 'POST':
        current = request.form.get('current_password', '')
        new1 = request.form.get('new_password', '')
        new2 = request.form.get('confirm_password', '')
        # If forced change, allow default seed to bypass current check if user has force flag and current is default?
        if not Player.verify_password(user, current):
            flash('Huidig wachtwoord klopt niet.', 'error')
            return render_template('auth/change_password.html')
        if len(new1) < 8:
            flash('Nieuw wachtwoord moet minimaal 8 tekens zijn.', 'error')
            return render_template('auth/change_password.html')
        if new1 != new2:
            flash('Wachtwoorden komen niet overeen.', 'error')
            return render_template('auth/change_password.html')
        Player.set_password(user['id'], new1, force_change=False)
        Player.clear_force_change(user['id'])
        flash('Wachtwoord bijgewerkt.', 'success')
        next_url = request.args.get('next') or url_for('main.index')
        return redirect(next_url)
    return render_template('auth/change_password.html')
