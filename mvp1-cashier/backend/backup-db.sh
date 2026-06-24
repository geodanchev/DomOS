#!/bin/bash

################################################################################
# Database Backup Script for DomOS Cashier
# 
# Purpose: Create timestamped backups of the database
# Supports: SQLite (development) and PostgreSQL (production)
################################################################################

set -e  # Exit on error

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="domos_cashier_backup_${TIMESTAMP}"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Detect database type from DATABASE_URL
if [[ "$DATABASE_URL" == sqlite* ]] || [ -z "$DATABASE_URL" ]; then
    DB_TYPE="sqlite"
    DB_FILE="${DATABASE_URL#sqlite:///}"
    if [ -z "$DB_FILE" ]; then
        DB_FILE="./domos_cashier.db"
    fi
else
    DB_TYPE="postgresql"
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "========================================"
echo "DomOS Database Backup"
echo "========================================"
echo "Database Type: $DB_TYPE"
echo "Timestamp: $TIMESTAMP"
echo "Backup Directory: $BACKUP_DIR"
echo ""

if [ "$DB_TYPE" = "sqlite" ]; then
    # SQLite backup
    echo "Backing up SQLite database..."
    
    if [ ! -f "$DB_FILE" ]; then
        echo "Error: Database file not found: $DB_FILE"
        exit 1
    fi
    
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.db"
    cp "$DB_FILE" "$BACKUP_FILE"
    
    # Create compressed version
    gzip -c "$BACKUP_FILE" > "${BACKUP_FILE}.gz"
    
    echo "✓ Backup created: $BACKUP_FILE"
    echo "✓ Compressed: ${BACKUP_FILE}.gz"
    
    # Show backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    COMPRESSED_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo ""
    echo "Backup size: $BACKUP_SIZE"
    echo "Compressed size: $COMPRESSED_SIZE"
    
else
    # PostgreSQL backup
    echo "Backing up PostgreSQL database..."
    
    # Parse DATABASE_URL: postgresql://user:pass@host:port/dbname
    if [[ "$DATABASE_URL" =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
        PGUSER="${BASH_REMATCH[1]}"
        PGPASSWORD="${BASH_REMATCH[2]}"
        PGHOST="${BASH_REMATCH[3]}"
        PGPORT="${BASH_REMATCH[4]}"
        PGDATABASE="${BASH_REMATCH[5]}"
    else
        echo "Error: Could not parse DATABASE_URL"
        exit 1
    fi
    
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.backup"
    
    # Use pg_dump with custom format (allows selective restore)
    export PGPASSWORD
    pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
        -Fc -f "$BACKUP_FILE" --verbose
    
    # Also create SQL format for inspection
    SQL_BACKUP="${BACKUP_DIR}/${BACKUP_NAME}.sql"
    pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
        -f "$SQL_BACKUP" --verbose
    gzip "$SQL_BACKUP"
    
    echo "✓ Backup created: $BACKUP_FILE (custom format)"
    echo "✓ SQL backup: ${SQL_BACKUP}.gz"
    
    # Show backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    SQL_SIZE=$(du -h "${SQL_BACKUP}.gz" | cut -f1)
    echo ""
    echo "Custom backup size: $BACKUP_SIZE"
    echo "SQL backup size: $SQL_SIZE"
fi

echo ""
echo "========================================"
echo "Backup completed successfully!"
echo "========================================"

# List recent backups
echo ""
echo "Recent backups:"
ls -lth "$BACKUP_DIR" | head -n 6

# Cleanup old backups (keep last 10)
echo ""
echo "Cleaning up old backups (keeping last 10)..."
if [ "$DB_TYPE" = "sqlite" ]; then
    ls -t "${BACKUP_DIR}"/*.db 2>/dev/null | tail -n +11 | xargs -r rm
    ls -t "${BACKUP_DIR}"/*.db.gz 2>/dev/null | tail -n +11 | xargs -r rm
else
    ls -t "${BACKUP_DIR}"/*.backup 2>/dev/null | tail -n +11 | xargs -r rm
    ls -t "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm
fi

echo "✓ Cleanup completed"
