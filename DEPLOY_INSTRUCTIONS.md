# Инструкции по развертыванию Family Emotions Light Bot

## Шаг 1: Подготовка окружения

Создайте файл `.env` в корне проекта:

```bash
cd /Users/glebbalcidi/Deployments/family-emotions-light
nano .env
```

Добавьте следующие переменные:

```
BOT_TOKEN=your_telegram_bot_token
ANTHROPIC_API_KEY=your_anthropic_api_key
POSTGRES_PASSWORD=secure_password_here
SECRET_KEY=your_secret_key_here
```

## Шаг 2: Коммит изменений

```bash
git add .
git commit -m "Update deploy script for docker compose v2"
git push origin main
```

## Шаг 3: Развертывание на сервере

### Вариант A: Через Coolify (если настроен)

1. Зайдите в Coolify
2. Найдите проект family-emotions-app
3. Нажмите "Redeploy" или "Force Rebuild"

### Вариант B: Ручное развертывание на сервере

1. Подключитесь к серверу:
```bash
ssh your-server
```

2. Перейдите в директорию проекта:
```bash
cd /tmp/family_emotions_app_new
```

3. Обновите код:
```bash
git pull origin main
```

4. Запустите скрипт развертывания:
```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

## Шаг 4: Проверка работы

1. Проверьте логи:
```bash
sudo docker compose -f docker-compose.v3.yml logs bot --tail 50
```

2. Убедитесь, что бот запустился без ошибок

3. Откройте Telegram и найдите вашего бота

4. Отправьте команду `/start`

## Устранение проблем

### Если появляется ошибка с dataclass

1. Полностью очистите Docker кэш:
```bash
sudo docker system prune -a --volumes
```

2. Пересоберите образ:
```bash
sudo docker build --no-cache --pull -t family-emotions-bot:latest .
```

3. Перезапустите сервисы:
```bash
sudo docker compose -f docker-compose.v3.yml down
sudo docker compose -f docker-compose.v3.yml up -d
```

### Если база данных не создается

1. Подключитесь к контейнеру PostgreSQL:
```bash
sudo docker compose -f docker-compose.v3.yml exec postgres psql -U family_bot -d family_emotions
```

2. Проверьте таблицы:
```sql
\dt
```

### Проверка версии кода в контейнере

```bash
sudo docker compose -f docker-compose.v3.yml exec bot cat /app/TEST_VERSION.txt
```

Если версия не соответствует последней, значит используется кэш.

## Мониторинг

Для постоянного мониторинга логов:
```bash
sudo docker compose -f docker-compose.v3.yml logs -f bot
```

## Остановка сервисов

```bash
sudo docker compose -f docker-compose.v3.yml down
```

## Важные заметки

- Убедитесь, что порты 5432 (PostgreSQL) и 6379 (Redis) не заняты другими сервисами
- Бот автоматически создаст необходимые таблицы в базе данных при первом запуске
- Все данные сохраняются в Docker volumes и не потеряются при перезапуске