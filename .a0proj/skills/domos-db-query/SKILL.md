# DomOS Database Query Skill

## Trigger Phrases
- "направи SQL заявка"
- "провери в базата"
- "database query"
- "покажи схемата на базата"
- "какви таблици има"

## Purpose
Предоставя точна информация за схемата на DomOS базата данни и помага при изграждане на правилни SQL заявки без грешки като "column does not exist".

## CRITICAL: Винаги проверявай актуалната схема!

**ПРЕДИ да пишеш SQL заявка, ВИНАГИ прочети актуалните model файлове:**

```bash
# Прочети всички модели
find /a0/usr/projects/domos/mvp1-cashier/backend/app/models -name '*.py' -exec cat {} \;

# Или конкретен модел
cat /a0/usr/projects/domos/mvp1-cashier/backend/app/models/obligation.py
cat /a0/usr/projects/domos/mvp1-cashier/backend/app/models/payment.py
cat /a0/usr/projects/domos/mvp1-cashier/backend/app/models/apartment.py
```

## Database Schema (към 2026-07-27)

### Таблица: `apartments`
| Колона | Тип | Nullable | Описание |
|--------|-----|----------|----------|
| id | INTEGER | NOT NULL | Primary Key |
| number | VARCHAR(20) | NOT NULL | Номер на апартамента (unique) |
| floor | INTEGER | NULL | Етаж |
| owner_name | VARCHAR(200) | NOT NULL | Име на собственика |
| residents_count | INTEGER | NOT NULL | Брой живущи (default: 1) |
| monthly_fee | NUMERIC(10,2) | NOT NULL | Месечна такса |
| notes | TEXT | NULL | Бележки |
| created_at | DATETIME | NOT NULL | Дата на създаване |
| updated_at | DATETIME | NOT NULL | Дата на промяна |

### Таблица: `obligations`
| Колона | Тип | Nullable | Описание |
|--------|-----|----------|----------|
| id | INTEGER | NOT NULL | Primary Key |
| type | ENUM | NOT NULL | Тип: monthly/initial/penalty/repair/fund/other |
| apartment_id | INTEGER | NOT NULL | FK към apartments |
| month | VARCHAR(7) | NULL | Месец (YYYY-MM), само за monthly |
| amount | NUMERIC(10,2) | NOT NULL | Сума на задължението |
| description | TEXT | NULL | Описание |
| created_at | DATETIME | NOT NULL | Дата на създаване |
| updated_at | DATETIME | NOT NULL | Дата на промяна |

⚠️ **ВАЖНО: obligations таблицата НЯМА колона `status`!**
Статусът на плащане се следи чрез `apartment_accounts.balance`, НЕ в obligations.

### Таблица: `payments`
| Колона | Тип | Nullable | Описание |
|--------|-----|----------|----------|
| id | INTEGER | NOT NULL | Primary Key |
| apartment_id | INTEGER | NOT NULL | FK към apartments |
| amount | NUMERIC(10,2) | NOT NULL | Платена сума |
| month | VARCHAR(7) | NOT NULL | Месец (YYYY-MM) |
| payment_date | DATE | NOT NULL | Дата на плащане |
| payment_method | VARCHAR(50) | NOT NULL | Метод: cash/bank/card |
| collected_by_id | INTEGER | NULL | FK към users |
| notes | TEXT | NULL | Бележки |
| status | ENUM | NOT NULL | active/voided/refunded |
| voided_at | DATETIME | NULL | Кога е анулирано |
| voided_by_id | INTEGER | NULL | FK към users |
| void_reason | TEXT | NULL | Причина за анулиране |
| created_at | DATETIME | NOT NULL | Дата на създаване |
| updated_at | DATETIME | NOT NULL | Дата на промяна |

### Таблица: `apartment_accounts`
| Колона | Тип | Nullable | Описание |
|--------|-----|----------|----------|
| id | INTEGER | NOT NULL | Primary Key |
| apartment_id | INTEGER | NOT NULL | FK към apartments (unique) |
| balance | NUMERIC(10,2) | NOT NULL | Текущ баланс (отрицателен = дължи) |
| created_at | DATETIME | NOT NULL | Дата на създаване |
| updated_at | DATETIME | NOT NULL | Дата на промяна |

### Таблица: `account_transactions`
| Колона | Тип | Nullable | Описание |
|--------|-----|----------|----------|
| id | INTEGER | NOT NULL | Primary Key |
| account_id | INTEGER | NOT NULL | FK към apartment_accounts |
| type | ENUM | NOT NULL | credit/debit |
| amount | NUMERIC(10,2) | NOT NULL | Сума |
| reference_type | ENUM | NOT NULL | payment/obligation/adjustment/migration/void |
| reference_id | INTEGER | NULL | ID на свързания запис |
| balance_after | NUMERIC(10,2) | NOT NULL | Баланс след транзакцията |
| description | TEXT | NULL | Описание |
| created_at | DATETIME | NOT NULL | Дата на създаване |
| updated_at | DATETIME | NOT NULL | Дата на промяна |

### Таблица: `users`
| Колона | Тип | Nullable | Описание |
|--------|-----|----------|----------|
| id | INTEGER | NOT NULL | Primary Key |
| username | VARCHAR(100) | NOT NULL | Потребителско име (unique) |
| password_hash | VARCHAR(255) | NOT NULL | Хеширана парола |
| display_name | VARCHAR(200) | NOT NULL | Име за показване |
| role | ENUM | NOT NULL | ADMIN/CASHIER/VIEWER |
| is_active | BOOLEAN | NOT NULL | Активен ли е |
| created_at | DATETIME | NOT NULL | Дата на създаване |
| updated_at | DATETIME | NOT NULL | Дата на промяна |

### Таблица: `receipts`
| Колона | Тип | Nullable | Описание |
|--------|-----|----------|----------|
| id | INTEGER | NOT NULL | Primary Key |
| receipt_number | VARCHAR(20) | NOT NULL | Номер (YYYY-NNNNNN) |
| payment_id | INTEGER | NOT NULL | FK към payments |
| is_copy | BOOLEAN | NOT NULL | Дали е копие |
| original_receipt_id | INTEGER | NULL | FK към receipts (за копия) |
| issued_at | DATETIME | NOT NULL | Кога е издадена |
| issued_by_id | INTEGER | NULL | FK към users |
| created_at | DATETIME | NOT NULL | Дата на създаване |
| updated_at | DATETIME | NOT NULL | Дата на промяна |

### Таблица: `expenses`
| Колона | Тип | Nullable | Описание |
|--------|-----|----------|----------|
| id | INTEGER | NOT NULL | Primary Key |
| description | VARCHAR(500) | NOT NULL | Описание |
| amount | NUMERIC(10,2) | NOT NULL | Сума |
| expense_type | ENUM | NOT NULL | repair/maintenance/utility/administrative/... |
| status | ENUM | NOT NULL | pending/paid/cancelled |
| expense_date | DATETIME | NOT NULL | Дата на разхода |
| paid_date | DATETIME | NULL | Дата на плащане |
| vendor | VARCHAR(255) | NULL | Доставчик |
| invoice_number | VARCHAR(100) | NULL | Номер на фактура |
| notes | TEXT | NULL | Бележки |
| created_by | INTEGER | NULL | User ID |
| created_at | DATETIME | NOT NULL | Дата на създаване |
| updated_at | DATETIME | NOT NULL | Дата на промяна |

### Таблица: `audit_logs`
| Колона | Тип | Nullable | Описание |
|--------|-----|----------|----------|
| id | INTEGER | NOT NULL | Primary Key |
| timestamp | DATETIME | NOT NULL | Timestamp |
| action | VARCHAR(100) | NOT NULL | Тип действие |
| user_id | INTEGER | NULL | FK към users |
| user_email | VARCHAR(255) | NULL | Email (denormalized) |
| entity_type | VARCHAR(100) | NULL | Тип entity |
| entity_id | INTEGER | NULL | ID на entity |
| apartment_id | INTEGER | NULL | FK към apartments |
| description | TEXT | NOT NULL | Описание |
| state_before | JSON | NULL | Състояние преди |
| state_after | JSON | NULL | Състояние след |
| extra_data | JSON | NULL | Допълнителни данни |
| ip_address | VARCHAR(45) | NULL | IP адрес |
| is_critical | BOOLEAN | NOT NULL | Критично действие |

## Примерни SQL Заявки

### Всички задължения
```sql
SELECT 
    o.id,
    o.type,
    o.apartment_id,
    a.number as apartment_number,
    a.owner_name,
    o.month,
    o.amount,
    o.description,
    o.created_at
FROM obligations o
JOIN apartments a ON o.apartment_id = a.id
ORDER BY o.created_at DESC;
```

### Баланс по апартаменти
```sql
SELECT 
    a.number,
    a.owner_name,
    aa.balance,
    CASE 
        WHEN aa.balance < 0 THEN 'Дължи ' || ABS(aa.balance) || ' лв'
        WHEN aa.balance > 0 THEN 'Аванс ' || aa.balance || ' лв'
        ELSE 'Изравнен'
    END as status
FROM apartments a
LEFT JOIN apartment_accounts aa ON a.id = aa.apartment_id
ORDER BY aa.balance ASC;
```

### Плащания за месец
```sql
SELECT 
    p.id,
    a.number as apartment,
    p.amount,
    p.payment_date,
    p.payment_method,
    p.status
FROM payments p
JOIN apartments a ON p.apartment_id = a.id
WHERE p.month = '2026-07'
  AND p.status = 'active'
ORDER BY p.payment_date DESC;
```

### Транзакции по сметка
```sql
SELECT 
    at.id,
    at.type,
    at.amount,
    at.reference_type,
    at.reference_id,
    at.balance_after,
    at.description,
    at.created_at
FROM account_transactions at
JOIN apartment_accounts aa ON at.account_id = aa.id
JOIN apartments a ON aa.apartment_id = a.id
WHERE a.number = '1'
ORDER BY at.created_at DESC;
```

### Общо събрани суми
```sql
SELECT 
    SUM(amount) as total_collected,
    COUNT(*) as payment_count
FROM payments
WHERE status = 'active';
```

### Общо задължения
```sql
SELECT 
    SUM(amount) as total_obligations,
    COUNT(*) as obligation_count
FROM obligations;
```

### Баланс на фонда
```sql
SELECT 
    (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'active') -
    (SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE status = 'paid')
    as fund_balance;
```

## Cloud SQL Connection Info

- **Instance**: `domos-db`
- **Database**: `domos`
- **User**: `domos_user`
- **Connection Name**: `bionic-region-502615-h8:europe-west3:domos-db`

### Cloud SQL Studio
https://console.cloud.google.com/sql/instances/domos-db/studio?project=bionic-region-502615-h8

### Connection String (от Secret Manager)
```
postgresql://domos_user:<PASSWORD>@/domos?host=/cloudsql/bionic-region-502615-h8:europe-west3:domos-db
```

## Често срещани грешки

### ❌ Грешка: `column "status" does not exist` в obligations
**Причина**: obligations таблицата НЯМА status колона
**Решение**: Използвай `apartment_accounts.balance` за да провериш дали задължението е платено

### ❌ Грешка: `column "amount_paid" does not exist` в obligations  
**Причина**: Премахната в account-based системата
**Решение**: Плащанията се следят чрез payments и account_transactions

### ❌ Грешка: `column "amount_due" does not exist` в obligations
**Причина**: Преименувано на `amount`
**Решение**: Използвай `amount` вместо `amount_due`
