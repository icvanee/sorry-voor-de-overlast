#!/bin/bash

# Setup script voor lokale development environment

echo "🚀 Sorry voor de Overlast - Local Development Setup"
echo "=================================================="

# Functie om te kiezen welke database setup
show_menu() {
    echo ""
    echo "Welke database setup wil je gebruiken?"
    echo "1) SQLite (eenvoudig, geen Docker nodig)"
    echo "2) PostgreSQL via Docker (poort 5433, identiek aan productie)"
    echo "3) Bestaande lokale PostgreSQL (poort 5432)"
    echo "4) Stop PostgreSQL Docker containers"
    echo "5) Reset PostgreSQL database"
    echo "6) Toon database status"
    echo ""
    read -p "Kies een optie (1-6): " choice
}

# SQLite setup
setup_sqlite() {
    echo "📦 SQLite setup wordt geactiveerd..."
    cp .env.sqlite .env 2>/dev/null || echo "DATABASE_PATH=data/teamplanning.db" > .env
    echo "✅ SQLite configuratie actief"
    echo "💡 Run 'python run.py' om de app te starten"
}

# Bestaande PostgreSQL setup
setup_existing_postgresql() {
    echo "🗄️  Bestaande PostgreSQL setup wordt geactiveerd..."
    
    # Check of PostgreSQL bereikbaar is op poort 5432
    if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo "❌ PostgreSQL niet bereikbaar op localhost:5432"
        echo "💡 Zorg dat PostgreSQL draait of gebruik optie 2 voor Docker setup"
        exit 1
    fi
    
    # Kopieer bestaande PostgreSQL config
    cp .env.existing-postgres .env
    
    # Initialiseer database
    echo "🏗️  Database wordt gecontroleerd/aangemaakt..."
    createdb -h localhost -p 5432 teamplanning_dev 2>/dev/null || echo "Database bestaat al of kon niet worden aangemaakt"
    
    # Activeer virtual environment als het bestaat
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    # Initialiseer database
    python -c "
from app.models.database import init_db, seed_initial_data
try:
    init_db()
    seed_initial_data()
    print('✅ Database succesvol geïnitialiseerd')
except Exception as e:
    print(f'⚠️  Database al geïnitialiseerd of fout: {e}')
"
    
    echo "✅ Bestaande PostgreSQL setup compleet!"
    echo "📊 Database: localhost:5432, database: teamplanning_dev"
    echo "💡 Run 'python run.py' om de app te starten"
}
# PostgreSQL Docker setup
setup_postgresql() {
    echo "🐳 PostgreSQL Docker setup wordt gestart..."
    
    # Check of Docker draait
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is niet actief. Start Docker eerst."
        exit 1
    fi
    
    # Start PostgreSQL container
    echo "Starting PostgreSQL container..."
    docker-compose up -d postgres
    
    # Wacht tot PostgreSQL ready is
    echo "Wachten tot PostgreSQL ready is..."
    until docker-compose exec postgres pg_isready -U admin -d teamplanning > /dev/null 2>&1; do
        echo "⏳ PostgreSQL start nog op..."
        sleep 2
    done
    
    # Kopieer lokale PostgreSQL config
    cp .env.local .env
    
    # Initialiseer database
    echo "🏗️  Database wordt geïnitialiseerd..."
    
    # Activeer virtual environment als het bestaat
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    python -c "
from app.models.database import init_db, seed_initial_data
try:
    init_db()
    seed_initial_data()
    print('✅ Database succesvol geïnitialiseerd')
except Exception as e:
    print(f'⚠️  Database al geïnitialiseerd of fout: {e}')
"
    
    echo "✅ PostgreSQL setup compleet!"
    echo "🌐 Adminer (database GUI) beschikbaar op: http://localhost:8080"
    echo "📊 Database: localhost:5433, user: admin, password: admin123, db: teamplanning"
    echo "💡 Run 'python run.py' om de app te starten"
}

# Stop PostgreSQL containers
stop_postgresql() {
    echo "🛑 PostgreSQL containers worden gestopt..."
    docker-compose down
    echo "✅ PostgreSQL containers gestopt"
}

# Reset PostgreSQL database
reset_postgresql() {
    echo "🧹 PostgreSQL database wordt gereset..."
    docker-compose down -v
    docker-compose up -d postgres
    
    # Wacht tot PostgreSQL ready is
    until docker-compose exec postgres pg_isready -U admin -d teamplanning > /dev/null 2>&1; do
        echo "⏳ PostgreSQL start nog op..."
        sleep 2
    done
    
    # Herinitialiseer database
    
    # Activeer virtual environment als het bestaat
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    python -c "
from app.models.database import init_db, seed_initial_data
init_db()
seed_initial_data()
print('✅ Database gereset en geïnitialiseerd')
"
    echo "✅ Database reset compleet!"
}

# Status tonen
show_status() {
    echo "📊 Database Status:"
    echo "=================="
    
    if [ -f .env ]; then
        echo "📄 Actieve configuratie (.env):"
        grep -E "DATABASE_|DB_TYPE" .env || echo "Geen database configuratie gevonden"
    else
        echo "⚠️  Geen .env bestand gevonden"
    fi
    
    echo ""
    echo "🐳 Docker containers:"
    docker-compose ps
}

# Main menu
case "${1:-menu}" in
    "sqlite")
        setup_sqlite
        ;;
    "existing-postgres")
        setup_existing_postgresql
        ;;
    "postgresql"|"postgres")
        setup_postgresql
        ;;
    "stop")
        stop_postgresql
        ;;
    "reset")
        reset_postgresql
        ;;
    "status")
        show_status
        ;;
    "menu"|*)
        show_menu
        case $choice in
            1)
                setup_sqlite
                ;;
            2)
                setup_postgresql
                ;;
            3)
                setup_existing_postgresql
                ;;
            4)
                stop_postgresql
                ;;
            5)
                reset_postgresql
                ;;
            6)
                show_status
                ;;
            *)
                echo "❌ Ongeldige keuze"
                exit 1
                ;;
        esac
        ;;
esac
