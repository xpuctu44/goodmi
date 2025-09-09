# 🚀 Настройка Time Tracker для продакшена

## Домен: work.maxmobiles.ru

### 📋 Быстрый запуск

```bash
# Вариант 1: Интерактивный выбор (рекомендуется)
./start.sh

# Вариант 2: Только веб-сайт
python3 startmysite.py

# Вариант 3: Только Telegram бот
python3 startbot.py

# Вариант 4: Полная система (сайт + бот)
python3 startall.py

# Вариант 5: Прямой запуск веб-сайта
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### ⚙️ Настройка для продакшена

#### 1. Настройте файл `.env`

Создайте файл `.env` в корне проекта:

```env
# Настройки для продакшена
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8001
DOMAIN=work.maxmobiles.ru

# База данных
DATABASE_URL=sqlite:///./time_tracker.db
# Или для PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/timetracker

# Секретный ключ (ОБЯЗАТЕЛЬНО измените!)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Разрешенные хосты
ALLOWED_HOSTS=work.maxmobiles.ru,localhost,127.0.0.1

# Настройки логирования
LOG_LEVEL=INFO
```

#### 2. Настройка Nginx (рекомендуется)

Создайте конфигурацию Nginx `/etc/nginx/sites-available/work.maxmobiles.ru`:

```nginx
server {
    listen 80;
    server_name work.maxmobiles.ru;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Статические файлы (если есть)
    location /static/ {
        alias /path/to/your/project/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Активируйте конфигурацию:
```bash
sudo ln -s /etc/nginx/sites-available/work.maxmobiles.ru /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. SSL сертификат (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d work.maxmobiles.ru
```

#### 4. Настройка systemd сервиса

Создайте файл `/etc/systemd/system/timetracker.service`:

```ini
[Unit]
Description=Time Tracker Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
Environment=PATH=/path/to/your/project/venv/bin
ExecStart=/path/to/your/project/venv/bin/python startmysite.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируйте сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable timetracker
sudo systemctl start timetracker
sudo systemctl status timetracker
```

### 🔧 Параметры запуска

Скрипт `startmysite.py` автоматически настроен для продакшена:

- **Хост**: 0.0.0.0 (доступен извне)
- **Порт**: 8001
- **Воркеры**: 4 (для высокой нагрузки)
- **Таймаут**: 30 секунд
- **Лимит соединений**: 1000
- **Логирование**: включено

### 📊 Мониторинг

#### Проверка статуса:
```bash
# Статус сервиса
sudo systemctl status timetracker

# Логи
sudo journalctl -u timetracker -f

# Проверка порта
netstat -tlnp | grep :8001
```

#### Проверка работы сайта:
```bash
curl -I http://work.maxmobiles.ru
curl -I https://work.maxmobiles.ru
```

### 🛡️ Безопасность

1. **Измените секретный ключ** в `.env`
2. **Настройте файрвол**:
   ```bash
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```
3. **Регулярно обновляйте** зависимости
4. **Настройте резервное копирование** базы данных

### 🔄 Обновление

```bash
# Остановить сервис
sudo systemctl stop timetracker

# Обновить код
git pull origin main

# Установить новые зависимости
pip install -r requirements.txt

# Запустить сервис
sudo systemctl start timetracker
```

### 📝 Логи

Логи приложения доступны через:
- `sudo journalctl -u timetracker` - системные логи
- `tail -f /var/log/nginx/access.log` - логи Nginx
- `tail -f /var/log/nginx/error.log` - ошибки Nginx

### 🆘 Устранение неполадок

1. **Сайт не доступен**:
   - Проверьте статус сервиса: `sudo systemctl status timetracker`
   - Проверьте логи: `sudo journalctl -u timetracker -f`
   - Проверьте порт: `netstat -tlnp | grep :8001`

2. **Ошибки базы данных**:
   - Проверьте права доступа к файлу БД
   - Запустите миграции: `python3 -m app.migrations`

3. **Проблемы с Nginx**:
   - Проверьте конфигурацию: `sudo nginx -t`
   - Перезагрузите: `sudo systemctl reload nginx`
