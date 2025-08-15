from flask import Flask
from config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure data directory exists
    data_dir = os.path.dirname(app.config['DATABASE_PATH'])
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Initialize database
    from app.models.database import init_db
    with app.app_context():
        init_db()
    
    # Register blueprints
    from app.routes.main import main
    from app.routes.players import players
    from app.routes.matches import matches
    from app.routes.planning import planning
    
    app.register_blueprint(main)
    app.register_blueprint(players, url_prefix='/players')
    app.register_blueprint(matches, url_prefix='/matches')
    app.register_blueprint(planning, url_prefix='/planning')
    
    return app
