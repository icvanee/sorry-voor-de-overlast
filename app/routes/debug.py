from flask import Blueprint, jsonify
from config import Config
from app.utils.db_adapter import get_database_info

debug = Blueprint('debug', __name__)

@debug.route('/debug/database')
def database_info():
    """Debug route to show database connection information"""
    if not Config.SECRET_KEY.endswith('2025'):  # Simple check to prevent access in real production
        return jsonify({'error': 'Access denied'}), 403
    
    info = get_database_info()
    return jsonify({
        'database_info': info,
        'environment': 'Railway' if Config.DATABASE_URL else 'Local',
        'config': {
            'db_type': Config.DB_TYPE,
            'has_database_url': bool(Config.DATABASE_URL)
        }
    })
