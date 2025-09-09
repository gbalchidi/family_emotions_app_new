# Family Emotions Light

Телеграм-бот помощник для родителей, который анализирует поведение и фразы детей с помощью Claude AI и предоставляет психологические рекомендации.

## Архитектура

- **Domain-Driven Design (DDD)** с разделением на Bounded Contexts
- **Hexagonal Architecture** для изоляции бизнес-логики
- **CQRS** паттерн для разделения команд и запросов
- **Event-Driven** подход с доменными событиями

### Bounded Contexts

1. **User Context** - управление пользователями и детьми
2. **Analysis Context** - анализ ситуаций и генерация рекомендаций
3. **Recommendation Context** - AI-powered рекомендации через Claude API

## Технологический стек

- **Python 3.11+**
- **aiogram 3.4** - асинхронная библиотека для Telegram Bot API
- **PostgreSQL** - основная база данных
- **Redis** - кеширование и rate limiting
- **SQLAlchemy 2.0** - ORM с поддержкой asyncio
- **Anthropic Claude API** - AI анализ
- **Docker & Docker Compose** - контейнеризация
- **Poetry** - управление зависимостями

## Установка и запуск

### Предварительные требования

- Python 3.11+
- Docker и Docker Compose
- Poetry (опционально, для локальной разработки)

### Настройка окружения

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd family-emotions-light
```

2. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

3. Заполните необходимые переменные окружения:
- `BOT_TOKEN` - токен вашего Telegram бота
- `ANTHROPIC_API_KEY` - ключ API Claude
- `POSTGRES_PASSWORD` - пароль для PostgreSQL
- `SECRET_KEY` - секретный ключ приложения

### Запуск с Docker Compose

1. Запустите все сервисы:
```bash
docker-compose up -d
```

2. Примените миграции базы данных:
```bash
docker-compose exec bot alembic upgrade head
```

3. Проверьте логи:
```bash
docker-compose logs -f bot
```

### Локальная разработка

1. Установите зависимости через Poetry:
```bash
poetry install
```

2. Запустите PostgreSQL и Redis:
```bash
docker-compose up -d postgres redis
```

3. Примените миграции:
```bash
poetry run alembic upgrade head
```

4. Запустите бота:
```bash
poetry run python -m src.main
```

## Структура проекта

```
src/
├── domain/              # Доменный слой (бизнес-логика)
│   ├── user/           # User bounded context
│   │   ├── aggregates/ # Агрегаты и сущности
│   │   ├── value_objects/ # Объекты-значения
│   │   ├── events/     # Доменные события
│   │   └── repositories/ # Интерфейсы репозиториев
│   └── analysis/       # Analysis bounded context
├── application/        # Слой приложения
│   ├── commands/      # Команды (CQRS)
│   ├── queries/       # Запросы (CQRS)
│   └── services/      # Сервисы приложения
├── infrastructure/     # Инфраструктурный слой
│   ├── persistence/   # Работа с БД
│   ├── cache/        # Кеширование
│   ├── external_services/ # Внешние сервисы (Claude API)
│   └── config/       # Конфигурация
└── presentation/      # Презентационный слой
    └── telegram/     # Telegram bot интерфейс
        ├── handlers/ # Обработчики команд
        ├── keyboards/ # Клавиатуры
        └── middlewares/ # Middleware
```

## Основной функционал

### Для пользователей

1. **Регистрация и онбординг**
   - Ввод имени родителя
   - Добавление информации о ребенке (имя, возраст, пол)

2. **Анализ ситуаций**
   - Описание ситуации с ребенком
   - Получение AI-анализа с рекомендациями

3. **Управление профилем**
   - Добавление нескольких детей
   - Просмотр истории анализов

### AI-анализ включает

- **Скрытый смысл** - что на самом деле чувствует ребенок
- **Немедленные действия** - что делать прямо сейчас
- **Долгосрочные рекомендации** - стратегии воспитания
- **Чего не делать** - распространенные ошибки

## Rate Limiting

- **50 анализов в день** на пользователя
- **10 анализов в час** на пользователя

## Деплой на Coolify

1. Создайте новое приложение в Coolify
2. Подключите Git репозиторий
3. Установите переменные окружения
4. Используйте `docker-compose.yml` для конфигурации
5. Включите автоматический деплой

## Мониторинг и логирование

- Структурированное логирование через `structlog`
- JSON формат логов в production
- Отслеживание всех запросов и ошибок

## Безопасность

- Валидация всех входных данных
- Rate limiting для защиты от злоупотреблений
- Шифрование sensitive данных
- Изоляция через Docker контейнеры

## Разработка

### Запуск тестов

```bash
poetry run pytest
```

### Форматирование кода

```bash
poetry run black src/
poetry run isort src/
poetry run ruff src/
```

### Создание новой миграции

```bash
poetry run alembic revision --autogenerate -m "Description"
```

## Лицензия

Proprietary

## Поддержка

Для вопросов и предложений создавайте issue в репозитории.