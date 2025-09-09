# Time Tracker - сайт без CSS

Мини-сервис учета рабочего времени (FastAPI + SQLite + SQLAlchemy + Jinja2) с единым стилем оформления.

## Особенности проекта

- ✅ Удалены все внешние CSS файлы
- 🎨 Единое оформление всех страниц в стиле админ-панели
- 📱 Адаптивный дизайн с контейнерной версткой
- 🔒 Встроенные стили для всех компонентов

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Доступные страницы

- `/` — главная страница
- `/register` — регистрация (для администратора нужен секрет: 20252025)
- `/login` — вход
- `/dashboard` — сотрудник (Я пришел/Я ушел)
- `/admin/planning` — планирование смен
- `/admin/schedule` — график (только просмотр опубликованного)
- `/admin/reports` — месячный отчет по присутствию
- `/admin/stores` — магазины, назначение сотрудникам

База данных создается автоматически в `time_tracker.db`.

## Зависимости

- fastapi, uvicorn
- sqlalchemy, pydantic
- jinja2
- passlib[bcrypt]
- python-multipart
- qrcode, Pillow (для QR-кодов)
