# Development Database Setup

## PostgreSQL via Docker (Aanbevolen)

Voor een productie-identieke development omgeving gebruik PostgreSQL:

```bash
# Start PostgreSQL development setup
./setup-dev.sh postgresql

# Of handmatig:
docker-compose up -d postgres
cp .env.local .env
python -c "from app.models.database import init_db, seed_initial_data; init_db(); seed_initial_data()"
python run.py
```

### Database toegang

- **App**: localhost:5433
- **Adminer GUI**: <http://localhost:8080>
- **Credentials**: user=admin, password=admin123, database=teamplanning

## SQLite (Eenvoudig)

Voor snelle development zonder Docker:

```bash
# Start SQLite setup
./setup-dev.sh sqlite

# Of handmatig:
cp .env.sqlite .env
python run.py
```

## Nuttige commando's:

```bash
./setup-dev.sh                 # Interactieve menu
./setup-dev.sh postgresql      # Start PostgreSQL
./setup-dev.sh sqlite          # Schakel naar SQLite
./setup-dev.sh stop            # Stop Docker containers
./setup-dev.sh reset           # Reset PostgreSQL database
./setup-dev.sh status          # Toon huidige status
```

## Database management:

- **Adminer**: http://localhost:8080 (alleen bij PostgreSQL)
- **DBeaver**: Verbind met localhost:5432 voor lokale PostgreSQL
- **Railway PostgreSQL**: Gebruik trolley.proxy.rlwy.net:43227 (productie)
