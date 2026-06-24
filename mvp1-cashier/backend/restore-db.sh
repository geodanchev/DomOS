#!/bin/bash

################################################################################
# Database Restore Script for DomOS Cashier
# 
# Purpose: Restore database from timestamped backups
# Supports: SQLite (development) and PostgreSQL (production)
################################################################################

set -e  # Exit on error

# Configuration
BACKUP_DIR="./backups"

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

echo "========================================"
echo "DomOS Database Restore"
echo "========================================"
echo "Database Type: $DB_TYPE"
echo ""

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory not found: $BACKUP_DIR"
    echo "Please create a backup first using backup-db.sh"
    exit 1
fi

# List available backups
echo "Available backups:"
echo ""

if [ "$DB_TYPE" = "sqlite" ]; then
    BACKUPS=($(ls -t "${BACKUP_DIR}"/*.db 2>/dev/null || echo ""))
else
    BACKUPS=($(ls -t "${BACKUP_DIR}"/*.backup 2>/dev/null || echo ""))
fi

if [ ${#BACKUPS[@]} -eq 0 ]; then
    echo "No backups found in $BACKUP_DIR"
    exit 1
fi

# Display backups with numbers
for i in "${!BACKUPS[@]}"; do
    BACKUP_FILE="${BACKUPS[$i]}"
    BACKUP_NAME=$(basename "$BACKUP_FILE")
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    BACKUP_DATE=$(stat -c %y "$BACKUP_FILE" 2>/dev/null || stat -f %Sm "$BACKUP_FILE" 2>/dev/null || echo "unknown")
    printf "%2d. %-60s %8s  %s\n" $((i+1)) "$BACKUP_NAME" "$BACKUP_SIZE" "${BACKUP_DATE:0:19}"
done

echo ""

# Get backup selection
if [ -n "$1" ]; then
    # Backup file provided as argument
    if [ -f "$1" ]; then
        SELECTED_BACKUP="$1"
    elif [ -f "${BACKUP_DIR}/$1" ]; then
        SELECTED_BACKUP="${BACKUP_DIR}/$1"
    else
        echo "Error: Backup file not found: $1"
        exit 1
    fi
else
    # Interactive selection
    read -p "Select backup number to restore (1-${#BACKUPS[@]}): " BACKUP_NUM
    
    if ! [[ "$BACKUP_NUM" =~ ^[0-9]+$ ]] || [ "$BACKUP_NUM" -lt 1 ] || [ "$BACKUP_NUM" -gt ${#BACKUPS[@]} ]; then
        echo "Error: Invalid selection"
        exit 1
    fi
    
    SELECTED_BACKUP="${BACKUPS[$((BACKUP_NUM-1))]}"
fi

echo ""
echo "Selected backup: $(basename "$SELECTED_BACKUP")"
echo ""

# Safety confirmation
echo "⚠️  WARNING: This will REPLACE the current database!"
echo "⚠️  All current data will be LOST!"
echo ""
read -p "Are you sure you want to continue? Type 'YES' to confirm: " CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "Creating safety backup of current database before restore..."

# Create safety backup before restore
SAFETY_BACKUP_NAME="before_restore_$(date +"%Y%m%d_%H%M%S")"

if [ "$DB_TYPE" = "sqlite" ]; then
    if [ -f "$DB_FILE" ]; then
        SAFETY_FILE="${BACKUP_DIR}/${SAFETY_BACKUP_NAME}.db"
        cp "$DB_FILE" "$SAFETY_FILE"
        echo "✓ Safety backup created: $SAFETY_FILE"
    fi
else
    # Parse DATABASE_URL for PostgreSQL
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
    
    SAFETY_FILE="${BACKUP_DIR}/${SAFETY_BACKUP_NAME}.backup"
    export PGPASSWORD
    pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
        -Fc -f "$SAFETY_FILE" 2>/dev/null
    echo "✓ Safety backup created: $SAFETY_FILE"
fi

echo ""
echo "========================================"
echo "Restoring database..."
echo "========================================"
echo ""

if [ "$DB_TYPE" = "sqlite" ]; then
    # SQLite restore
    echo "Restoring SQLite database from: $(basename "$SELECTED_BACKUP")"
    
    # Handle compressed backups
    if [[ "$SELECTED_BACKUP" == *.gz ]]; then
        gunzip -c "$SELECTED_BACKUP" > "$DB_FILE"
    else
        cp "$SELECTED_BACKUP" "$DB_FILE"
    fi
    
    echo "✓ SQLite database restored successfully"
    
else
    # PostgreSQL restore
    echo "Restoring PostgreSQL database from: $(basename "$SELECTED_BACKUP")"
    
    export PGPASSWORD
    
    # Drop and recreate database is risky, use --clean instead
    pg_restore -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
        --clean --if-exists -v "$SELECTED_BACKUP" 2>&1 | grep -v "WARNING"
    
    echo "✓ PostgreSQL database restored successfully"
fi

echo ""
echo "========================================"
echo "Restore completed successfully!"
echo "========================================"
echo ""
echo "Restored from: $(basename "$SELECTED_BACKUP")"
echo "Safety backup: $(basename "$SAFETY_FILE")"
echo ""
echo "If something went wrong, you can restore from the safety backup:"
echo "  ./restore-db.sh \"$SAFETY_FILE\""
echo ""
