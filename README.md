# Family Emotions Light

Telegram бот для анализа детских эмоций и предоставления рекомендаций родителям с использованием Claude AI.

## Архитектура

Проект построен с использованием Domain-Driven Design (DDD) и Hexagonal Architecture:

```
src/
├── domain/           # Бизнес-логика
│   ├── aggregates/   # Агрегаты (User, Situation)
│   ├── value_objects/# Объекты-значения
│   ├── events/       # Доменные события
│   └── repositories/ # Интерфейсы репозиториев
├── application/      # Сервисы приложения
│   ├── commands/     # Команды
│   ├── services/     # Сервисы (UserService, AnalysisService)
│   └── dto/          # DTO для передачи данных
├── infrastructure/   # Инфраструктура
│   ├── database/     # PostgreSQL + SQLAlchemy
│   ├── redis/        # Redis для FSM
│   └── claude/       # Claude AI адаптер
└── presentation/     # Telegram Bot
    ├── handlers/     # Обработчики команд
    ├── keyboards/    # Клавиатуры
    └── states/       # FSM состояния
```

## Технологии

- **Python 3.11+** с полными type hints
- **aiogram 3.x** для Telegram Bot API
- **SQLAlchemy 2.0** с asyncpg
- **PostgreSQL** для хранения данных
- **Redis** для FSM состояний
- **Anthropic Claude** для анализа
- **Poetry** для управления зависимостями
- **Docker** и **Docker Compose**

## Установка

### 1. Клонирование репозитория

```bash
cd ~/Deployments/family-emotions-light
```

### 2. Настройка окружения

```bash
cp .env.example .env
```

Отредактируйте `.env` файл:
- `BOT_TOKEN` - токен вашего Telegram бота
- `ANTHROPIC_API_KEY` - ключ API Claude

### 3. Запуск с Docker

```bash
make docker-up
make migrate
```

### 4. Локальная разработка

```bash
# Установка зависимостей
poetry install

# Запуск PostgreSQL и Redis
docker-compose up -d postgres redis

# Запуск миграций
poetry run alembic upgrade head

# Запуск бота
poetry run python -m src.bot
```

## Команды

```bash
make help          # Показать все команды
make install       # Установить зависимости
make test          # Запустить тесты
make lint          # Проверить код
make format        # Форматировать код
make run           # Запустить бот локально
make docker-up     # Запустить все сервисы
make docker-down   # Остановить сервисы
make migrate       # Выполнить миграции
```

## Основные сценарии

1. **Регистрация**: `/start` → ввод данных о ребенке
2. **Анализ ситуации**: Главное меню → "💭 Анализировать ситуацию" → описание → результат
3. **История анализов**: Главное меню → "📊 Мои анализы"

## Структура анализа

Claude анализирует ситуацию и предоставляет:
- 🔍 **Скрытый смысл** - что на самом деле происходит с ребенком
- ✅ **Что делать сейчас** - немедленные действия
- 📚 **Долгосрочные рекомендации** - стратегия развития
- ❌ **Чего НЕ делать** - типичные ошибки

## Тестирование

```bash
# Запуск всех тестов
make test

# Только unit тесты
poetry run pytest tests/unit -v

# С покрытием
poetry run pytest --cov=src --cov-report=html
```

## Деплой

### Production с Docker

```bash
docker-compose -f docker-compose.yml up -d
```

### Мониторинг

```bash
# Логи бота
docker-compose logs -f bot

# Состояние сервисов
docker-compose ps
```

## Разработка

### Создание новой миграции

```bash
poetry run alembic revision --autogenerate -m "описание изменений"
```

### Форматирование кода

```bash
make format
```

### Проверка типов

```bash
poetry run mypy src
```

## Лицензия

MIT