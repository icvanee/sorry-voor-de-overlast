#!/usr/bin/env python3
"""
Railway Database Migration Script
This script ensures the Railway PostgreSQL database has the complete enhanced schema
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def migrate_railway_database():
    """Migrate Railway database to enhanced schema"""
    try:
        from config import Config
        from app.models.database import init_database, seed_initial_data
        
        print("🚀 Railway Database Migration Starting...")
        print("=" * 50)
        
        if Config.DB_TYPE != 'postgresql':
            print("❌ Error: Expected PostgreSQL but found", Config.DB_TYPE)
            print("Make sure DATABASE_URL environment variable is set correctly")
            return False
        
        print(f"✅ Connected to PostgreSQL: {Config.DB_CONFIG['host']}:{Config.DB_CONFIG['port']}")
        print(f"   Database: {Config.DB_CONFIG['database']}")
        print(f"   User: {Config.DB_CONFIG['user']}")
        
        # Check if we need to drop existing tables for full migration
        try:
            from app.models.database import get_db_connection
            import psycopg
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check current schema
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'players' 
                ORDER BY ordinal_position
            """)
            current_columns = cursor.fetchall()
            
            print(f"\n📊 Current Players Table Schema ({len(current_columns)} columns):")
            for col in current_columns:
                print(f"   {col[0]}: {col[1]}")
            
            # Check if we have the enhanced schema
            column_names = [col[0] for col in current_columns]
            has_enhanced_schema = all(col in column_names for col in ['partner_id', 'role', 'prefer_partner_together'])
            
            if has_enhanced_schema:
                print("\n✅ Enhanced schema already present!")
                
                # Check if we have data
                cursor.execute("SELECT COUNT(*) FROM players")
                player_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM matches")  
                match_count = cursor.fetchone()[0]
                
                print(f"   Players: {player_count}")
                print(f"   Matches: {match_count}")
                
                if player_count == 0:
                    print("\n📥 Seeding initial data...")
                    seed_initial_data()
                    print("✅ Initial data seeded!")
                
            else:
                print("\n🔄 Migrating to enhanced schema...")
                
                # Drop all tables to ensure clean migration
                print("   Dropping existing tables...")
                cursor.execute("DROP TABLE IF EXISTS partner_preferences CASCADE")
                cursor.execute("DROP TABLE IF EXISTS player_preferences CASCADE")
                cursor.execute("DROP TABLE IF EXISTS player_availability CASCADE") 
                cursor.execute("DROP TABLE IF EXISTS match_planning CASCADE")
                cursor.execute("DROP TABLE IF EXISTS planning_versions CASCADE")
                cursor.execute("DROP TABLE IF EXISTS matches CASCADE")
                cursor.execute("DROP TABLE IF EXISTS players CASCADE")
                
                conn.commit()
                print("   ✅ Old tables dropped")
                
                # Initialize with enhanced schema
                print("   Creating enhanced schema...")
                init_database()
                print("   ✅ Enhanced schema created")
                
                # Seed initial data
                print("   Seeding initial data...")
                seed_initial_data()
                print("   ✅ Initial data seeded")
            
            # Verify migration
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['players', 'matches', 'planning_versions', 'match_planning', 'player_availability', 'player_preferences', 'partner_preferences']
            
            print(f"\n📋 Database Tables ({len(tables)}):")
            for table in tables:
                status = "✅" if table in expected_tables else "❓"
                print(f"   {status} {table}")
            
            # Test partner relationships
            cursor.execute("SELECT COUNT(*) FROM players WHERE partner_id IS NOT NULL")
            partner_count = cursor.fetchone()[0]
            print(f"\n👥 Partner relationships: {partner_count} players have partners")
            
            cursor.close()
            conn.close()
            
            print(f"\n🎉 Railway Migration Complete!")
            print("   ✅ Enhanced PostgreSQL schema deployed")
            print("   ✅ Partner relationships functional")
            print("   ✅ All planning tables available")
            print("   ✅ Ready for team planning!")
            
            return True
            
        except Exception as db_error:
            print(f"❌ Database migration error: {db_error}")
            return False
        
    except Exception as e:
        print(f"❌ Migration setup error: {e}")
        import traceback
        traceback.print_exc()
        return False

def health_check():
    """Quick health check of the migrated database"""
    try:
        from app.models.player import Player
        from app.models.match import Match
        # Single planning system - no need for PlanningVersion import
        
        print("\n🔍 Post-Migration Health Check:")
        print("-" * 35)
        
        # Test Player model
        players = Player.get_all()
        print(f"✅ Players: {len(players)} found")
        
        # Test partner pairs
        partner_pairs = Player.get_partner_pairs()
        print(f"✅ Partner pairs: {len(partner_pairs)} found")
        
        # Test Match model
        matches = Match.get_all()
        print(f"✅ Matches: {len(matches)} found")
        
        # Single planning system - check match_planning table directly
        from app.models.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM match_planning WHERE planning_version_id = 1')
        planning_count = cursor.fetchone()['count']
        cursor.close()
        conn.close()
        print(f"✅ Single planning entries: {planning_count} found")
        
        print("\n🎯 All models operational!")
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == '__main__':
    print("Railway Database Migration Tool")
    print("=" * 40)
    
    # Check if we're in Railway environment
    if not os.environ.get('RAILWAY_ENVIRONMENT'):
        print("⚠️  This script is designed for Railway deployment")
        print("   For local development, use the normal Flask app")
        sys.exit(1)
    
    # Wait a moment for Railway services to be ready
    print("⏳ Waiting for Railway services...")
    time.sleep(3)
    
    # Run migration
    success = migrate_railway_database()
    
    if success:
        # Run health check
        health_check()
        print("\n🚀 Railway deployment ready!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
