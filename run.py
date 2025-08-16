import os
from app import create_app

def create_application():
    """Factory function to create Flask app"""
    # Initialize database on Railway with enhanced schema
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        try:
            # Use our enhanced migration script for Railway
            from migrate_railway_db import migrate_railway_database
            print("🚀 Running Railway database migration...")
            success = migrate_railway_database()
            if not success:
                print("❌ Database migration failed!")
                raise Exception("Railway database migration failed")
            print("✅ Railway database migration completed")
        except Exception as e:
            print(f"❌ Railway database initialization error: {e}")
            # Fallback to old method if migration fails
            try:
                print("🔄 Attempting fallback database initialization...")
                from init_railway_db import ensure_database
                ensure_database()
                print("⚠️  Using fallback database initialization")
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                raise e
    else:
        # Local development - just use regular database initialization
        print("🏠 Local development mode - using standard database initialization")
    
    return create_app()

# Create app instance for Gunicorn
app = create_application()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
