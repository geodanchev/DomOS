# DomOS Database Management Skill

## Trigger Phrases
- управление на базата данни
- добави потребител, създай потребител, нов потребител
- изтрий потребител, премахни потребител
- добави апартамент, създай апартамент, нов апартамент
- изтрий апартамент, премахни апартамент
- добави задължение, създай задължение
- добави плащане, създай плащане
- добави разход, създай разход
- покажи апартаменти, списък апартаменти
- покажи потребители, списък потребители
- database management, add user, delete user, add apartment

## Description
Този skill позволява управление на базата данни на DomOS MVP1-Cashier чрез REST API.
Поддържа CRUD операции за апартаменти, потребители, плащания, задължения и разходи.

## Database Structure Overview

### Core Entities

| Entity | Table | Description |
|--------|-------|-------------|
| Apartment | `apartments` | Апартаменти в сградата |
| User | `users` | Потребители (касиери, администратори) |
| Payment | `payments` | Плащания от апартаменти |
| Obligation | `obligations` | Задължения (месечни такси, глоби и др.) |
| Expense | `expenses` | Разходи от фонда на сградата |
| ApartmentAccount | `apartment_accounts` | Сметка на апартамент с баланс |
| AccountTransaction | `account_transactions` | Транзакции по сметка |
| Receipt | `receipts` | Разписки за плащания |
| AuditLog | `audit_logs` | Одит лог (immutable) |

### Entity Details

#### Apartment (apartments)
```
id: int (PK)
number: str (unique) - Номер на апартамента
floor: int | null - Етаж
owner_name: str - Име на собственика
residents_count: int (default 1) - Брой живущи
monthly_fee: decimal - Месечна такса в лева
notes: str | null - Бележки
created_at, updated_at: datetime
```

#### User (users)
```
id: int (PK)
username: str (unique) - Потребителско име
password_hash: str - Хеширана парола
display_name: str - Име за показване
role: enum (admin, cashier, viewer) - Роля
is_active: bool (default true)
created_at, updated_at: datetime
```

#### Payment (payments)
```
id: int (PK)
apartment_id: int (FK) - Апартамент
amount: decimal - Сума
month: str (YYYY-MM) - Месец
payment_date: date - Дата на плащане
payment_method: str (cash, bank, card)
collected_by_id: int (FK) - Касиер
notes: str | null
status: enum (active, voided, refunded)
voided_at, voided_by_id, void_reason: за анулиране
created_at, updated_at: datetime
```

#### Obligation (obligations)
```
id: int (PK)
type: enum (monthly, initial, penalty, repair, fund, other)
apartment_id: int (FK)
month: str | null (YYYY-MM) - само за monthly
amount: decimal - Сума
description: str | null
created_at, updated_at: datetime
```

#### Expense (expenses)
```
id: int (PK)
description: str - Описание
amount: decimal - Сума
expense_type: enum (repair, maintenance, utility, administrative, cleaning, elevator, security, insurance, other)
status: enum (pending, paid, cancelled)
expense_date: datetime
paid_date: datetime | null
vendor: str | null - Доставчик
invoice_number: str | null
notes: str | null
created_by: int | null
created_at, updated_at: datetime
```

#### ApartmentAccount (apartment_accounts)
```
id: int (PK)
apartment_id: int (FK, unique) - 1:1 с апартамент
balance: decimal - Текущ баланс (отрицателен = дължи)
created_at, updated_at: datetime
```

## API Endpoints

### Base URL
```
http://localhost:8001/api
```

### Authentication
Всички endpoints изискват JWT token:
```
Authorization: Bearer <token>
```

За получаване на token:
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Apartments API

#### List Apartments
```bash
GET /api/apartments
```

#### Get Apartment
```bash
GET /api/apartments/{id}
```

#### Create Apartment (Admin only)
```bash
POST /api/apartments
Content-Type: application/json

{
  "number": "1",
  "floor": 1,
  "owner_name": "Иван Иванов",
  "residents_count": 2,
  "monthly_fee": 15.00,
  "notes": "Бележка"
}
```

#### Update Apartment (Admin only)
```bash
PUT /api/apartments/{id}
Content-Type: application/json

{
  "owner_name": "Ново име",
  "monthly_fee": 20.00
}
```

#### Delete Apartment (Admin only)
```bash
DELETE /api/apartments/{id}
```

### Payments API

#### List Payments
```bash
GET /api/payments
```

#### Create Payment
```bash
POST /api/payments/
Content-Type: application/json

{
  "apartment_id": 1,
  "amount": 15.00,
  "month": "2026-06",
  "payment_method": "cash",
  "notes": "Платено в брой"
}
```

#### Void Payment (soft delete)
```bash
POST /api/payments/{id}/void
Content-Type: application/json

{
  "reason": "Грешно въведена сума"
}
```

### Obligations API

#### List Obligations
```bash
GET /api/obligations/
```

#### Create Obligation
```bash
POST /api/obligations/
Content-Type: application/json

{
  "type": "monthly",
  "apartment_id": 1,
  "month": "2026-06",
  "amount": 15.00,
  "description": "Месечна такса"
}
```

### Expenses API

#### List Expenses
```bash
GET /api/expenses/
```

#### Create Expense
```bash
POST /api/expenses/
Content-Type: application/json

{
  "description": "Почистване на входа",
  "amount": 100.00,
  "expense_type": "cleaning",
  "vendor": "Чистачка ООД"
}
```

## Usage Instructions

### Prerequisites
1. Backend сървърът трябва да работи на `http://localhost:8001`
2. За да стартирате dev средата, използвайте skill `domos-dev-start`

### Common Operations

#### 1. Добавяне на нов апартамент
```python
import requests

# Login first
login_response = requests.post(
    "http://localhost:8001/api/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = login_response.json()["access_token"]

# Create apartment
response = requests.post(
    "http://localhost:8001/api/apartments",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "number": "15",
        "floor": 3,
        "owner_name": "Петър Петров",
        "residents_count": 3,
        "monthly_fee": 25.00
    }
)
print(response.json())
```

#### 2. Списък на всички апартаменти
```python
response = requests.get(
    "http://localhost:8001/api/apartments",
    headers={"Authorization": f"Bearer {token}"}
)
for apt in response.json()["items"]:
    print(f"Ап. {apt['number']}: {apt['owner_name']} - {apt['monthly_fee']} лв")
```

#### 3. Добавяне на плащане
```python
response = requests.post(
    "http://localhost:8001/api/payments/",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "apartment_id": 1,
        "amount": 15.00,
        "month": "2026-06",
        "payment_method": "cash"
    }
)
print(response.json())
```

#### 4. Генериране на месечни задължения за всички апартаменти
```python
# Get all apartments
apartments = requests.get(
    "http://localhost:8001/api/apartments",
    headers={"Authorization": f"Bearer {token}"}
).json()["items"]

# Create obligation for each
for apt in apartments:
    requests.post(
        "http://localhost:8001/api/obligations/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "monthly",
            "apartment_id": apt["id"],
            "month": "2026-07",
            "amount": apt["monthly_fee"],
            "description": f"Месечна такса за Юли 2026"
        }
    )
```

## Important Notes

1. **Плащанията не се изтриват** - използва се void операция за грешни плащания
2. **Одит логът е immutable** - всички критични действия се записват
3. **Trailing slash** - POST endpoints изискват trailing slash (`/api/obligations/`)
4. **Account-based система** - балансът на апартамента се следи автоматично
5. **RBAC** - само admin може да създава/редактира апартаменти и потребители

## Default Users

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| admin | admin123 | admin | Администратор |
| cashier | cashier123 | cashier | Касиер (Цецка) |

## Related Skills
- `domos-dev-start` - Стартиране на dev средата
- `domos-dev-stop` - Спиране на dev средата
- `domos-dev-deploy` - Deploy в production
- `domos-git-push` - Push промени към GitHub
