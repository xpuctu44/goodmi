# Time Tracker

Мини-сервис учета рабочего времени (FastAPI + SQLite + SQLAlchemy + Jinja2).

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Открой:
- /register — регистрация (для администратора нужен секрет: 20252025)
- /login — вход
- /dashboard — сотрудник (Я пришел/Я ушел)
- /admin/planning — планирование смен
- /admin/schedule — график (только просмотр опубликованного)
- /admin/reports — месячный отчет по присутствию
- /admin/reports/shifts — отчет по сменам с редактированием
- /admin/stores — магазины, назначение сотрудникам

База создается автоматически в `time_tracker.db`.

## Зависимости
- fastapi, uvicorn
- sqlalchemy, pydantic
- jinja2
- passlib[bcrypt]
- python-multipart


