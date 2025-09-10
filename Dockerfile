# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директории для логов и данных
RUN mkdir -p logs backups

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Открываем порт
EXPOSE 8001

# Команда запуска
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8001"]
