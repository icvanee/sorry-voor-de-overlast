# Issue: Database Reset and Fresh Import Functionality

## 📋 Overview
Implementeer een "fresh start" functionaliteit waarmee gebruikers de database kunnen legen en opnieuw kunnen beginnen met het importeren van wedstrijd- en spelerdata van teambeheer.nl.

## 🎯 Use Cases and Scenarios

### Development & Testing:
- **Clean development environment** - Reset database voor testing
- **Bug reproduction** - Consistent starting point voor debugging
- **Feature testing** - Test nieuwe features met schone data
- **Demo preparation** - Reset voor presentaties

### Production Scenarios:
- **New season setup** - Begin nieuw seizoen met verse data
- **Data corruption recovery** - Herstel na database problemen
- **Team changes** - Nieuwe teamsamenstelling importeren
- **Migration testing** - Test data migration scenarios

### Admin Maintenance:
- **Performance reset** - Verwijder oude/onnodige data
- **System cleanup** - Periodieke database onderhoud
- **Backup restoration** - Herstel naar clean state

## 🚨 Current Situation Analysis

### What Works:
- ✅ **Individual imports** - Matches en players kunnen apart geïmporteerd worden
- ✅ **Scraper functionality** - teambeheer.nl scraper is functioneel
- ✅ **Database operations** - Basic CRUD operations werken

### What's Missing:
- ❌ **No reset functionality** - Geen manier om volledig opnieuw te beginnen
- ❌ **Manual cleanup required** - Handmatig database tabellen legen
- ❌ **No confirmation safeguards** - Risico van onbedoelde data loss
- ❌ **No backup creation** - Geen automatische backup voor reset

## 🔧 Proposed Solution: Database Reset System

### 🎛️ Reset Options Interface

```html
┌─────────────────────────────────────────────────────────────┐
│                 DATABASE RESET OPTIES                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ⚠️  WAARSCHUWING: Deze actie kan niet ongedaan gemaakt    │
│     worden. Alle data wordt permanent verwijderd!          │
│                                                             │
│ Reset Opties:                                               │
│ ☐ Matches (wedstrijden)                                    │
│ ☐ Players (spelers)                                        │
│ ☐ Player Availability (beschikbaarheid)                   │
│ ☐ Planning Versions (alle planningen)                     │
│ ☐ Match Planning (wedstrijd toewijzingen)                 │
│                                                             │
│ Import Opties:                                              │
│ ☑️ Auto-import matches van teambeheer.nl                   │
│ ☑️ Auto-import players van teambeheer.nl                   │
│                                                             │
│ [ Maak Backup ] [ Annuleren ] [ 🔄 RESET & IMPORT ]      │
└─────────────────────────────────────────────────────────────┘
```

### 🛡️ Safety Measures

#### Multi-Step Confirmation:
```html
Step 1: ⚠️  Are you sure? Type 'RESET' to confirm
Step 2: 📧 Email confirmation required for admin users  
Step 3: 💾 Automatic backup creation before reset
Step 4: ✅ Final confirmation with data summary
```

#### Backup Creation:
- **Automatic backup** - Voor elke reset
- **Timestamp naming** - `backup_2025-08-16_10-30-45.sql`
- **Retention policy** - Bewaar laatste 10 backups
- **Restore capability** - Mogelijkheid tot herstel

## 🚀 Technical Implementation

### Backend Components:

#### 1. Database Reset Service
```python
class DatabaseResetService:
    """Service for safely resetting database and importing fresh data."""
    
    @staticmethod
    def create_backup(backup_name=None):
        """Create database backup before reset."""
        if not backup_name:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            backup_name = f'backup_{timestamp}.sql'
        
        # PostgreSQL backup command
        backup_path = f'backups/{backup_name}'
        # Implementation: pg_dump command
        return backup_path
    
    @staticmethod
    def reset_tables(table_selection):
        """Reset selected database tables."""
        reset_operations = {
            'matches': 'DELETE FROM matches; ALTER SEQUENCE matches_id_seq RESTART WITH 1;',
            'players': 'DELETE FROM players; ALTER SEQUENCE players_id_seq RESTART WITH 1;',
            'availability': 'DELETE FROM player_availability;',
            'planning_versions': 'DELETE FROM planning_versions; ALTER SEQUENCE planning_versions_id_seq RESTART WITH 1;',
            'match_planning': 'DELETE FROM match_planning;'
        }
        
        # Execute selected reset operations
        # Implementation: Execute SQL with transaction safety
    
    @staticmethod
    def import_fresh_data(import_options):
        """Import fresh data from teambeheer.nl."""
        results = {}
        
        if import_options.get('matches'):
            results['matches'] = scraper.scrape_matches()
        
        if import_options.get('players'):
            results['players'] = scraper.scrape_players()
        
        return results
    
    @staticmethod
    def get_reset_summary():
        """Get current database state for confirmation."""
        return {
            'matches_count': Match.count_all(),
            'players_count': Player.count_all(),
            'availability_count': PlayerAvailability.count_all(),
            'planning_versions_count': PlanningVersion.count_all()
        }
```

#### 2. Reset Routes
```python
@admin.route('/database/reset', methods=['GET', 'POST'])
def database_reset():
    """Database reset interface."""
    if not current_user.is_admin():
        flash('Admin privileges required!', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Handle reset request with safety checks
        confirmation = request.form.get('confirmation')
        if confirmation != 'RESET':
            flash('Confirmation required!', 'error')
            return render_template('admin/database_reset.html')
        
        # Process reset
        table_selection = request.form.getlist('reset_tables')
        import_options = request.form.getlist('import_options')
        
        try:
            # Create backup
            backup_path = DatabaseResetService.create_backup()
            
            # Reset selected tables
            DatabaseResetService.reset_tables(table_selection)
            
            # Import fresh data
            import_results = DatabaseResetService.import_fresh_data(import_options)
            
            flash(f'Database reset successful! Backup created: {backup_path}', 'success')
            return render_template('admin/reset_success.html', results=import_results)
            
        except Exception as e:
            flash(f'Reset failed: {e}', 'error')
            return render_template('admin/database_reset.html')
    
    # Show reset form
    current_state = DatabaseResetService.get_reset_summary()
    return render_template('admin/database_reset.html', current_state=current_state)
```

### Frontend Interface:

#### 1. Reset Form Template
```html
<!-- admin/database_reset.html -->
<div class="container mt-4">
    <div class="row">
        <div class="col-md-8 mx-auto">
            <div class="card">
                <div class="card-header bg-warning text-dark">
                    <h4><i class="fas fa-exclamation-triangle"></i> Database Reset</h4>
                </div>
                <div class="card-body">
                    <!-- Warning Section -->
                    <div class="alert alert-danger">
                        <h5><i class="fas fa-skull-crossbones"></i> GEVAAR ZONE</h5>
                        <p>Deze actie verwijdert permanent geselecteerde data uit de database.</p>
                        <p><strong>Een backup wordt automatisch aangemaakt.</strong></p>
                    </div>
                    
                    <!-- Current State -->
                    <div class="alert alert-info">
                        <h6>Huidige Database Status:</h6>
                        <ul class="mb-0">
                            <li>Wedstrijden: {{ current_state.matches_count }}</li>
                            <li>Spelers: {{ current_state.players_count }}</li>
                            <li>Beschikbaarheid records: {{ current_state.availability_count }}</li>
                            <li>Planning versies: {{ current_state.planning_versions_count }}</li>
                        </ul>
                    </div>
                    
                    <!-- Reset Form -->
                    <form method="POST" id="resetForm">
                        <!-- Table Selection -->
                        <div class="mb-4">
                            <h6>Selecteer tabellen om te resetten:</h6>
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input" id="reset_matches" name="reset_tables" value="matches">
                                <label class="form-check-label" for="reset_matches">
                                    Wedstrijden ({{ current_state.matches_count }} records)
                                </label>
                            </div>
                            <!-- More checkboxes... -->
                        </div>
                        
                        <!-- Import Options -->
                        <div class="mb-4">
                            <h6>Auto-import opties:</h6>
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input" id="import_matches" name="import_options" value="matches" checked>
                                <label class="form-check-label" for="import_matches">
                                    Import wedstrijden van teambeheer.nl
                                </label>
                            </div>
                            <!-- More import options... -->
                        </div>
                        
                        <!-- Confirmation -->
                        <div class="mb-4">
                            <label for="confirmation" class="form-label">
                                <strong>Type 'RESET' om te bevestigen:</strong>
                            </label>
                            <input type="text" class="form-control" id="confirmation" name="confirmation" required>
                        </div>
                        
                        <!-- Action Buttons -->
                        <div class="d-flex gap-2">
                            <button type="button" class="btn btn-secondary" onclick="createBackup()">
                                <i class="fas fa-save"></i> Maak Backup
                            </button>
                            <a href="{{ url_for('admin.dashboard') }}" class="btn btn-outline-secondary">
                                Annuleren
                            </a>
                            <button type="submit" class="btn btn-danger" disabled id="resetBtn">
                                <i class="fas fa-redo"></i> RESET & IMPORT
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Enable reset button only when confirmation is correct
document.getElementById('confirmation').addEventListener('input', function() {
    const resetBtn = document.getElementById('resetBtn');
    resetBtn.disabled = this.value !== 'RESET';
});
</script>
```

## 🔄 Advanced Features

### Selective Reset Options:
- [ ] **Custom date ranges** - Reset alleen matches binnen bepaalde periode
- [ ] **Player subset reset** - Reset alleen specifieke spelers
- [ ] **Planning version cleanup** - Verwijder oude planning versies
- [ ] **Availability cleanup** - Reset alleen oude beschikbaarheid data

### Batch Operations:
- [ ] **Season rollover** - Automated new season setup
- [ ] **Team transfer** - Import players van ander team
- [ ] **Merge databases** - Combine data from multiple sources
- [ ] **Data validation** - Check data integrity after import

### Monitoring & Logging:
- [ ] **Reset history** - Log alle reset operaties
- [ ] **Performance metrics** - Track import speeds
- [ ] **Error reporting** - Detailed error logs
- [ ] **Admin notifications** - Email alerts voor resets

## 📊 Implementation Phases

### Phase 1: Basic Reset (3-4 hours)
- [ ] Create DatabaseResetService class
- [ ] Basic table reset functionality
- [ ] Simple confirmation interface
- [ ] Manual backup creation

### Phase 2: Safety & UX (3-4 hours)
- [ ] Automatic backup creation
- [ ] Multi-step confirmation process
- [ ] Current state display
- [ ] Error handling and rollback

### Phase 3: Import Integration (2-3 hours)
- [ ] Auto-import after reset
- [ ] Import progress indicators
- [ ] Import result reporting
- [ ] Selective import options

### Phase 4: Advanced Features (2-3 hours)
- [ ] Selective reset options
- [ ] Backup management interface
- [ ] Reset history logging
- [ ] Performance optimization

## 🎯 Success Criteria

### Functional Requirements:
- [ ] **Safe reset** - No accidental data loss
- [ ] **Automatic backup** - Always create backup before reset
- [ ] **Selective options** - Choose which tables to reset
- [ ] **Auto-import** - Fresh data import after reset
- [ ] **Error recovery** - Rollback capability on failure

### User Experience Requirements:
- [ ] **Clear warnings** - Users understand consequences
- [ ] **Progress feedback** - Show operation progress
- [ ] **Success confirmation** - Clear success/failure messages
- [ ] **Backup access** - Easy access to created backups

### Admin Requirements:
- [ ] **Audit trail** - Log all reset operations
- [ ] **Access control** - Only admin users can reset
- [ ] **Emergency recovery** - Quick restore from backup
- [ ] **Scheduled resets** - Optional automated resets

## 🔗 Dependencies
- **PostgreSQL database** - Backup and restore capabilities
- **Admin user system** - Access control
- **teambeheer.nl scraper** - For fresh data import
- **Current database models** - Match, Player, etc.

## 🏷️ Labels
- `enhancement`
- `admin-tools`
- `database`
- `data-management`
- `safety`

## 📊 Priority
**MEDIUM** - Very useful for development and maintenance, essential for production

## 💡 Additional Considerations

### Security Measures:
- **IP restrictions** - Limit reset capability to trusted IPs
- **Time delays** - Cooling-off period between resets
- **Email notifications** - Alert all admins of reset operations
- **Confirmation emails** - Email-based confirmation for resets

### Backup Management:
- **Automatic cleanup** - Remove old backups automatically
- **Backup verification** - Verify backup integrity
- **Restore testing** - Periodic restore tests
- **Cloud backup** - Optional cloud storage integration

---

**Estimated Total Effort:** 10-14 hours
**Business Impact:** High - Critical for development workflow and production maintenance
**User Benefit:** Enables easy fresh starts and safe data management
