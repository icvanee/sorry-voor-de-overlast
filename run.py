import os
from app import create_app

def create_application():
    """Factory function to create Flask app"""
    print("🚀 Starting Flask application with PostgreSQL")
    return create_app()

# Create app instance for Gunicorn
app = create_application()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
