# Деплой Family Emotions Bot в Coolify

## ВАЖНО: Решение проблемы с Nixpacks

Coolify по умолчанию использует Nixpacks для Python проектов, но это может вызвать проблемы. У вас есть 3 варианта:

### Вариант A: Использовать Docker Compose (РЕКОМЕНДУЕТСЯ)
В Coolify выберите тип приложения "Docker Compose" вместо "Nixpacks"

### Вариант B: Использовать наш Dockerfile
В настройках Coolify укажите Build Pack: "Dockerfile"

### Вариант C: Nixpacks конфигурация
Проект уже содержит nixpacks.toml для правильной сборки

## Способ 1: Docker Compose (Рекомендуется)

### 1. В Coolify создайте новое приложение:
- New Project → New Resource → **Docker Compose** (НЕ Nixpacks!)
- Source: GitHub
- Repository: `https://github.com/gbalchidi/family_emotions_app_new`

### 2. Настройте переменные окружения в Coolify:
```env
BOT_TOKEN=your_telegram_bot_token
ANTHROPIC_API_KEY=your_anthropic_api_key
POSTGRES_DB=family_emotions
POSTGRES_USER=family_bot
POSTGRES_PASSWORD=secure_password_here
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
RATE_LIMIT_DAILY=50
RATE_LIMIT_HOURLY=10
```

### 3. В настройках приложения Coolify:
- Docker Compose Location: `/docker-compose.coolify.yml`
- Port Exposes: не требуется (бот не слушает порты)

### 4. Deploy!

После первого деплоя выполните миграции:
```bash
# В Coolify terminal для контейнера bot:
alembic upgrade head
```

## Способ 2: Раздельные сервисы (Для production)

### 1. Создайте PostgreSQL в Coolify:
- New Resource → Database → PostgreSQL
- Запомните connection string

### 2. Создайте Redis в Coolify:
- New Resource → Database → Redis
- Запомните connection string

### 3. Модифицируйте docker-compose для бота:

Создайте `docker-compose.production.yml`:
```yaml
version: '3.8'

services:
  bot:
    build: .
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=${DATABASE_URL}  # От Coolify PostgreSQL
      - REDIS_URL=${REDIS_URL}        # От Coolify Redis
      - SECRET_KEY=${SECRET_KEY}
```

### 4. В Coolify для приложения:
- Docker Compose Location: `/docker-compose.production.yml`
- Добавьте переменные с connection strings от БД

## Проверка работоспособности

### 1. Проверьте логи:
```bash
# В Coolify UI смотрите логи контейнера bot
# Должно быть:
# Bot starting...
# Database initialized
# Bot started successfully
```

### 2. Проверьте бота в Telegram:
- Найдите вашего бота по username
- Отправьте `/start`
- Должен начаться онбординг

### 3. Проверьте базу данных:
```bash
# В terminal контейнера postgres:
psql -U family_bot -d family_emotions
\dt  # Показать таблицы
```

## Troubleshooting

### Ошибка "Bot token invalid":
- Проверьте BOT_TOKEN в переменных окружения
- Убедитесь что токен от @BotFather корректный

### Ошибка "Cannot connect to database":
- Проверьте что PostgreSQL контейнер запущен
- Проверьте DATABASE_URL или отдельные POSTGRES_* переменные
- Убедитесь что сеть docker настроена правильно

### Ошибка "Claude API error":
- Проверьте ANTHROPIC_API_KEY
- Проверьте лимиты API на anthropic.com

### База данных пустая:
- Выполните миграции: `alembic upgrade head`
- Проверьте логи на ошибки миграций

## Мониторинг

### Health Check endpoint:
Бот предоставляет health check (если включен API):
```
GET /health
```

### Метрики для мониторинга:
- Использование памяти контейнера
- CPU usage
- Количество активных пользователей (в БД)
- Rate limit счетчики (в Redis)

## Backup

### PostgreSQL backup:
```bash
# В Coolify terminal:
pg_dump -U family_bot family_emotions > backup.sql
```

### Redis backup:
```bash
# Redis автоматически сохраняет в /data/dump.rdb
docker cp family-emotions-redis:/data/dump.rdb ./redis-backup.rdb
```