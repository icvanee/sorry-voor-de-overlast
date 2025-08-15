from flask import Blueprint, jsonify, request
import os
from config import Config

test = Blueprint('test', __name__)

@test.route('/db-info')
def database_info():
    """Simple database info endpoint for testing"""
    try:
        info = {
            'database_url_exists': bool(os.environ.get('DATABASE_URL')),
            'db_type': getattr(Config, 'DB_TYPE', 'unknown'),
            'railway_env': bool(os.environ.get('RAILWAY_ENVIRONMENT')),
            'database_path': getattr(Config, 'DATABASE_PATH', None),
        }
        
        if hasattr(Config, 'DB_CONFIG') and Config.DB_CONFIG:
            info['db_host'] = Config.DB_CONFIG.get('host', 'N/A')
            info['db_port'] = Config.DB_CONFIG.get('port', 'N/A')
            info['db_name'] = Config.DB_CONFIG.get('database', 'N/A')
        
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
