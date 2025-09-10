# 🚀 Cloud Deployment для Time Tracker

## Описание
`cloud_deploy.py` - это универсальный скрипт для автоматического развертывания Time Tracker на облачных серверах (AWS, Google Cloud, DigitalOcean, Yandex Cloud и др.).

## ✨ Особенности

### 🔄 Автоматическое управление
- **Параллельный запуск** веб-сервера и Telegram бота
- **Автоматический перезапуск** при падении сервисов
- **Мониторинг состояния** в реальном времени
- **Graceful shutdown** при получении сигналов остановки

### 📊 Мониторинг и логирование
- **Health checks** каждые 30 секунд
- **Детальное логирование** всех действий
- **Статистика перезапусков** сервисов
- **Статус системы** в реальном времени

### 🛡️ Надежность
- **Лимит перезапусков** (5 попыток за 5 минут)
- **Обработка ошибок** и исключений
- **Восстановление после сбоев**
- **Проверка зависимостей** перед запуском

## 📋 Требования

### Системные требования
- Python 3.8+
- Linux/Windows/macOS
- Минимум 512MB RAM
- Минимум 1GB дискового пространства

### Зависимости
```bash
pip install -r requirements.txt
```

### Переменные окружения
```bash
# Обязательные
TELEGRAM_BOT_TOKEN=your_bot_token_here
SECRET_KEY=your_super_secret_key

# Опциональные
PORT=8001
HOST=0.0.0.0
DOMAIN=your-domain.com
ENVIRONMENT=production
```

## 🚀 Быстрый старт

### 1. Подготовка
```bash
# Клонируйте репозиторий
git clone <your-repo>
cd time-tracker

# Создайте виртуальное окружение (рекомендуется)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
```bash
# Создайте .env файл
cp .env.example .env

# Отредактируйте .env файл
nano .env
```

Пример `.env` файла:
```env
# Настройки сервера
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8001
DOMAIN=your-domain.com

# База данных
DATABASE_URL=sqlite:///./time_tracker.db

# Безопасность
SECRET_KEY=your-super-secret-key-change-this-in-production

# Telegram бот
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Разрешенные хосты
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# Логирование
LOG_LEVEL=INFO
```

### 3. Запуск
```bash
# Простой запуск
python cloud_deploy.py

# Или с переменными окружения
PORT=8001 DOMAIN=your-domain.com python cloud_deploy.py
```

## 📊 Мониторинг

### Статус системы
Скрипт автоматически показывает статус каждые 5 минут:
```
============================================================
📊 СТАТУС СИСТЕМЫ TIME TRACKER
============================================================
🌐 Веб-сервер: ✅ Активен
🤖 Telegram бот: ✅ Активен
👀 Мониторинг: ✅ Активен
🔄 Перезапуски веб-сервера: 0
🔄 Перезапуски бота: 0
🌐 URL: http://your-domain.com:8001
📊 Админ панель: http://your-domain.com:8001/admin
============================================================
```

### Логи
Все действия логируются в файл `cloud_deploy.log`:
```bash
tail -f cloud_deploy.log
```

## 🛠️ Расширенная настройка

### Переменные окружения
| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| `PORT` | `8001` | Порт веб-сервера |
| `HOST` | `0.0.0.0` | Хост веб-сервера |
| `DOMAIN` | `localhost` | Домен для ссылок |
| `TELEGRAM_BOT_TOKEN` | - | Токен Telegram бота (обязательно) |
| `SECRET_KEY` | - | Секретный ключ FastAPI (обязательно) |
| `DATABASE_URL` | `sqlite:///./time_tracker.db` | URL базы данных |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

### Настройка для разных облачных провайдеров

#### AWS EC2
```bash
# Установите переменные в EC2
export TELEGRAM_BOT_TOKEN="your_token"
export SECRET_KEY="your_secret"
export DOMAIN="your-ec2-instance.com"

# Запустите как systemd service
sudo cp cloud_deploy.service /etc/systemd/system/
sudo systemctl enable cloud_deploy
sudo systemctl start cloud_deploy
```

#### Google Cloud Run
```yaml
# cloud_run.yaml
env:
  - name: TELEGRAM_BOT_TOKEN
    value: "your_token"
  - name: SECRET_KEY
    value: "your_secret"
  - name: PORT
    value: "8080"
```

#### Docker
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["python", "cloud_deploy.py"]
```

## 🔧 Управление

### Остановка
```bash
# Graceful остановка (Ctrl+C)
# или
kill -TERM <pid>
```

### Проверка состояния
```bash
# Health check веб-сервера
curl http://localhost:8001/health

# Проверка процессов
ps aux | grep python

# Просмотр логов
tail -f cloud_deploy.log
```

### Ручное управление сервисами
```bash
# Только веб-сервер
python startmysite.py

# Только бот
python startbot.py

# Оба сервиса (простая версия)
python startall.py
```

## 🚨 Устранение неполадок

### Веб-сервер не запускается
```bash
# Проверьте порт
netstat -tlnp | grep 8001

# Проверьте логи
tail -f cloud_deploy.log

# Проверьте зависимости
python -c "import uvicorn; print('OK')"
```

### Бот не запускается
```bash
# Проверьте токен
echo $TELEGRAM_BOT_TOKEN

# Проверьте подключение к Telegram API
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe

# Проверьте логи бота
tail -f cloud_deploy.log | grep bot
```

### Высокое потребление ресурсов
```bash
# Уменьшите количество воркеров
# Измените в коде cloud_deploy.py:
# "--workers", "1",  # Вместо "2"
```

### Проблемы с базой данных
```bash
# Проверьте права на файл БД
ls -la time_tracker.db

# Пересоздайте БД если нужно
rm time_tracker.db
python -c "from app.database import init_db; init_db()"
```

## 📈 Производительность

### Оптимизация для облака
- **2 воркера** для веб-сервера (можно уменьшить до 1)
- **30 секунд** интервал health check
- **5 попыток** перезапуска за 5 минут
- **10 секунд** задержка перед перезапуском

### Мониторинг ресурсов
```bash
# CPU и память
top -p <pid>

# Дисковое пространство
df -h

# Сетевые соединения
netstat -tlnp
```

## 🔒 Безопасность

### Рекомендации
1. **Измените SECRET_KEY** на уникальный
2. **Используйте HTTPS** (настройте SSL)
3. **Ограничьте ALLOWED_HOSTS**
4. **Регулярно обновляйте зависимости**
5. **Мониторьте логи на подозрительную активность**

### Firewall настройки
```bash
# Разрешить только необходимые порты
ufw allow 8001
ufw allow 22
ufw --force enable
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `tail -f cloud_deploy.log`
2. Проверьте статус: `ps aux | grep python`
3. Проверьте health: `curl http://localhost:8001/health`
4. Создайте issue в репозитории с логами

## 🎯 Следующие шаги

После успешного развертывания:
1. ✅ Настройте домен и SSL
2. ✅ Настройте бэкапы базы данных
3. ✅ Настройте мониторинг (Prometheus/Grafana)
4. ✅ Настройте автоматические обновления
5. ✅ Оптимизируйте производительность

---

**🚀 Удачного развертывания!**