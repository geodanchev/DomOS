#!/usr/bin/env python3
"""
DomOS Database Management - Safe Operations Helper

Този модул предоставя безопасни функции за CRUD операции в DomOS базата данни.
Всички destructive операции автоматично създават backup и логват промените.

Използване:
    from safe_operations import DomOSDatabase
    
    db = DomOSDatabase()
    db.connect()
    
    # Dry-run режим (preview без промени)
    db.safe_update('apartments', {'monthly_fee': 30}, 'id = 1', dry_run=True)
    
    # Реално изпълнение с автоматичен backup
    db.safe_update('apartments', {'monthly_fee': 30}, 'id = 1')
    
    db.close()

Environment Variables:
    DOMOS_DB_PASSWORD - парола за базата данни
    DOMOS_DB_HOST - host (default: localhost за Cloud SQL Proxy)
    DOMOS_DB_PORT - port (default: 5432)
    DOMOS_DB_NAME - database name (default: domos)
    DOMOS_DB_USER - database user (default: domos_user)
"""

import os
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("WARNING: psycopg2 not installed. Run: pip install psycopg2-binary")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('domos_db')

# FK Dependencies map - кои таблици зависят от кои
FK_DEPENDENCIES = {
    'apartments': ['obligations', 'payments', 'apartment_accounts', 'audit_logs'],
    'users': ['payments', 'receipts', 'expenses', 'audit_logs'],
    'apartment_accounts': ['account_transactions'],
    'payments': ['receipts'],
    'obligations': [],
    'receipts': [],
    'expenses': [],
    'account_transactions': [],
    'audit_logs': [],
}

# FK Reference columns - коя колона в child таблицата сочи към parent
FK_REFERENCE_COLUMNS = {
    ('apartments', 'obligations'): 'apartment_id',
    ('apartments', 'payments'): 'apartment_id',
    ('apartments', 'apartment_accounts'): 'apartment_id',
    ('apartments', 'audit_logs'): 'apartment_id',
    ('users', 'payments'): 'collected_by_id',
    ('users', 'receipts'): 'issued_by_id',
    ('users', 'expenses'): 'created_by',
    ('users', 'audit_logs'): 'user_id',
    ('apartment_accounts', 'account_transactions'): 'account_id',
    ('payments', 'receipts'): 'payment_id',
}


class DomOSDatabase:
    """Клас за безопасна работа с DomOS базата данни."""
    
    def __init__(self):
        """Инициализация на database helper."""
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
        
        self.conn = None
        self.host = os.environ.get('DOMOS_DB_HOST', 'localhost')
        self.port = int(os.environ.get('DOMOS_DB_PORT', 5432))
        self.database = os.environ.get('DOMOS_DB_NAME', 'domos')
        self.user = os.environ.get('DOMOS_DB_USER', 'domos_user')
        self.password = os.environ.get('DOMOS_DB_PASSWORD')
        
        if not self.password:
            raise ValueError(
                "DOMOS_DB_PASSWORD environment variable is required.\n"
                "Set it with: export DOMOS_DB_PASSWORD='your_password'"
            )
    
    def connect(self, unix_socket: Optional[str] = None) -> None:
        """
        Свързване към базата данни.
        
        Args:
            unix_socket: Unix socket path за Cloud Run (optional)
                        Example: /cloudsql/bionic-region-502615-h8:europe-west3:domos-db
        """
        try:
            if unix_socket:
                # Cloud Run connection via Unix socket
                self.conn = psycopg2.connect(
                    host=unix_socket,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                logger.info(f"Connected to {self.database} via Unix socket")
            else:
                # Cloud SQL Proxy or direct connection
                self.conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
                logger.info(f"Connected to {self.database} at {self.host}:{self.port}")
        except psycopg2.Error as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    def close(self) -> None:
        """Затваряне на връзката."""
        if self.conn:
            self.conn.close()
            logger.info("Connection closed")
    
    @contextmanager
    def transaction(self):
        """
        Context manager за транзакции.
        
        Usage:
            with db.transaction():
                db.execute("UPDATE ...")
                db.execute("INSERT ...")
            # автоматичен COMMIT при успех, ROLLBACK при грешка
        """
        try:
            yield
            self.conn.commit()
            logger.info("Transaction committed")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
    
    def execute(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch: bool = False
    ) -> Optional[List[Dict]]:
        """
        Изпълнение на SQL заявка.
        
        Args:
            query: SQL заявка
            params: параметри за заявката (tuple)
            fetch: дали да върне резултати
            
        Returns:
            List[Dict] ако fetch=True, иначе None
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                return [dict(row) for row in cur.fetchall()]
            return None
    
    # ========================
    # BACKUP FUNCTIONS
    # ========================
    
    def backup_table(self, table: str, suffix: Optional[str] = None) -> str:
        """
        Създаване на backup на цяла таблица.
        
        Args:
            table: име на таблицата
            suffix: suffix за backup таблицата (default: timestamp)
            
        Returns:
            име на backup таблицата
        """
        if suffix is None:
            suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backup_table = f"{table}_backup_{suffix}"
        
        with self.transaction():
            # Провери дали backup таблицата вече съществува
            exists = self.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                (backup_table,),
                fetch=True
            )[0]['exists']
            
            if exists:
                logger.warning(f"Backup table {backup_table} already exists, skipping")
                return backup_table
            
            self.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {table}")
            
            count = self.execute(f"SELECT COUNT(*) as cnt FROM {backup_table}", fetch=True)[0]['cnt']
            logger.info(f"Created backup {backup_table} with {count} rows")
        
        return backup_table
    
    def backup_rows(
        self, 
        table: str, 
        where_clause: str, 
        params: Optional[Tuple] = None
    ) -> List[Dict]:
        """
        Backup на конкретни редове (връща ги като list of dicts).
        
        Args:
            table: име на таблицата
            where_clause: WHERE условие (без WHERE keyword)
            params: параметри за WHERE условието
            
        Returns:
            List[Dict] с backup-натите редове
        """
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        rows = self.execute(query, params, fetch=True)
        logger.info(f"Backed up {len(rows)} rows from {table}")
        return rows
    
    # ========================
    # FK CONSTRAINT CHECKS
    # ========================
    
    def check_fk_dependencies(
        self, 
        table: str, 
        record_id: int
    ) -> Dict[str, int]:
        """
        Проверка за FK зависимости преди delete.
        
        Args:
            table: име на parent таблицата
            record_id: ID на записа за изтриване
            
        Returns:
            Dict с броя зависими записи per таблица
        """
        dependencies = {}
        
        for child_table in FK_DEPENDENCIES.get(table, []):
            fk_column = FK_REFERENCE_COLUMNS.get((table, child_table))
            if fk_column:
                count = self.execute(
                    f"SELECT COUNT(*) as cnt FROM {child_table} WHERE {fk_column} = %s",
                    (record_id,),
                    fetch=True
                )[0]['cnt']
                if count > 0:
                    dependencies[child_table] = count
        
        return dependencies
    
    def can_delete(self, table: str, record_id: int) -> Tuple[bool, Dict[str, int]]:
        """
        Проверка дали записът може да бъде изтрит безопасно.
        
        Args:
            table: име на таблицата
            record_id: ID на записа
            
        Returns:
            (can_delete: bool, dependencies: Dict)
        """
        deps = self.check_fk_dependencies(table, record_id)
        return (len(deps) == 0, deps)
    
    # ========================
    # SAFE CRUD OPERATIONS
    # ========================
    
    def safe_update(
        self,
        table: str,
        updates: Dict[str, Any],
        where_clause: str,
        where_params: Optional[Tuple] = None,
        dry_run: bool = False,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Безопасен UPDATE с backup и dry-run режим.
        
        Args:
            table: име на таблицата
            updates: Dict с колони и нови стойности
            where_clause: WHERE условие (без WHERE keyword)
            where_params: параметри за WHERE условието
            dry_run: ако True, само показва какво ще се промени
            create_backup: дали да създаде backup (default: True)
            
        Returns:
            Dict с информация за операцията
        """
        # 1. Намери засегнатите редове
        select_query = f"SELECT * FROM {table} WHERE {where_clause}"
        affected_rows = self.execute(select_query, where_params, fetch=True)
        
        result = {
            'table': table,
            'operation': 'UPDATE',
            'affected_count': len(affected_rows),
            'before': affected_rows,
            'updates': updates,
            'dry_run': dry_run
        }
        
        if dry_run:
            logger.info(f"DRY RUN: Would update {len(affected_rows)} rows in {table}")
            logger.info(f"DRY RUN: Changes: {updates}")
            return result
        
        if len(affected_rows) == 0:
            logger.warning(f"No rows match condition: {where_clause}")
            return result
        
        # 2. Backup ако е нужен
        if create_backup:
            backup_data = self.backup_rows(table, where_clause, where_params)
            result['backup'] = backup_data
        
        # 3. Изпълни UPDATE
        set_clauses = [f"{col} = %s" for col in updates.keys()]
        set_clause = ", ".join(set_clauses)
        
        # Добави updated_at ако колоната съществува
        if self._column_exists(table, 'updated_at'):
            set_clause += ", updated_at = NOW()"
        
        update_params = tuple(updates.values())
        if where_params:
            update_params += where_params
        
        with self.transaction():
            update_query = f"UPDATE {table} SET {set_clause} WHERE {where_clause} RETURNING *"
            updated = self.execute(update_query, update_params, fetch=True)
            result['after'] = updated
        
        # 4. Log в audit_logs
        self._log_audit(
            action='SAFE_UPDATE',
            entity_type=table,
            entity_id=affected_rows[0].get('id') if affected_rows else None,
            description=f"Updated {len(updated)} rows in {table}",
            state_before=affected_rows,
            state_after=updated
        )
        
        logger.info(f"Updated {len(updated)} rows in {table}")
        return result
    
    def safe_delete(
        self,
        table: str,
        where_clause: str,
        where_params: Optional[Tuple] = None,
        dry_run: bool = False,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Безопасен DELETE с FK проверка, backup и dry-run режим.
        
        Args:
            table: име на таблицата
            where_clause: WHERE условие (без WHERE keyword)
            where_params: параметри за WHERE условието
            dry_run: ако True, само показва какво ще се изтрие
            force: ако True, игнорира FK зависимости (ОПАСНО!)
            
        Returns:
            Dict с информация за операцията
        """
        # 1. Намери засегнатите редове
        select_query = f"SELECT * FROM {table} WHERE {where_clause}"
        affected_rows = self.execute(select_query, where_params, fetch=True)
        
        result = {
            'table': table,
            'operation': 'DELETE',
            'affected_count': len(affected_rows),
            'rows': affected_rows,
            'dry_run': dry_run
        }
        
        if len(affected_rows) == 0:
            logger.warning(f"No rows match condition: {where_clause}")
            return result
        
        # 2. Провери FK зависимости
        all_dependencies = {}
        for row in affected_rows:
            record_id = row.get('id')
            if record_id:
                deps = self.check_fk_dependencies(table, record_id)
                if deps:
                    all_dependencies[record_id] = deps
        
        if all_dependencies:
            result['dependencies'] = all_dependencies
            if not force:
                logger.error(f"Cannot delete: FK dependencies exist: {all_dependencies}")
                result['error'] = 'FK dependencies exist. Use force=True to override (DANGEROUS!)'
                return result
            else:
                logger.warning(f"FORCE DELETE: Ignoring FK dependencies: {all_dependencies}")
        
        if dry_run:
            logger.info(f"DRY RUN: Would delete {len(affected_rows)} rows from {table}")
            return result
        
        # 3. Backup
        backup_data = self.backup_rows(table, where_clause, where_params)
        result['backup'] = backup_data
        
        # 4. Изпълни DELETE
        with self.transaction():
            delete_query = f"DELETE FROM {table} WHERE {where_clause} RETURNING *"
            deleted = self.execute(delete_query, where_params, fetch=True)
            result['deleted'] = deleted
        
        # 5. Log в audit_logs
        self._log_audit(
            action='SAFE_DELETE',
            entity_type=table,
            entity_id=affected_rows[0].get('id') if affected_rows else None,
            description=f"Deleted {len(deleted)} rows from {table}",
            state_before=affected_rows,
            state_after=None
        )
        
        logger.info(f"Deleted {len(deleted)} rows from {table}")
        return result
    
    def safe_insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Безопасен INSERT с dry-run режим.
        
        Args:
            table: име на таблицата
            data: Dict или List[Dict] с данни за вмъкване
            dry_run: ако True, само показва какво ще се вмъкне
            
        Returns:
            Dict с информация за операцията
        """
        if isinstance(data, dict):
            data = [data]
        
        result = {
            'table': table,
            'operation': 'INSERT',
            'rows_to_insert': len(data),
            'data': data,
            'dry_run': dry_run
        }
        
        if dry_run:
            logger.info(f"DRY RUN: Would insert {len(data)} rows into {table}")
            return result
        
        # Добави timestamps ако колоните съществуват
        has_created_at = self._column_exists(table, 'created_at')
        has_updated_at = self._column_exists(table, 'updated_at')
        
        inserted_rows = []
        with self.transaction():
            for row in data:
                if has_created_at and 'created_at' not in row:
                    row['created_at'] = datetime.now()
                if has_updated_at and 'updated_at' not in row:
                    row['updated_at'] = datetime.now()
                
                columns = list(row.keys())
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                
                insert_query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) RETURNING *"
                inserted = self.execute(insert_query, tuple(row.values()), fetch=True)
                inserted_rows.extend(inserted)
        
        result['inserted'] = inserted_rows
        
        # Log в audit_logs
        self._log_audit(
            action='SAFE_INSERT',
            entity_type=table,
            entity_id=inserted_rows[0].get('id') if inserted_rows else None,
            description=f"Inserted {len(inserted_rows)} rows into {table}",
            state_before=None,
            state_after=inserted_rows
        )
        
        logger.info(f"Inserted {len(inserted_rows)} rows into {table}")
        return result
    
    # ========================
    # HELPER METHODS
    # ========================
    
    def _column_exists(self, table: str, column: str) -> bool:
        """Проверка дали колона съществува в таблица."""
        result = self.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            )
            """,
            (table, column),
            fetch=True
        )
        return result[0]['exists']
    
    def _log_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[int],
        description: str,
        state_before: Optional[Any] = None,
        state_after: Optional[Any] = None,
        user_email: str = 'system@domos.bg'
    ) -> None:
        """
        Записване в audit_logs таблицата.
        
        Args:
            action: тип на действието
            entity_type: тип на entity (таблица)
            entity_id: ID на entity
            description: описание
            state_before: състояние преди
            state_after: състояние след
            user_email: email на user (default: system)
        """
        try:
            # Сериализирай state обектите
            def serialize(obj):
                if obj is None:
                    return None
                if isinstance(obj, list):
                    return json.dumps([self._serialize_row(r) for r in obj], default=str, ensure_ascii=False)
                return json.dumps(self._serialize_row(obj), default=str, ensure_ascii=False)
            
            self.execute(
                """
                INSERT INTO audit_logs (
                    timestamp, action, user_email, entity_type, entity_id,
                    description, state_before, state_after, is_critical
                ) VALUES (
                    NOW(), %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s
                )
                """,
                (
                    action,
                    user_email,
                    entity_type,
                    entity_id,
                    description,
                    serialize(state_before),
                    serialize(state_after),
                    True  # всички safe operations са критични
                )
            )
            self.conn.commit()
        except Exception as e:
            logger.warning(f"Failed to log audit: {e}")
            # Don't fail the main operation if audit logging fails
    
    def _serialize_row(self, row: Dict) -> Dict:
        """Сериализиране на ред за JSON (handle datetime и Decimal)."""
        from decimal import Decimal
        result = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = float(value)
            else:
                result[key] = value
        return result
    
    # ========================
    # UTILITY METHODS
    # ========================
    
    def get_table_stats(self) -> Dict[str, int]:
        """Връща брой записи във всички таблици."""
        tables = [
            'apartments', 'users', 'apartment_accounts', 'obligations',
            'payments', 'account_transactions', 'receipts', 'expenses', 'audit_logs'
        ]
        stats = {}
        for table in tables:
            try:
                count = self.execute(f"SELECT COUNT(*) as cnt FROM {table}", fetch=True)[0]['cnt']
                stats[table] = count
            except Exception:
                stats[table] = -1  # таблицата не съществува
        return stats
    
    def verify_connection(self) -> bool:
        """Проверка на връзката към базата."""
        try:
            result = self.execute("SELECT 1 as test", fetch=True)
            return result[0]['test'] == 1
        except Exception:
            return False


# ========================
# CLI INTERFACE
# ========================

def main():
    """Command-line interface за safe operations."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='DomOS Database Safe Operations Helper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примери:
  # Тест на връзката
  python safe_operations.py --test
  
  # Статистика на таблиците
  python safe_operations.py --stats
  
  # Backup на таблица
  python safe_operations.py --backup apartments
  
  # Dry-run update
  python safe_operations.py --update apartments --set monthly_fee=30 --where "id=1" --dry-run
  
  # FK dependency check
  python safe_operations.py --check-deps apartments 1
        """
    )
    
    parser.add_argument('--test', action='store_true', help='Тест на връзката')
    parser.add_argument('--stats', action='store_true', help='Статистика на таблиците')
    parser.add_argument('--backup', metavar='TABLE', help='Backup на таблица')
    parser.add_argument('--check-deps', nargs=2, metavar=('TABLE', 'ID'), help='Провери FK зависимости')
    parser.add_argument('--dry-run', action='store_true', help='Само preview без промени')
    
    args = parser.parse_args()
    
    try:
        db = DomOSDatabase()
        db.connect()
        
        if args.test:
            if db.verify_connection():
                print("✓ Връзката работи успешно")
            else:
                print("✗ Връзката не работи")
                return 1
        
        elif args.stats:
            stats = db.get_table_stats()
            print("\n=== Статистика на таблиците ===")
            for table, count in stats.items():
                status = count if count >= 0 else "N/A"
                print(f"  {table}: {status}")
        
        elif args.backup:
            backup_name = db.backup_table(args.backup)
            print(f"✓ Създаден backup: {backup_name}")
        
        elif args.check_deps:
            table, record_id = args.check_deps
            can_del, deps = db.can_delete(table, int(record_id))
            if can_del:
                print(f"✓ Записът може да бъде изтрит безопасно")
            else:
                print(f"✗ Записът има FK зависимости:")
                for dep_table, count in deps.items():
                    print(f"  - {dep_table}: {count} записа")
        
        else:
            parser.print_help()
        
        db.close()
        return 0
        
    except Exception as e:
        print(f"Грешка: {e}")
        return 1


if __name__ == '__main__':
    exit(main())