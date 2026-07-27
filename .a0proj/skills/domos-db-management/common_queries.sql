-- ============================================================================
-- DomOS Database Management - Common SQL Queries
-- ============================================================================
-- Готови SQL snippets за типични операции с DomOS базата данни.
-- 
-- ВАЖНО: Винаги използвай BEGIN/COMMIT за destructive операции!
-- ВАЖНО: Провери WHERE условията с SELECT преди UPDATE/DELETE!
-- ============================================================================

-- ============================================================================
-- 1. АПАРТАМЕНТИ (APARTMENTS)
-- ============================================================================

-- 1.1 Добавяне на нов апартамент с автоматично създаване на account
-- ----------------------------------------------------------------------------
BEGIN;

-- Създай апартамент
INSERT INTO apartments (number, floor, owner_name, residents_count, monthly_fee, notes, created_at, updated_at)
VALUES (
    '15',           -- номер на апартамента
    3,              -- етаж
    'Петър Петров', -- име на собственика
    2,              -- брой живущи
    25.00,          -- месечна такса
    NULL,           -- бележки
    NOW(), 
    NOW()
)
RETURNING id, number, owner_name;

-- Създай account за апартамента (изпълни след горния INSERT)
INSERT INTO apartment_accounts (apartment_id, balance, created_at, updated_at)
SELECT id, 0.00, NOW(), NOW() 
FROM apartments 
WHERE number = '15'
RETURNING id, apartment_id, balance;

COMMIT;


-- 1.2 Списък на всички апартаменти с баланси и статус
-- ----------------------------------------------------------------------------
SELECT 
    a.id,
    a.number AS "Номер",
    a.floor AS "Етаж",
    a.owner_name AS "Собственик",
    a.residents_count AS "Живущи",
    a.monthly_fee AS "Месечна такса",
    COALESCE(aa.balance, 0) AS "Баланс",
    CASE 
        WHEN aa.balance < 0 THEN 'Дължи ' || ABS(aa.balance) || ' лв'
        WHEN aa.balance > 0 THEN 'Аванс ' || aa.balance || ' лв'
        ELSE 'Изравнен'
    END AS "Статус"
FROM apartments a
LEFT JOIN apartment_accounts aa ON a.id = aa.apartment_id
ORDER BY 
    CASE WHEN a.number ~ '^[0-9]+$' THEN a.number::int ELSE 999999 END,
    a.number;


-- 1.3 Апартаменти с дължими суми (длъжници)
-- ----------------------------------------------------------------------------
SELECT 
    a.number AS "Апартамент",
    a.owner_name AS "Собственик",
    ABS(aa.balance) AS "Дължима сума",
    a.monthly_fee AS "Месечна такса",
    ROUND(ABS(aa.balance) / NULLIF(a.monthly_fee, 0), 1) AS "Месеци назад"
FROM apartments a
JOIN apartment_accounts aa ON a.id = aa.apartment_id
WHERE aa.balance < 0
ORDER BY aa.balance ASC;


-- 1.4 Промяна на месечна такса
-- ----------------------------------------------------------------------------
BEGIN;

-- Преди UPDATE, провери текущата стойност
SELECT id, number, owner_name, monthly_fee 
FROM apartments 
WHERE id = 1;

-- Направи промяната
UPDATE apartments 
SET monthly_fee = 30.00, updated_at = NOW()
WHERE id = 1
RETURNING id, number, monthly_fee;

COMMIT;


-- 1.5 Масова промяна на месечни такси (напр. +10%)
-- ----------------------------------------------------------------------------
BEGIN;

-- Preview какво ще се промени
SELECT 
    number, 
    owner_name, 
    monthly_fee AS "Текуща такса",
    ROUND(monthly_fee * 1.10, 2) AS "Нова такса (+10%)"
FROM apartments;

-- Ако preview изглежда добре, изпълни UPDATE
-- UPDATE apartments 
-- SET monthly_fee = ROUND(monthly_fee * 1.10, 2), updated_at = NOW()
-- RETURNING number, monthly_fee;

COMMIT;


-- ============================================================================
-- 2. ЗАДЪЛЖЕНИЯ (OBLIGATIONS)
-- ============================================================================

-- 2.1 Масово създаване на месечни задължения за всички апартаменти
-- ----------------------------------------------------------------------------
BEGIN;

-- Задай месеца за генериране
DO $$
DECLARE
    target_month VARCHAR(7) := '2026-08';  -- ПРОМЕНИ МЕСЕЦА ТУК
    target_description TEXT := 'Месечна такса август 2026';
BEGIN
    -- Създай задължения за апартаменти, които нямат такова за месеца
    INSERT INTO obligations (type, apartment_id, month, amount, description, created_at, updated_at)
    SELECT 
        'monthly',
        a.id,
        target_month,
        a.monthly_fee,
        target_description,
        NOW(),
        NOW()
    FROM apartments a
    WHERE NOT EXISTS (
        SELECT 1 FROM obligations o 
        WHERE o.apartment_id = a.id 
        AND o.month = target_month 
        AND o.type = 'monthly'
    );

    RAISE NOTICE 'Създадени са задължения за месец %', target_month;
END $$;

-- Обнови балансите (намали ги със сумата на новите задължения)
UPDATE apartment_accounts aa
SET 
    balance = aa.balance - o.amount,
    updated_at = NOW()
FROM (
    SELECT apartment_id, amount 
    FROM obligations 
    WHERE created_at > NOW() - INTERVAL '1 minute'
    AND type = 'monthly'
) o
WHERE aa.apartment_id = o.apartment_id
RETURNING aa.apartment_id, aa.balance;

-- Създай debit транзакции за новите задължения
INSERT INTO account_transactions (
    account_id, type, amount, reference_type, reference_id, 
    balance_after, description, created_at, updated_at
)
SELECT 
    aa.id,
    'debit',
    o.amount,
    'obligation',
    o.id,
    aa.balance,
    o.description,
    NOW(),
    NOW()
FROM obligations o
JOIN apartment_accounts aa ON o.apartment_id = aa.apartment_id
WHERE o.created_at > NOW() - INTERVAL '1 minute'
AND o.type = 'monthly';

COMMIT;


-- 2.2 Добавяне на извънредно задължение (ремонт, глоба и др.)
-- ----------------------------------------------------------------------------
BEGIN;

INSERT INTO obligations (type, apartment_id, month, amount, description, created_at, updated_at)
VALUES (
    'repair',       -- тип: monthly/initial/penalty/repair/fund/other
    1,              -- apartment_id
    NULL,           -- месец (NULL за non-monthly)
    150.00,         -- сума
    'Вноска за ремонт на покрив - Решение от ОС 15.07.2026',
    NOW(),
    NOW()
)
RETURNING *;

-- Обнови баланса
UPDATE apartment_accounts 
SET balance = balance - 150.00, updated_at = NOW()
WHERE apartment_id = 1
RETURNING apartment_id, balance;

-- Запиши транзакция
INSERT INTO account_transactions (
    account_id, type, amount, reference_type, reference_id, 
    balance_after, description, created_at, updated_at
)
SELECT 
    aa.id,
    'debit',
    150.00,
    'obligation',
    (SELECT id FROM obligations WHERE apartment_id = 1 ORDER BY id DESC LIMIT 1),
    aa.balance,
    'Вноска за ремонт на покрив',
    NOW(),
    NOW()
FROM apartment_accounts aa 
WHERE aa.apartment_id = 1;

COMMIT;


-- 2.3 Списък на задължения за апартамент
-- ----------------------------------------------------------------------------
SELECT 
    o.id,
    o.type AS "Тип",
    o.month AS "Месец",
    o.amount AS "Сума",
    o.description AS "Описание",
    o.created_at AS "Създадено"
FROM obligations o
WHERE o.apartment_id = 1  -- ПРОМЕНИ apartment_id
ORDER BY o.created_at DESC;


-- 2.4 Общо задължения по месеци (статистика)
-- ----------------------------------------------------------------------------
SELECT 
    o.month AS "Месец",
    o.type AS "Тип",
    COUNT(*) AS "Брой",
    SUM(o.amount) AS "Обща сума"
FROM obligations o
WHERE o.month IS NOT NULL
GROUP BY o.month, o.type
ORDER BY o.month DESC, o.type;


-- ============================================================================
-- 3. ПЛАЩАНИЯ (PAYMENTS)
-- ============================================================================

-- 3.1 Регистриране на ново плащане
-- ----------------------------------------------------------------------------
BEGIN;

-- Създай плащане
INSERT INTO payments (
    apartment_id, amount, month, payment_date, payment_method, 
    collected_by_id, notes, status, created_at, updated_at
)
VALUES (
    1,              -- apartment_id
    50.00,          -- сума
    '2026-07',      -- месец
    CURRENT_DATE,   -- дата на плащане
    'cash',         -- метод: cash/bank/card
    1,              -- collected_by_id (user ID на касиера)
    'Платено в брой',
    'active',
    NOW(),
    NOW()
)
RETURNING *;

-- Обнови баланса (увеличи го)
UPDATE apartment_accounts 
SET balance = balance + 50.00, updated_at = NOW()
WHERE apartment_id = 1
RETURNING apartment_id, balance;

-- Запиши credit транзакция
INSERT INTO account_transactions (
    account_id, type, amount, reference_type, reference_id, 
    balance_after, description, created_at, updated_at
)
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
FROM apartment_accounts aa 
WHERE aa.apartment_id = 1;

COMMIT;


-- 3.2 Анулиране на плащане (void)
-- ----------------------------------------------------------------------------
BEGIN;

-- Намери плащането и провери детайлите
SELECT * FROM payments WHERE id = 10;  -- ПРОМЕНИ payment_id

-- Анулирай плащането
UPDATE payments 
SET 
    status = 'voided',
    voided_at = NOW(),
    voided_by_id = 1,  -- ID на user който анулира
    void_reason = 'Грешно въведена сума',  -- ПРОМЕНИ причината
    updated_at = NOW()
WHERE id = 10
RETURNING *;

-- Върни парите от баланса
UPDATE apartment_accounts 
SET 
    balance = balance - (SELECT amount FROM payments WHERE id = 10),
    updated_at = NOW()
WHERE apartment_id = (SELECT apartment_id FROM payments WHERE id = 10)
RETURNING apartment_id, balance;

-- Запиши void транзакция
INSERT INTO account_transactions (
    account_id, type, amount, reference_type, reference_id, 
    balance_after, description, created_at, updated_at
)
SELECT 
    aa.id,
    'debit',
    p.amount,
    'void',
    p.id,
    aa.balance,
    'Анулирано плащане #' || p.id || ': ' || COALESCE(p.void_reason, 'без причина'),
    NOW(),
    NOW()
FROM apartment_accounts aa
JOIN payments p ON aa.apartment_id = p.apartment_id
WHERE p.id = 10;

COMMIT;


-- 3.3 Плащания за месец (отчет)
-- ----------------------------------------------------------------------------
SELECT 
    p.id,
    a.number AS "Апартамент",
    a.owner_name AS "Собственик",
    p.amount AS "Сума",
    p.payment_date AS "Дата",
    p.payment_method AS "Метод",
    u.display_name AS "Касиер",
    p.status AS "Статус"
FROM payments p
JOIN apartments a ON p.apartment_id = a.id
LEFT JOIN users u ON p.collected_by_id = u.id
WHERE p.month = '2026-07'  -- ПРОМЕНИ месеца
ORDER BY p.payment_date DESC;


-- 3.4 Сумарен отчет за плащания по месеци
-- ----------------------------------------------------------------------------
SELECT 
    p.month AS "Месец",
    COUNT(*) AS "Брой плащания",
    SUM(CASE WHEN p.status = 'active' THEN p.amount ELSE 0 END) AS "Активни",
    SUM(CASE WHEN p.status = 'voided' THEN p.amount ELSE 0 END) AS "Анулирани",
    SUM(CASE WHEN p.payment_method = 'cash' THEN p.amount ELSE 0 END) AS "В брой",
    SUM(CASE WHEN p.payment_method = 'bank' THEN p.amount ELSE 0 END) AS "Банка",
    SUM(CASE WHEN p.payment_method = 'card' THEN p.amount ELSE 0 END) AS "Карта"
FROM payments p
WHERE p.status = 'active'
GROUP BY p.month
ORDER BY p.month DESC;


-- ============================================================================
-- 4. КОРЕКЦИИ НА БАЛАНСИ
-- ============================================================================

-- 4.1 Ръчна корекция на баланс (с audit trail)
-- ----------------------------------------------------------------------------
BEGIN;

-- Запиши текущия баланс
SELECT 
    a.number, 
    a.owner_name, 
    aa.balance AS "Текущ баланс"
FROM apartments a
JOIN apartment_accounts aa ON a.id = aa.apartment_id
WHERE a.id = 1;

-- Направи корекция
UPDATE apartment_accounts 
SET balance = balance + 10.00, updated_at = NOW()  -- положително = кредит, отрицателно = дебит
WHERE apartment_id = 1
RETURNING apartment_id, balance;

-- Създай adjustment транзакция
INSERT INTO account_transactions (
    account_id, type, amount, reference_type, reference_id, 
    balance_after, description, created_at, updated_at
)
SELECT 
    id,
    CASE WHEN 10.00 > 0 THEN 'credit' ELSE 'debit' END,  -- ПРОМЕНИ стойността
    ABS(10.00),  -- ПРОМЕНИ стойността
    'adjustment',
    NULL,
    balance,
    'Ръчна корекция: [ОПИШИ ПРИЧИНАТА ТУК]',  -- ПРОМЕНИ описанието
    NOW(),
    NOW()
FROM apartment_accounts 
WHERE apartment_id = 1;

-- Запиши в audit log
INSERT INTO audit_logs (
    timestamp, action, user_email, entity_type, entity_id, apartment_id,
    description, state_before, state_after, is_critical
)
SELECT 
    NOW(),
    'BALANCE_ADJUSTMENT',
    'admin@domos.bg',  -- ПРОМЕНИ с реалния email
    'apartment_account',
    aa.id,
    1,
    'Ръчна корекция на баланс: +10.00 лв. Причина: [ОПИШИ]',
    jsonb_build_object('balance', aa.balance - 10.00),
    jsonb_build_object('balance', aa.balance),
    true
FROM apartment_accounts aa
WHERE aa.apartment_id = 1;

COMMIT;


-- 4.2 Преизчисляване на баланс от транзакции (verification)
-- ----------------------------------------------------------------------------
WITH calculated AS (
    SELECT 
        aa.apartment_id,
        aa.balance AS stored_balance,
        COALESCE(
            SUM(CASE WHEN at.type = 'credit' THEN at.amount ELSE -at.amount END), 
            0
        ) AS calculated_balance
    FROM apartment_accounts aa
    LEFT JOIN account_transactions at ON aa.id = at.account_id
    GROUP BY aa.apartment_id, aa.balance
)
SELECT 
    a.number AS "Апартамент",
    c.stored_balance AS "Записан баланс",
    c.calculated_balance AS "Изчислен баланс",
    c.stored_balance - c.calculated_balance AS "Разлика",
    CASE 
        WHEN c.stored_balance = c.calculated_balance THEN '✓ OK'
        ELSE '⚠ НЕСЪОТВЕТСТВИЕ'
    END AS "Статус"
FROM calculated c
JOIN apartments a ON c.apartment_id = a.id
ORDER BY ABS(c.stored_balance - c.calculated_balance) DESC;


-- 4.3 Масово преизчисляване на баланси (ОПАСНО!)
-- ----------------------------------------------------------------------------
-- ⚠️ САМО при доказани несъответствия! Винаги backup първо!
BEGIN;

-- Backup на accounts
CREATE TABLE apartment_accounts_backup_recalc AS 
SELECT * FROM apartment_accounts;

-- Преизчисли и обнови
UPDATE apartment_accounts aa
SET 
    balance = COALESCE(calc.new_balance, 0),
    updated_at = NOW()
FROM (
    SELECT 
        aa2.id,
        SUM(CASE WHEN at.type = 'credit' THEN at.amount ELSE -at.amount END) AS new_balance
    FROM apartment_accounts aa2
    LEFT JOIN account_transactions at ON aa2.id = at.account_id
    GROUP BY aa2.id
) calc
WHERE aa.id = calc.id
AND aa.balance != COALESCE(calc.new_balance, 0)
RETURNING aa.apartment_id, aa.balance;

-- Провери резултата преди COMMIT
-- SELECT * FROM apartment_accounts ORDER BY apartment_id;

COMMIT;


-- ============================================================================
-- 5. ОТЧЕТИ И СТАТИСТИКА
-- ============================================================================

-- 5.1 Месечен отчет за събираемост
-- ----------------------------------------------------------------------------
WITH monthly_data AS (
    SELECT 
        '2026-07' AS month,  -- ПРОМЕНИ месеца
        (SELECT SUM(amount) FROM obligations WHERE month = '2026-07') AS total_obligations,
        (SELECT SUM(amount) FROM payments WHERE month = '2026-07' AND status = 'active') AS total_payments
)
SELECT 
    month AS "Месец",
    total_obligations AS "Общо задължения",
    total_payments AS "Общо плащания",
    total_obligations - COALESCE(total_payments, 0) AS "Неплатено",
    ROUND(COALESCE(total_payments, 0) / NULLIF(total_obligations, 0) * 100, 1) || '%' AS "Събираемост"
FROM monthly_data;


-- 5.2 Dashboard статистика
-- ----------------------------------------------------------------------------
SELECT 
    (SELECT COUNT(*) FROM apartments) AS "Апартаменти",
    (SELECT COUNT(*) FROM apartments a JOIN apartment_accounts aa ON a.id = aa.apartment_id WHERE aa.balance < 0) AS "Длъжници",
    (SELECT COALESCE(SUM(ABS(balance)), 0) FROM apartment_accounts WHERE balance < 0) AS "Общо дължимо",
    (SELECT COALESCE(SUM(balance), 0) FROM apartment_accounts WHERE balance > 0) AS "Общо аванси",
    (SELECT COUNT(*) FROM payments WHERE status = 'active' AND payment_date = CURRENT_DATE) AS "Плащания днес",
    (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'active' AND payment_date = CURRENT_DATE) AS "Сума днес";


-- 5.3 Топ 10 длъжници
-- ----------------------------------------------------------------------------
SELECT 
    a.number AS "Апартамент",
    a.owner_name AS "Собственик",
    ABS(aa.balance) AS "Дължима сума",
    (SELECT MAX(payment_date) FROM payments WHERE apartment_id = a.id AND status = 'active') AS "Последно плащане"
FROM apartments a
JOIN apartment_accounts aa ON a.id = aa.apartment_id
WHERE aa.balance < 0
ORDER BY aa.balance ASC
LIMIT 10;


-- 5.4 Разходи по категории
-- ----------------------------------------------------------------------------
SELECT 
    expense_type AS "Категория",
    COUNT(*) AS "Брой",
    SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) AS "Платени",
    SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) AS "Чакащи",
    SUM(CASE WHEN status = 'cancelled' THEN amount ELSE 0 END) AS "Отменени"
FROM expenses
GROUP BY expense_type
ORDER BY SUM(amount) DESC;


-- ============================================================================
-- 6. DATA CLEANUP И MAINTENANCE
-- ============================================================================

-- 6.1 Намиране на orphan записи
-- ----------------------------------------------------------------------------
-- Плащания без апартамент
SELECT p.* FROM payments p 
LEFT JOIN apartments a ON p.apartment_id = a.id 
WHERE a.id IS NULL;

-- Задължения без апартамент
SELECT o.* FROM obligations o 
LEFT JOIN apartments a ON o.apartment_id = a.id 
WHERE a.id IS NULL;

-- Транзакции без account
SELECT at.* FROM account_transactions at 
LEFT JOIN apartment_accounts aa ON at.account_id = aa.id 
WHERE aa.id IS NULL;

-- Апартаменти без account
SELECT a.* FROM apartments a 
LEFT JOIN apartment_accounts aa ON a.id = aa.apartment_id 
WHERE aa.id IS NULL;


-- 6.2 Създаване на липсващи accounts за апартаменти
-- ----------------------------------------------------------------------------
BEGIN;

INSERT INTO apartment_accounts (apartment_id, balance, created_at, updated_at)
SELECT a.id, 0.00, NOW(), NOW()
FROM apartments a
LEFT JOIN apartment_accounts aa ON a.id = aa.apartment_id
WHERE aa.id IS NULL
RETURNING *;

COMMIT;


-- 6.3 Почистване на дублирани месечни задължения
-- ----------------------------------------------------------------------------
-- Първо намери дубликатите
SELECT 
    apartment_id, 
    month, 
    type,
    COUNT(*) AS cnt,
    array_agg(id ORDER BY id) AS ids
FROM obligations
WHERE type = 'monthly' AND month IS NOT NULL
GROUP BY apartment_id, month, type
HAVING COUNT(*) > 1;

-- Изтрий дубликатите (запази първия)
-- ⚠️ ВНИМАТЕЛНО! Провери първо!
-- DELETE FROM obligations
-- WHERE id IN (
--     SELECT unnest(ids[2:])  -- всички освен първия
--     FROM (
--         SELECT array_agg(id ORDER BY id) AS ids
--         FROM obligations
--         WHERE type = 'monthly' AND month IS NOT NULL
--         GROUP BY apartment_id, month, type
--         HAVING COUNT(*) > 1
--     ) dups
-- );


-- ============================================================================
-- 7. BACKUP И RESTORE
-- ============================================================================

-- 7.1 In-database backup на критични таблици
-- ----------------------------------------------------------------------------
-- Backup на апартаменти
CREATE TABLE IF NOT EXISTS apartments_backup_manual AS SELECT *, NOW() as backup_date FROM apartments WHERE 1=0;
INSERT INTO apartments_backup_manual SELECT *, NOW() FROM apartments;

-- Backup на accounts
CREATE TABLE IF NOT EXISTS apartment_accounts_backup_manual AS SELECT *, NOW() as backup_date FROM apartment_accounts WHERE 1=0;
INSERT INTO apartment_accounts_backup_manual SELECT *, NOW() FROM apartment_accounts;

-- Backup на плащания
CREATE TABLE IF NOT EXISTS payments_backup_manual AS SELECT *, NOW() as backup_date FROM payments WHERE 1=0;
INSERT INTO payments_backup_manual SELECT *, NOW() FROM payments;


-- 7.2 Restore от backup таблица
-- ----------------------------------------------------------------------------
-- ⚠️ МНОГО ОПАСНО! Само при критична нужда!
BEGIN;

-- Изтрий текущите данни
-- TRUNCATE apartments CASCADE;

-- Възстанови от backup
-- INSERT INTO apartments (id, number, floor, owner_name, residents_count, monthly_fee, notes, created_at, updated_at)
-- SELECT id, number, floor, owner_name, residents_count, monthly_fee, notes, created_at, updated_at
-- FROM apartments_backup_manual
-- WHERE backup_date = (SELECT MAX(backup_date) FROM apartments_backup_manual);

-- Нулирай sequence
-- SELECT setval('apartments_id_seq', (SELECT MAX(id) FROM apartments));

COMMIT;


-- 7.3 Почистване на стари backup таблици
-- ----------------------------------------------------------------------------
-- Виж backup таблиците
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE '%_backup_%'
ORDER BY table_name;

-- Изтрий стар backup (ВНИМАТЕЛНО!)
-- DROP TABLE IF EXISTS apartments_backup_20