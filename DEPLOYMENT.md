# Deployment Workflow - Sorry voor de Overlast

## GitFlow Branch Strategy

### 🔧 Development Branches

- **`main`**: Production-ready code (master branch)
- **`develop`**: Integration branch voor features  
- **`feature/*`**: Feature branches - branchen van develop
- **`release/*`**: Release branches voor production deployment
- **`hotfix/*`**: Hotfixes voor production issues

### 🚀 GitFlow Deployment Process

1. **Feature Development:**

   ```bash
   git checkout develop
   git pull origin develop  
   git checkout -b feature/nieuwe-functie
   # ... werk aan feature
   git push -u origin feature/nieuwe-functie
   # Maak PR: feature/nieuwe-functie → develop
   ```

2. **Release Preparation:**

   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/v1.0.0
   # ... laatste aanpassingen, version bumps
   git push -u origin release/v1.0.0
   # Maak PR: release/v1.0.0 → main
   ```

3. **Production Deployment:**

   ```bash
   # Na merge van release → main:
   git checkout main
   git pull origin main
   git tag v1.0.0
   git push origin v1.0.0
   # Railway deployt automatisch vanaf main
   
   # Merge terug naar develop:
   git checkout develop
   git merge main
   git push origin develop
   ```

## Railway Configuration

- **Deploy Branch**: `main` (production)
- **Auto Deploy**: Enabled vanaf main branch
- **Environment**: Production
- **Database**: SQLite in `/tmp` directory

## Environment Variables (Railway)

```env
RAILWAY_ENVIRONMENT=true
FLASK_ENV=production
SECRET_KEY=railway-secret-key-sorry-voor-de-overlast-2025
```

## Branch Protection

Aanbevolen GitHub branch protection rules:

- **main**: Require PR reviews, no direct pushes
- **develop**: Require PR reviews voor features

## URL

Production app: <https://your-app.railway.app>

## Database

- **Development**: Local SQLite in `data/database.db`
- **Production**: SQLite in `/tmp/database.db` (auto-initialized)

## Monitoring

- Check Railway logs for deployment status
- Health check endpoint: `/`
- Database auto-initializes on first run
