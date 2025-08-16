# Railway Deployment Checklist
# Sorry voor de Overlast - Team Planning App

## Pre-Deployment Verificatie

### 1. Database Schema Status
- [x] Lokale PostgreSQL schema geüpdatet met alle tables
- [x] Partner relationships geïmplementeerd  
- [x] Planning versioning toegevoegd
- [x] Enhanced match tracking actief
- [x] Alle models getest lokaal

### 2. Environment Variables (Railway)
Zorg dat deze environment variables zijn ingesteld in Railway dashboard:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
RAILWAY_ENVIRONMENT=production

# Flask Configuration  
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
PORT=5000

# Optional: Debug settings
FLASK_DEBUG=false
```

### 3. Railway Database Migration
Bij eerste deployment of als database schema verandert:

```bash
# Na Railway deployment, check logs voor:
🚀 Running Railway database migration...
✅ Connected to PostgreSQL: [host:port]
🔄 Migrating to enhanced schema...
✅ Enhanced schema created
✅ Initial data seeded
🎉 Railway Migration Complete!
```

### 4. Deployment Process

#### Stap 1: Commit en Push
```bash
git add .
git commit -m "Railway deployment with enhanced database schema"
git push origin main
```

#### Stap 2: Railway Deploy
- Railway detecteert automatisch wijzigingen
- Nieuwe deployment start automatisch
- Database migratie script draait bij opstarten

#### Stap 3: Verificatie
Check Railway logs voor:
- ✅ Database connection successful
- ✅ Enhanced schema deployed
- ✅ Partner relationships functional
- ✅ All models operational

### 5. Post-Deployment Tests

#### Test 1: Database Schema
```bash
# In Railway console of via database viewer:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

# Verwacht: 7 tables
# - matches
# - match_planning  
# - partner_preferences
# - player_availability
# - player_preferences
# - players
# - planning_versions
```

#### Test 2: Sample Data
```bash
# Check dat initial data is geladen:
SELECT COUNT(*) FROM players;        -- Verwacht: 8
SELECT COUNT(*) FROM matches;        -- Verwacht: 4
SELECT COUNT(*) FROM planning_versions; -- Verwacht: 1
```

#### Test 3: Partner Relationships
```bash
SELECT 
    p1.name as player,
    p2.name as partner
FROM players p1 
LEFT JOIN players p2 ON p1.partner_id = p2.id
WHERE p1.partner_id IS NOT NULL;
-- Verwacht: 4 rows (2 partner pairs)
```

#### Test 4: Web Interface
- Ga naar Railway URL
- Test alle routes:
  - `/` - Dashboard
  - `/players` - Spelers overzicht
  - `/matches` - Wedstrijden
  - `/planning` - Team planning
  - `/planning/version/1` - Planning details

### 6. Troubleshooting

#### Database Connection Issues
```bash
# Check DATABASE_URL format:
postgresql://user:password@host:port/database
```

#### Schema Migration Failed
```bash
# In Railway logs, zoek naar:
❌ Migration setup error
❌ Database migration error

# Check fallback activation:
🔄 Attempting fallback database initialization...
⚠️  Using fallback database initialization
```

#### Missing Environment Variables
```bash
# Zet alle required variables in Railway dashboard
# Check met: echo $DATABASE_URL
```

### 7. Rollback Plan
Bij problemen:

1. **Database Issues**: 
   - Railway PostgreSQL kan gereset worden
   - Migratie script draait opnieuw bij herstart

2. **Code Issues**:
   - `git revert HEAD` voor laatste commit
   - Railway redeploys automatisch

3. **Complete Rollback**:
   - Ga naar Railway dashboard
   - Gebruik "Rollback to Previous Deployment"

### 8. Performance Check
Na deployment:
- Check response times < 500ms
- Database queries optimaal
- Geen memory leaks
- Alle partner queries werken correct

### 9. Data Backup
Railway PostgreSQL:
- Automatische backups via Railway
- Manual export mogelijk via database tools
- Local backup: `pg_dump` via Railway console

### 10. Success Criteria
✅ Railway app toegankelijk via URL
✅ Alle 8 spelers zichtbaar met partner info
✅ 4 test matches geïmporteerd  
✅ Team planning functionaliteit werkt
✅ Partner relationships correct weergegeven
✅ Geen errors in Railway logs
✅ Database schema volledig gemigreerd
