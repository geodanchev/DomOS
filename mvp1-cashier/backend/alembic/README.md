# Alembic Database Migrations - DomOS Cashier

## Overview

This directory contains Alembic database migrations for the DomOS Cashier application. Alembic is a lightweight database migration tool for usage with SQLAlchemy.

## Quick Start

### Creating a New Migration

```bash
# Use the helper script (recommended)
./create-migration.sh "description of changes"

# Or use alembic directly
alembic revision --autogenerate -m "description"
```

### Applying Migrations

```bash
# Upgrade to the latest version
alembic upgrade head

# Preview SQL without executing
alembic upgrade head --sql

# Upgrade by one version
alembic upgrade +1
```

### Rollback Migrations

```bash
# Downgrade by one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade c6068e1a480f

# Downgrade to base (empty database)
alembic downgrade base
```

## Helper Scripts

### `create-migration.sh`

Simplified migration creation with automatic validation and backup.

**Usage:**
```bash
./create-migration.sh "add user roles"
./create-migration.sh "create receipts table"
./create-migration.sh "add payment void column"
```

**Features:**
- Validates migration description
- Checks model imports before generation
- Creates automatic backup before migration
- Shows migration preview
- Displays next steps and rollback instructions

### `backup-db.sh`

Create timestamped database backups.

**Usage:**
```bash
./backup-db.sh
```

**Features:**
- Supports both SQLite (dev) and PostgreSQL (prod)
- Creates timestamped backups
- Automatic compression (gzip for SQLite, custom format for PostgreSQL)
- Keeps last 10 backups automatically
- Shows backup sizes

**Output:**
- SQLite: `backups/domos_cashier_backup_YYYYMMDD_HHMMSS.db[.gz]`
- PostgreSQL: `backups/domos_cashier_backup_YYYYMMDD_HHMMSS.backup` (custom format)
- PostgreSQL: `backups/domos_cashier_backup_YYYYMMDD_HHMMSS.sql.gz` (SQL format for inspection)

### `restore-db.sh`

Restore database from timestamped backups with safety checks.

**Usage:**
```bash
# Interactive mode (lists available backups)
./restore-db.sh

# Direct restore from specific file
./restore-db.sh backups/domos_cashier_backup_20260624_120000.db
```

**Safety Features:**
- Lists all available backups with timestamps and sizes
- Requires explicit "YES" confirmation
- Creates safety backup before restore
- Provides rollback instructions if restore fails

## Common Workflows

### Development Workflow

1. **Make model changes:**
   ```python
   # app/models/user.py
   class User(Base):
       __tablename__ = "users"
       # ... add new column
       phone = Column(String(20), nullable=True)
   ```

2. **Create migration:**
   ```bash
   ./create-migration.sh "add user phone column"
   ```

3. **Review generated migration:**
   ```bash
   # Check the generated file in alembic/versions/
   # Edit if needed (add custom logic, data migrations, etc.)
   ```

4. **Test migration (dry-run):**
   ```bash
   alembic upgrade head --sql > migration.sql
   cat migration.sql  # Review SQL
   ```

5. **Apply migration:**
   ```bash
   alembic upgrade head
   ```

6. **Verify database:**
   ```bash
   # Check table structure
   psql -d domos_cashier -c "\d users"
   ```

### Production Deployment Workflow

1. **Create backup before deployment:**
   ```bash
   ./backup-db.sh
   ```

2. **Test migrations in staging environment:**
   ```bash
   # On staging server
   alembic upgrade head --sql > migration.sql
   cat migration.sql  # Review carefully
   alembic upgrade head
   ```

3. **Apply to production:**
   ```bash
   # On production server
   ./backup-db.sh  # Create fresh backup
   alembic upgrade head
   ```

4. **Verify application:**
   ```bash
   # Check application logs
   # Run smoke tests
   # Monitor error rates
   ```

5. **Rollback if needed:**
   ```bash
   alembic downgrade -1
   # Or restore from backup:
   ./restore-db.sh
   ```

### Data Migration Workflow

When migrations involve data transformations:

1. **Create empty migration:**
   ```bash
   alembic revision -m "migrate payment data"
   ```

2. **Edit migration file manually:**
   ```python
   # alembic/versions/XXXXXX_migrate_payment_data.py
   
   def upgrade():
       # Schema changes first
       op.add_column('payments', sa.Column('new_field', sa.String(100)))
       
       # Data migration
       connection = op.get_bind()
       connection.execute("""
           UPDATE payments 
           SET new_field = old_field || '_migrated'
           WHERE old_field IS NOT NULL
       """)
       
       # Drop old column if needed
       op.drop_column('payments', 'old_field')
   
   def downgrade():
       # Reverse operations
       op.add_column('payments', sa.Column('old_field', sa.String(100)))
       connection = op.get_bind()
       connection.execute("""
           UPDATE payments 
           SET old_field = REPLACE(new_field, '_migrated', '')
           WHERE new_field IS NOT NULL
       """)
       op.drop_column('payments', 'new_field')
   ```

3. **Test thoroughly:**
   ```bash
   # Test upgrade
   alembic upgrade head
   
   # Verify data
   psql -d domos_cashier -c "SELECT * FROM payments LIMIT 10;"
   
   # Test downgrade
   alembic downgrade -1
   
   # Verify rollback worked
   psql -d domos_cashier -c "SELECT * FROM payments LIMIT 10;"
   ```

## Migration History

### View Migration History

```bash
# List all migrations
alembic history

# Verbose output with details
alembic history --verbose

# Show current version
alembic current

# Show specific revision details
alembic show c6068e1a480f
```

### Existing Migrations

Current migration chain (oldest to newest):

1. **c6068e1a480f** - Add obligations table (2026-06-21 20:38:19)
   - Created `obligations` table
   - Linked to apartments and users

2. **e6a58feb3c22** - Account-based system (2026-06-21 21:17:25)
   - Created `apartment_accounts` table
   - Created `account_transactions` table
   - Implemented double-entry accounting

3. **a1b2c3d4e5f6** - Add expenses table (2026-06-24 10:04:00)
   - Created `expenses` table
   - Added expense tracking functionality

4. **f7g8h9i0j1k2** - Add payment void and audit log (2026-06-24 10:08:00)
   - Added `is_voided` flag to payments
   - Created `audit_logs` table
   - Implemented audit trail system

## Troubleshooting

### Issue: "Target database is not up to date"

**Solution:**
```bash
alembic upgrade head
```

### Issue: "Can't locate revision identified by 'XXXXX'"

**Cause:** Migration file was deleted or revision ID mismatch.

**Solution:**
```bash
# Check migration history
alembic history

# If migration is missing, recreate it or restore from backup
```

### Issue: "relation 'table_name' already exists"

**Cause:** Tables exist but migrations not tracked.

**Solution:**
```bash
# Mark current state as up-to-date without executing migrations
alembic stamp head
```

### Issue: "FAILED: Can't locate revision identified by 'XXXXX'"

**Cause:** Broken migration chain (duplicate revision IDs).

**Solution:**
1. Find duplicate revisions:
   ```bash
   grep -r "revision = " alembic/versions/
   ```

2. Fix duplicate revision IDs in migration files

3. Verify chain:
   ```bash
   alembic history
   ```

### Issue: Migration fails with constraint error

**Solution:**
```bash
# Rollback failed migration
alembic downgrade -1

# Fix migration script
# Add data cleanup or adjust constraints

# Retry
alembic upgrade head
```

### Issue: Database locked (SQLite)

**Solution:**
```bash
# Stop all processes using the database
pkill -f uvicorn

# Remove lock file if exists
rm -f domos_cashier.db-shm domos_cashier.db-wal

# Retry migration
alembic upgrade head
```

## Best Practices

### 1. Always Create Backups

```bash
# Before any migration
./backup-db.sh

# Before production deployment
./backup-db.sh
```

### 2. Test Migrations Thoroughly

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

### 3. Review Generated Migrations

Autogenerate is helpful but not perfect:

- **Always review** generated migration files
- **Add custom logic** for data migrations
- **Test edge cases** with real data
- **Document complex migrations** with comments

### 4. Use Descriptive Migration Messages

```bash
# Good:
./create-migration.sh "add user phone column"
./create-migration.sh "create receipts table with foreign keys"

# Bad:
./create-migration.sh "update"
./create-migration.sh "fix"
```

### 5. Never Edit Applied Migrations

Once a migration is applied:
- **Do not** edit the migration file
- **Do not** change revision IDs
- **Create a new migration** for fixes

### 6. Keep Migrations Small and Focused

```bash
# Good (separate concerns):
./create-migration.sh "add user roles"
./create-migration.sh "migrate existing users to default role"

# Bad (too much in one migration):
./create-migration.sh "add user roles and migrate data and update permissions"
```

### 7. Document Complex Migrations

Add comments to complex migration files:

```python
def upgrade():
    """
    Migration: Add payment refund workflow
    
    Changes:
    1. Add is_refund boolean column to payments
    2. Add refund_of_payment_id foreign key
    3. Create index on refund_of_payment_id
    4. Update existing refunds (payment_method='REFUND') to use new structure
    
    Data Migration:
    - Find all payments with payment_method='REFUND'
    - Link them to original payment via description parsing
    - Update is_refund flag
    """
    # ... implementation
```

### 8. Use Transactions for Data Migrations

```python
def upgrade():
    connection = op.get_bind()
    
    # Start transaction (PostgreSQL)
    with connection.begin():
        # Schema changes
        op.add_column('payments', sa.Column('status', sa.String(20)))
        
        # Data migration
        connection.execute("""
            UPDATE payments 
            SET status = 'completed'
            WHERE payment_date IS NOT NULL
        """)
        
        connection.execute("""
            UPDATE payments 
            SET status = 'pending'
            WHERE payment_date IS NULL
        """)
```

## Docker Environment

### Running Migrations in Docker

```bash
# Execute migration inside container
docker compose exec backend alembic upgrade head

# Create backup inside container
docker compose exec backend ./backup-db.sh

# Create new migration inside container
docker compose exec backend ./create-migration.sh "description"
```

### Database URL Configuration

The `alembic/env.py` is configured to use `DATABASE_URL` environment variable:

```python
# Override sqlalchemy.url with DATABASE_URL from environment if available
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
```

This allows:
- **Development**: `sqlite:///./domos_cashier.db` (from .env)
- **Docker**: `postgresql://postgres:postgres@db:5432/domos_cashier` (from docker-compose)
- **Production**: Full PostgreSQL URL (from environment)

## Configuration Files

### `alembic.ini`

Main Alembic configuration file:
- **script_location**: `alembic` (migration scripts directory)
- **file_template**: Timestamp-based naming: `YYYYMMDD_HHMMSS_revision_slug`
- **sqlalchemy.url**: Default database URL (can be overridden by environment variable)

### `alembic/env.py`

Alembic environment configuration:
- **Imports**: All models from `app.models`
- **target