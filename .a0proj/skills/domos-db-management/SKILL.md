# DomOS Database Management Skill

## Trigger Phrases
- управление на базата данни
- директен достъп до базата
- Cloud SQL манипулация
- добави данни в базата
- изтрий от базата
- update в базата
- backup на базата
- restore база данни
- CRUD операции база
- директно SQL изпълнение
- database management
- direct database access
- run SQL query
- backup database
- restore database

## Описание

Този skill предоставя инструменти и процедури за **директна манипулация** на DomOS Cloud SQL базата данни. За разлика от API-базирания подход, тук се работи директно с PostgreSQL чрез SQL заявки.

⚠️ **ВНИМАНИЕ**: Директният достъп до production база данни изисква повишено внимание!

## Cloud SQL Connection Details

```
Instance Name: domos-db
Connection Name: bionic-region-502615-h8:europe-west3:domos-db
Database: domos
User: domos_user
Region: europe-west3
IP: 34.40.67.38
```

## Методи за Връзка

### 1. Cloud SQL Proxy (Препоръчителен)

```bash
# Стартиране на Cloud SQL Proxy
cloud-sql-proxy bionic-region-502615-h8:europe-west3:domos-db --port=5432 &

# Връзка с psql
PGPASSWORD="$DOMOS_DB_PASSWORD" psql -h localhost -p 5432 -U domos_user -d domos
```

### 2. Cloud SQL Studio (Web UI)

URL: https://console.cloud.google.com/sql/instances/domos-db/studio?project=bionic-region-502615-h8

### 3. Директна Връзка (с Public IP)

```bash
# Изисква IP да е в authorized networks
PGPASSWORD="$DOMOS_DB_PASSWORD" psql -h 34.40.67.38 -U domos_user -d domos
```

### 4. Python с psycopg2

```python
import os
import psycopg2

# Чрез Unix socket (в Cloud Run)
conn = psycopg2.connect(
    host='/cloudsql/bionic-region-502615-h8:europe-west3:domos-db',
    database='domos',
    user='domos_user',
    password=os.environ.get('DOMOS_DB_PASSWORD')
)

# Чрез Cloud SQL Proxy (локално)
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='domos',
    user='domos_user',
    password=os.environ.get('DOMOS_DB_PASSWORD')
)
```

## ⚠️ Правила за Безопасност

### ЗАДЪЛЖИТЕЛНО преди destructive операции:

1. **ВИНАГИ backup преди DELETE/UPDATE**
   ```sql
   -- Backup на таблица преди промени
   CREATE TABLE apartments_backup_20260727 AS SELECT * FROM apartments;
   ```

2. **ВИНАГИ използвай transactions**
   ```sql
   BEGIN;
   -- твоите промени тук
   -- провери резултата
   COMMIT; -- или ROLLBACK;
   ```

3. **ВИНАГИ dry-run първо**
   ```sql
   -- Преди UPDATE/DELETE, провери какво ще засегнеш:
   SELECT * FROM apartments WHERE monthly_fee < 10;
   -- След като си сигурен:
   UPDATE apartments SET monthly_fee = 15 WHERE monthly_fee < 10;
   ```

4. **Провери FK constraints преди delete**
   ```sql
   -- Провери дали апартаментът има свързани записи
   SELECT 
       (SELECT COUNT(*) FROM obligations WHERE apartment_id = 1) as obligations,
       (SELECT COUNT(*) FROM payments WHERE apartment_id = 1) as payments,
       (SELECT COUNT(*) FROM apartment_accounts WHERE apartment_id = 1) as accounts;
   ```

5. **Никога не hardcode-вай пароли в код или SQL файлове**
   - Използвай environment variables: `$DOMOS_DB_PASSWORD`
   - Или Secret Manager: `gcloud secrets versions access latest --secret=domos-db-password`

## Database Schema Reference

Виж skill `domos-db-query` за пълната документация на схемата.

### Основни Таблици

| Таблица | Описание | FK Dependencies |
|---------|----------|------------------|
| `apartments` | Апартаменти | - |
| `users` | Потребители | - |
| `apartment_accounts` | Сметки | → apartments |
| `obligations` | Задължения | → apartments |
| `payments` | Плащания | → apartments, users |
| `account_transactions` | Транзакции | → apartment_accounts |
| `receipts` | Разписки | → payments, users |
| `expenses` | Разходи | → users |
| `audit_logs` | Одит лог | → users, apartments |

### FK Dependency Order (за delete)

```
1. receipts (depends on: payments, users)
2. account_transactions (depends on: apartment_accounts)
3. payments (depends on: apartments, users)
4. obligations (depends on: apartments)
5. apartment_accounts (depends on: apartments)
6. expenses (depends on: users)
7. audit_logs (depends on: users, apartments)
8. apartments (base table)
9. users (base table)
```

## CRUD Операции

### CREATE - Добавяне на Записи

#### Нов Апартамент
```sql
BEGIN;

INSERT INTO apartments (number, floor, owner_name, residents_count, monthly_fee, notes, created_at, updated_at)
VALUES ('15', 3, 'Петър Петров', 2, 25.00, NULL, NOW(), NOW())
RETURNING id, number, owner_name;

-- Автоматично създай account за апартамента
INSERT INTO apartment_accounts (apartment_id, balance, created_at, updated_at)
SELECT id, 0.00, NOW(), NOW() FROM apartments WHERE number = '15'
RETURNING id, apartment_id, balance;

COMMIT;
```

#### Ново Задължение
```sql
BEGIN;

INSERT INTO obligations (type, apartment_id, month, amount, description, created_at, updated_at)
VALUES ('monthly', 1, '2026-07', 25.00, 'Месечна такса юли 2026', NOW(), NOW())
RETURNING *;

-- Обнови баланса на сметката
UPDATE apartment_accounts 
SET balance = balance - 25.00, updated_at = NOW()
WHERE apartment_id = 1
RETURNING id, apartment_id, balance;

-- Създай transaction record
INSERT INTO account_transactions (account_id, type, amount, reference_type, reference_id, balance_after, description, created_at, updated_at)
SELECT 
    aa.id,
    'debit',
    25.00,
    'obligation',
    (SELECT id FROM obligations WHERE apartment_id = 1 AND month = '2026-07' ORDER BY id DESC LIMIT 1),
    aa.balance,
    'Месечна такса юли 2026',
    NOW(),
    NOW()
FROM apartment_accounts aa WHERE aa.apartment_id = 1
RETURNING *;

COMMIT;
```

#### Ново Плащане
```sql
BEGIN;

-- 1. Създай плащане
INSERT INTO payments (apartment_id, amount, month, payment_date, payment_method, collected_by_id, notes, status, created_at, updated_at)
VALUES (1, 50.00, '2026-07', CURRENT_DATE, 'cash', 1, 'Платено в брой', 'active', NOW(), NOW())
RETURNING *;

-- 2. Обнови баланса
UPDATE apartment_accounts 
SET balance = balance + 50.00, updated_at = NOW()
WHERE apartment_id = 1
RETURNING *;

-- 3. Създай transaction record
INSERT INTO account_transactions (account_id, type, amount, reference_type, reference_id, balance_after, description, created_at, updated_at)
SELECT 
    aa.id,
    'credit',
    50.00,
    'payment',
    (SELECT id FROM payments WHERE apartment_id = 1 ORDER BY id DESC LIMIT 1),
    aa.balance,
    'Плащане юли 2026',
    NOW(),
    NOW()
FROM apartment_accounts aa WHERE aa.apartment_id = 1
RETURNING *;

COMMIT;
```

### READ - Четене на Данни

#### Всички Апартаменти с Баланси
```sql
SELECT 
    a.id,
    a.number,
    a.floor,
    a.owner_name,
    a.residents_count,
    a.monthly_fee,
    COALESCE(aa.balance, 0) as balance,
    CASE 
        WHEN aa.balance < 0 THEN 'Дължи ' || ABS(aa.balance) || ' лв'
        WHEN aa.balance > 0 THEN 'Аванс ' || aa.balance || ' лв'
        ELSE 'Изравнен'
    END as status
FROM apartments a
LEFT JOIN apartment_accounts aa ON a.id = aa.apartment_id
ORDER BY a.number::int;
```

#### История на Плащанията за Апартамент
```sql
SELECT 
    p.id,
    p.amount,
    p.month,
    p.payment_date,
    p.payment_method,
    p.status,
    u.display_name as collected_by,
    p.notes
FROM payments p
LEFT JOIN users u ON p.collected_by_id = u.id
WHERE p.apartment_id = 1
ORDER BY p.payment_date DESC;
```

#### Транзакции по Сметка
```sql
SELECT 
    at.id,
    at.type,
    at.amount,
    at.reference_type,
    at.balance_after,
    at.description,
    at.created_at
FROM account_transactions at
JOIN apartment_accounts aa ON at.account_id = aa.id
WHERE aa.apartment_id = 1
ORDER BY at.created_at DESC;
```

### UPDATE - Обновяване на Записи

#### Промяна на Месечна Такса
```sql
BEGIN;

-- Backup първо
SELECT id, number, monthly_fee, updated_at 
FROM apartments WHERE id = 1;

-- Update
UPDATE apartments 
SET monthly_fee = 30.00, updated_at = NOW()
WHERE id = 1
RETURNING id, number, monthly_fee, updated_at;

COMMIT;
```

#### Корекция на Баланс (с audit)
```sql
BEGIN;

-- Запиши текущия баланс за audit
SELECT balance FROM apartment_accounts WHERE apartment_id = 1;

-- Направи корекция
UPDATE apartment_accounts 
SET balance = balance + 10.00, updated_at = NOW()
WHERE apartment_id = 1
RETURNING *;

-- Създай adjustment transaction
INSERT INTO account_transactions (account_id, type, amount, reference_type, balance_after, description, created_at, updated_at)
SELECT 
    id,
    'credit',
    10.00,
    'adjustment',
    balance,
    'Ръчна корекция на баланс - причина: ...',
    NOW(),
    NOW()
FROM apartment_accounts WHERE apartment_id = 1
RETURNING *;

COMMIT;
```

### DELETE - Изтриване на Записи

⚠️ **МНОГО ВНИМАТЕЛНО с изтриванията в production!**

#### Изтриване на Апартамент (само ако няма свързани данни)
```sql
BEGIN;

-- 1. Провери за свързани записи
SELECT 
    (SELECT COUNT(*) FROM obligations WHERE apartment_id = 5) as obligations,
    (SELECT COUNT(*) FROM payments WHERE apartment_id = 5) as payments,
    (SELECT COUNT(*) FROM apartment_accounts WHERE apartment_id = 5) as accounts,
    (SELECT COUNT(*) FROM audit_logs WHERE apartment_id = 5) as audit_logs;

-- 2. Ако всичко е 0, backup и изтрий
INSERT INTO apartments_deleted_backup 
SELECT *, NOW() as deleted_at FROM apartments WHERE id = 5;

DELETE FROM apartments WHERE id = 5 RETURNING *;

COMMIT;
```

#### Soft Delete на Плащане (void)
```sql
BEGIN;

-- Вместо DELETE, използвай void
UPDATE payments 
SET 
    status = 'voided',
    voided_at = NOW(),
    voided_by_id = 1,  -- ID на user който анулира
    void_reason = 'Грешно въведено плащане',
    updated_at = NOW()
WHERE id = 10
RETURNING *;

-- Обнови баланса (върни парите)
UPDATE apartment_accounts 
SET balance = balance - (SELECT amount FROM payments WHERE id = 10), updated_at = NOW()
WHERE apartment_id = (SELECT apartment_id FROM payments WHERE id = 10)
RETURNING *;

-- Създай void transaction
INSERT INTO account_transactions (account_id, type, amount, reference_type, reference_id, balance_after, description, created_at, updated_at)
SELECT 
    aa.id,
    'debit',
    p.amount,
    'void',
    p.id,
    aa.balance,
    'Анулирано плащане #' || p.id || ': ' || p.void_reason,
    NOW(),
    NOW()
FROM apartment_accounts aa
JOIN payments p ON aa.apartment_id = p.apartment_id
WHERE p.id = 10
RETURNING *;

COMMIT;
```

## Масови Операции

### Генериране на Месечни Задължения за Всички Апартаменти
```sql
BEGIN;

-- Провери кои апартаменти вече имат задължение за месеца
SELECT a.id, a.number 
FROM apartments a
WHERE NOT EXISTS (
    SELECT 1 FROM obligations o 
    WHERE o.apartment_id = a.id AND o.month = '2026-08' AND o.type = 'monthly'
);

-- Създай задължения за всички апартаменти без такова за месеца
INSERT INTO obligations (type, apartment_id, month, amount, description, created_at, updated_at)
SELECT 
    'monthly',
    a.id,
    '2026-08',
    a.monthly_fee,
    'Месечна такса август 2026',
    NOW(),
    NOW()
FROM apartments a
WHERE NOT EXISTS (
    SELECT 1 FROM obligations o 
    WHERE o.apartment_id = a.id AND o.month = '2026-08' AND o.type = 'monthly'
)
RETURNING id, apartment_id, amount;

-- Обнови балансите
UPDATE apartment_accounts aa
SET balance = aa.balance - a.monthly_fee, updated_at = NOW()
FROM apartments a
WHERE aa.apartment_id = a.id
AND EXISTS (
    SELECT 1 FROM obligations o 
    WHERE o.apartment_id = a.id AND o.month = '2026-08' AND o.type = 'monthly'
    AND o.created_at > NOW() - INTERVAL '1 minute'  -- само новосъздадените
)
RETURNING aa.apartment_id, aa.balance;

COMMIT;
```

### Корекция на Всички Баланси (Recalculation)
```sql
-- ⚠️ ОПАСНА ОПЕРАЦИЯ - само при несъответствия!
BEGIN;

-- Backup първо
CREATE TABLE apartment_accounts_backup_recalc AS SELECT * FROM apartment_accounts;

-- Преизчисли балансите от транзакциите
WITH calculated_balances AS (
    SELECT 
        aa.id as account_id,
        aa.apartment_id,
        aa.balance as current_balance,
        COALESCE(SUM(CASE WHEN at.type = 'credit' THEN at.amount ELSE -at.amount END), 0) as calculated_balance
    FROM apartment_accounts aa
    LEFT JOIN account_transactions at ON aa.id = at.account_id
    GROUP BY aa.id, aa.apartment_id, aa.balance
)
SELECT * FROM calculated_balances WHERE current_balance != calculated_balance;

-- Ако има разлики, коригирай (ВНИМАТЕЛНО!)
-- UPDATE apartment_accounts aa
-- SET balance = cb.calculated_balance, updated_at = NOW()
-- FROM calculated_balances cb
-- WHERE aa.id = cb.account_id AND aa.balance != cb.calculated_balance;

COMMIT;
```

## Backup и Restore

### Пълен Backup на Базата
```bash
# Чрез Cloud SQL Proxy
PGPASSWORD="$DOMOS_DB_PASSWORD" pg_dump -h localhost -p 5432 -U domos_user -d domos \
    --format=custom \
    --file=domos_backup_$(date +%Y%m%d_%H%M%S).dump

# Само данни (без schema)
PGPASSWORD="$DOMOS_DB_PASSWORD" pg_dump -h localhost -p 5432 -U domos_user -d domos \
    --data-only \
    --format=custom \
    --file=domos_data_$(date +%Y%m%d_%H%M%S).dump

# Само определени таблици
PGPASSWORD="$DOMOS_DB_PASSWORD" pg_dump -h localhost -p 5432 -U domos_user -d domos \
    --table=apartments \
    --table=payments \
    --format=custom \
    --file=domos_partial_$(date +%Y%m%d_%H%M%S).dump
```

### Restore от Backup
```bash
# Възстанови пълен backup
PGPASSWORD="$DOMOS_DB_PASSWORD" pg_restore -h localhost -p 5432 -U domos_user -d domos \
    --clean \
    --if-exists \
    domos_backup_20260727_143000.dump

# Възстанови само данни
PGPASSWORD="$DOMOS_DB_PASSWORD" pg_restore -h localhost -p 5432 -U domos_user -d domos \
    --data-only \
    domos_data_20260727_143000.dump
```

### SQL-based Backup (в базата)
```sql
-- Backup на таблица в друга таблица
CREATE TABLE apartments_backup_20260727 AS SELECT * FROM apartments;

-- Restore от backup таблица
BEGIN;
DELETE FROM apartments;  -- или TRUNCATE CASCADE ако няма FK
INSERT INTO apartments SELECT * FROM apartments_backup_20260727;
COMMIT;
```

## Помощни Скриптове

Виж `safe_operations.py` в същата директория за Python helper функции:
- `backup_table()` - автоматичен backup преди промени
- `safe_delete()` - проверка за FK и backup преди delete
- `safe_update()` - dry-run и backup преди update
- `execute_with_audit()` - logging на всички промени
- `dry_run()` - preview на промените без commit

Виж `common_queries.sql` за готови SQL snippets за типични операции.

## Audit Log

Всички критични операции трябва да се логват в `audit_logs` таблицата:

```sql
INSERT INTO audit_logs (
    timestamp, action, user_id, user_email, 
    entity_type, entity_id, apartment_id,
    description, state_before, state_after,
    extra_data, ip_address, is_critical
)
VALUES (
    NOW(),
    'MANUAL_UPDATE',
    NULL,  -- или user ID ако е известен
    'admin@domos.bg',
    'apartment',
    1,
    1,
    'Ръчна корекция на месечна такса от 25 на 30 лв',
    '{"monthly_fee": 25.00}'::jsonb,
    '{"monthly_fee": 30.00}'::jsonb,
    '{"reason": "Решение на ОС от 15.07.2026"}'::jsonb,
    '127.0.0.1',
    true
);
```

## Troubleshooting

### Connection Issues
```bash
# Провери дали Cloud SQL Proxy работи
ps aux | grep cloud-sql-proxy

# Рестартирай Cloud SQL Proxy
pkill cloud-sql-proxy
cloud-sql-proxy bionic-region-502615-h8:europe-west3:domos-db --port=5432 &

# Тествай връзка
PGPASSWORD="$DOMOS_DB_PASSWORD" psql -h localhost -p 5432 -U domos_user -d domos -c "SELECT 1;"
```

### Lock Issues
```sql
-- Виж активни заключвания
SELECT * FROM pg_locks WHERE NOT granted;

-- Виж активни транзакции
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- Прекрати блокираща транзакция (ОПАСНО!)
-- SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <blocked_pid>;
```

### Data Integrity Checks
```sql
-- Апартаменти без account
SELECT a.* FROM apartments a 
LEFT JOIN apartment_accounts aa ON a.id = aa.apartment_id 
WHERE aa.id IS NULL;

-- Orphan payments (без апартамент)
SELECT p.* FROM payments p 
LEFT JOIN apartments a ON p.apartment_id = a.id 
WHERE a.id IS NULL;

-- Несъответствия в баланси
WITH calc AS (
    SELECT 
        aa.apartment_id,
        aa.balance as stored_balance,
        COALESCE(SUM(CASE WHEN at.type = 'credit' THEN at.amount ELSE -at.amount END), 0) as calc_balance
    FROM apartment_accounts aa
    LEFT JOIN account_transactions at ON aa.id = at.account_id
    GROUP BY aa.apartment_id, aa.balance
)
SELECT * FROM calc WHERE stored_balance != calc_balance;
```

## Свързани Skills

- `domos-db-query` - документация на схемата и примерни SELECT заявки
- `domos-cloudrun-deploy` - deployment на приложението
- `domos-dev-start` - локална development среда