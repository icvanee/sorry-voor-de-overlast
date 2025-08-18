from functools import wraps
from flask import session, redirect, url_for, flash, request, g, jsonify
from app.models.player import Player


def get_current_user():
    """Return the current logged-in player dict or None."""
    pid = session.get('player_id')
    if not pid:
        return None
    if getattr(g, '_current_user', None) and g._current_user.get('id') == pid:
        return g._current_user
    user = Player.get_by_id(pid)
    g._current_user = user
    return user


def login_user(player_id):
    session['player_id'] = player_id


def logout_user():
    session.pop('player_id', None)
    if hasattr(g, '_current_user'):
        delattr(g, '_current_user')


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not get_current_user():
            # JSON-aware response for API/AJAX calls
            if _wants_json_response():
                return jsonify({'success': False, 'error': 'Inloggen vereist.'}), 401
            flash('Log in om deze pagina te bekijken.', 'warning')
            # Preserve next URL for redirect after login
            return redirect(url_for('auth.login', next=request.path))
        # Enforce password change if flagged, except on auth routes
        path = request.path or ''
        if path.startswith(('/auth/login', '/auth/change-password')):
            return f(*args, **kwargs)
        user = get_current_user()
        if user and user.get('force_password_change'):
            if _wants_json_response():
                return jsonify({'success': False, 'error': 'Wachtwoord wijzigen vereist.'}), 403
            flash('Wijzig eerst je wachtwoord om verder te gaan.', 'warning')
            return redirect(url_for('auth.change_password', next=path))
        return f(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    roles = set(r.lower() for r in roles)
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                if _wants_json_response():
                    return jsonify({'success': False, 'error': 'Inloggen vereist.'}), 401
                flash('Log in vereist.', 'warning')
                return redirect(url_for('auth.login', next=request.path))
            role = (user.get('role') or 'speler').lower()
            if role not in roles:
                if _wants_json_response():
                    return jsonify({'success': False, 'error': 'Geen permissie voor deze actie.'}), 403
                flash('Geen permissie voor deze actie.', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def _wants_json_response():
    """Heuristic to decide if the current request expects JSON.
    Covers fetch/XHR, API routes and clients sending JSON or accepting JSON over HTML.
    """
    try:
        # XHR/fetch hint
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return True
        # JSON body
        if request.is_json:
            return True
        # Accept header prefers JSON
        accepts = getattr(request, 'accept_mimetypes', None)
        if accepts and accepts.accept_json and not accepts.accept_html:
            return True
        # API-ish paths or non-GET JSON endpoints
        path = request.path or ''
        if path.startswith(('/planning/api', '/api/')):
            return True
    except Exception:
        # Be conservative
        return False
    return False
