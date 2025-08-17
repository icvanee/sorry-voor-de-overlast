from flask import Flask
from config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Only create data directory for SQLite
    if Config.DB_TYPE == 'sqlite':
        data_dir = os.path.dirname(Config.DATABASE_PATH)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    # Initialize database
    from app.models.database import init_database
    with app.app_context():
        init_database()
    
    # Register blueprints
    from app.routes.main import main
    from app.routes.players import players
    from app.routes.matches import matches
    from app.routes.single_planning import single_planning
    from app.routes.auth import auth
    from app.routes.debug import debug
    from app.routes.test import test
    
    app.register_blueprint(main)
    app.register_blueprint(players, url_prefix='/players')
    app.register_blueprint(matches, url_prefix='/matches')
    app.register_blueprint(single_planning)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(debug, url_prefix='/debug')
    app.register_blueprint(test, url_prefix='/test')
    
    return app
