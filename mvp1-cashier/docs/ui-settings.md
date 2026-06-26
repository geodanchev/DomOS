# UI Settings & Permissions

## Обзор

UI Settings системата позволява на frontend приложението да знае кои елементи да показва/скрива спрямо ролята на текущия потребител.

**Важно:** UI Settings е само за удобство на потребителския интерфейс. Backend-ът ВИНАГИ валидира правата при всяка операция и ще върне грешка ако потребителят се опита да извърши неоторизирано действие.

## Роли

| Роля | Описание |
|------|----------|
| `admin` | Пълен достъп до всички функции |
| `cashier` | Създаване на плащания и задължения, преглед на данни |
| `viewer` | Само преглед на данни |

## Permissions Матрица

| Операция | ADMIN | CASHIER | VIEWER | Permission Key |
|----------|:-----:|:-------:|:------:|----------------|
| Преглед апартаменти | ✅ | ✅ | ✅ | `apartments.view` |
| Създаване апартаменти | ✅ | ❌ | ❌ | `apartments.create` |
| Редактиране апартаменти | ✅ | ❌ | ❌ | `apartments.edit` |
| Изтриване апартаменти | ✅ | ❌ | ❌ | `apartments.delete` |
| Преглед плащания | ✅ | ✅ | ✅ | `payments.view` |
| Създаване плащания | ✅ | ✅ | ❌ | `payments.create` |
| Анулиране плащания | ✅ | ❌ | ❌ | `payments.void` |
| Преглед задължения | ✅ | ✅ | ✅ | `obligations.view` |
| Създаване задължения | ✅ | ✅ | ❌ | `obligations.create` |
| Редактиране задължения | ✅ | ❌ | ❌ | `obligations.edit` |
| Изтриване задължения | ✅ | ❌ | ❌ | `obligations.delete` |
| Генериране месечни | ✅ | ❌ | ❌ | `obligations.generate_monthly` |
| Преглед разходи | ✅ | ✅ | ✅ | `expenses.view` |
| Създаване разходи | ✅ | ✅ | ❌ | `expenses.create` |
| Редактиране разходи | ✅ | ❌ | ❌ | `expenses.edit` |
| Изтриване разходи | ✅ | ❌ | ❌ | `expenses.delete` |
| Преглед справки | ✅ | ✅ | ✅ | `reports.view` |
| Експорт справки | ✅ | ✅ | ✅ | `reports.export` |
| Scheduler jobs | ✅ | ❌ | ❌ | `scheduler.manage` |
| Управление потребители | ✅ | ❌ | ❌ | `users.manage` |

## API Response

### Login Response (Updated)

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=cecka&password=1234
```

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "username": "cecka",
    "display_name": "Цецка",
    "role": "cashier",
    "is_active": true
  },
  "permissions": {
    "apartments": {
      "view": true,
      "create": false,
      "edit": false,
      "delete": false
    },
    "payments": {
      "view": true,
      "create": true,
      "void": false
    },
    "obligations": {
      "view": true,
      "create": true,
      "edit": false,
      "delete": false,
      "generate_monthly": false
    },
    "expenses": {
      "view": true,
      "create": true,
      "edit": false,
      "delete": false
    },
    "reports": {
      "view": true,
      "export": true
    },
    "scheduler": {
      "manage": false
    },
    "users": {
      "manage": false
    }
  }
}
```

## Frontend Usage

### Файлова структура

```
src/
├── types/index.ts           # UIPermissions типове
├── context/AuthContext.tsx  # Auth + Permissions контекст
└── components/PermissionGate.tsx  # Компонент за условно рендиране
```

### Типове (types/index.ts)

```typescript
export interface ApartmentPermissions {
  view: boolean;
  create: boolean;
  edit: boolean;
  delete: boolean;
}

export interface PaymentPermissions {
  view: boolean;
  create: boolean;
  void: boolean;
}

export interface ObligationPermissions {
  view: boolean;
  create: boolean;
  edit: boolean;
  delete: boolean;
  generate_monthly: boolean;
}

// ... и т.н. за expenses, reports, scheduler, users

export interface UIPermissions {
  apartments: ApartmentPermissions;
  payments: PaymentPermissions;
  obligations: ObligationPermissions;
  expenses: ExpensePermissions;
  reports: ReportPermissions;
  scheduler: SchedulerPermissions;
  users: UserManagementPermissions;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
  permissions: UIPermissions;  // Добавено
}
```

### AuthContext (context/AuthContext.tsx)

```typescript
// Permissions се записват при login и се изчистват при logout
// Refresh на permissions става само при re-login
// При липса на permissions се използват DEFAULT_PERMISSIONS (viewer права)

import { useAuth, usePermissions } from '../context/AuthContext';

// Достъп до целия auth контекст
const { user, permissions, isAuthenticated, login, logout } = useAuth();

// Само permissions
const permissions = usePermissions();
```

### Налични Hooks

```typescript
import { 
  usePermissions,
  useCanView, 
  useCanCreate, 
  useCanEdit, 
  useCanDelete 
} from '../context/AuthContext';

import {
  useHasPermission,
  useHasAnyPermission,
  useHasAllPermissions
} from '../components/PermissionGate';

// Примери
const canEditApartments = useCanEdit('apartments');
const canVoidPayments = useHasPermission('payments', 'void');
const canManageUsers = useHasPermission('users', 'manage');
```

### PermissionGate Компонент

```tsx
import { PermissionGate } from '../components/PermissionGate';

// 1. Проста проверка
<PermissionGate feature="apartments" action="create">
  <Button>Добави апартамент</Button>
</PermissionGate>

// 2. С fallback
<PermissionGate 
  feature="payments" 
  action="void" 
  fallback={<span className="text-muted">Нямате права</span>}
>
  <Button variant="destructive">Анулирай</Button>
</PermissionGate>

// 3. Множество actions (показва ако ПОНЕ ЕДИН е разрешен)
<PermissionGate feature="apartments" actions={['edit', 'delete']}>
  <DropdownMenu>
    <DropdownMenuItem>Редактирай</DropdownMenuItem>
    <DropdownMenuItem>Изтрий</DropdownMenuItem>
  </DropdownMenu>
</PermissionGate>
```

### Примери за използване в компоненти

```tsx
// Използване с hooks
function ApartmentActions({ apartment }) {
  const canEdit = useCanEdit('apartments');
  const canDelete = useCanDelete('apartments');
  
  return (
    <>
      {canEdit && <Button onClick={() => handleEdit(apartment)}>Редактирай</Button>}
      {canDelete && <Button variant="destructive">Изтрий</Button>}
    </>
  );
}

// Използване с PermissionGate
function PaymentsList() {
  return (
    <div>
      <h1>Плащания</h1>
      
      <PermissionGate feature="payments" action="create">
        <NewPaymentDialog />
      </PermissionGate>
      
      <PaymentsTable />
    </div>
  );
}

// Скриване на цял раздел в навигацията
function Navigation() {
  const { permissions } = useAuth();
  
  return (
    <nav>
      <Link to="/dashboard">Табло</Link>
      <Link to="/apartments">Апартаменти</Link>
      <Link to="/payments">Плащания</Link>
      
      {permissions.scheduler.manage && (
        <Link to="/scheduler">Планировчик</Link>
      )}
      
      {permissions.users.manage && (
        <Link to="/users">Потребители</Link>
      )}
    </nav>
  );
}
```

## Security Notes

1. **Backend е source of truth** - UI permissions са само за UX, backend валидира всяка заявка
2. **Не разчитайте само на frontend** - злонамерен потребител може да заобиколи UI проверките
3. **Permissions се обновяват само при login** - промяна на роля изисква re-login
4. **Audit log** - всички критични операции се логват независимо от UI

## Бъдещи разширения

- `ui_settings` може да включва и други настройки (theme, items_per_page, default_view)
- Per-building permissions (ако потребител има различни права за различни сгради)
- Fine-grained permissions (напр. права само за определени апартаменти)
