# CI/CD Pipeline за DomOS

## Общ преглед

Този проект използва GitHub Actions за автоматично тестване при всеки pull request и push към main/master branch.

## Структура на Pipeline

Pipeline-ът се състои от 4 job-а, които се изпълняват паралелно:

### 1. Backend Tests
- **Цел**: Изпълнява всички backend тестове с pytest
- **Coverage**: Генерира code coverage report
- **Локация на тестове**: `mvp1-cashier/backend/tests/`
- **Команда**: `pytest tests/ -v --cov=app`

### 2. Frontend Tests
- **Цел**: Изпълнява всички frontend тестове с vitest
- **Build проверка**: Проверява дали приложението може да се build-не успешно
- **Локация на тестове**: `mvp1-cashier/frontend/src/test/`
- **Команди**: 
  - `npm run test:ci` (vitest run --coverage)
  - `npm run build` (tsc && vite build)

### 3. Backend Linting
- **Цел**: Проверява код качество на Python код
- **Tools**: flake8, black, isort
- **Забележка**: Грешките не блокират pipeline-а (continue-on-error: true)

### 4. Frontend Linting
- **Цел**: Проверява код качество на TypeScript/React код
- **Tools**: ESLint, TypeScript compiler
- **Забележка**: Грешките не блокират pipeline-а (continue-on-error: true)

## Trigger условия

Pipeline-ът се задейства при:
- **Pull Request** към `main` или `master` branch
- **Push** към `main` або `master` branch

## Локално изпълнение на тестове

### Backend
```bash
cd mvp1-cashier/backend
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
pytest tests/ -v --cov=app
```

### Frontend
```bash
cd mvp1-cashier/frontend
npm install
npm run test:ci
npm run build
```

## Статус на Pipeline

Можете да видите статуса на всички изпълнения в GitHub:
- Отидете в раздел **Actions** в GitHub repository
- Кликнете на конкретно изпълнение за подробности
- Зелена отметка ✅ означава успех
- Червен X ❌ означава провал

## Coverage Reports

- Backend coverage се качва в Codecov (ако е конфигурирано)
- Frontend coverage се генерира локално в `coverage/` директория

## Препоръки за разработчици

1. **Преди да push-нете код**: Изпълнете тестовете локално
2. **Преди да създадете PR**: Уверете се че всички тестове минават
3. **Review на failed builds**: Проверете GitHub Actions logs за детайли
4. **Добавяне на нови тестове**: При нова функционалност винаги добавяйте тестове

## Troubleshooting

### Backend тестове не минават
- Проверете дали всички dependencies са инсталирани
- Проверете дали test database е правилно настроена
- Прегледайте pytest output за конкретни грешки

### Frontend тестове не минават
- Проверете дали `npm ci` е изпълнено успешно
- Проверете дали vitest config е правилно настроен
- Прегледайте vitest output за конкретни грешки

### Build failure
- Проверете TypeScript грешки с `npx tsc --noEmit`
- Проверете Vite build локално с `npm run build`

## Бъдещи подобрения

- [ ] Добавяне на ESLint конфигурация
- [ ] E2E тестове с Playwright
- [ ] Docker image build в CI
- [ ] Автоматичен deployment при успешен merge
- [ ] Security scanning (Dependabot, CodeQL)
- [ ] Performance testing
