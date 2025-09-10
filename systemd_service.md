# 🔄 Systemd Service для Time Tracker

## Описание
Systemd сервис для автоматического запуска и управления Time Tracker на Linux серверах.

## 📁 Файлы сервиса

### 1. Создание сервиса
```bash
# Создайте файл сервиса
sudo nano /etc/systemd/system/time-tracker.service
```

### 2. Содержимое файла сервиса
```ini
[Unit]
Description=Time Tracker Application
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/time-tracker
Environment=PATH=/home/ubuntu/time-tracker/venv/bin
Environment=PYTHONPATH=/home/ubuntu/time-tracker
Environment=ENVIRONMENT=production
Environment=HOST=0.0.0.0
Environment=PORT=8001
Environment=DOMAIN=your-domain.com
Environment=TELEGRAM_BOT_TOKEN=your_bot_token_here
Environment=SECRET_KEY=your_super_secret_key
ExecStart=/home/ubuntu/time-tracker/venv/bin/python cloud_deploy.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=time-tracker

# Ограничения ресурсов
MemoryLimit=512M
CPUQuota=50%

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/home/ubuntu/time-tracker

[Install]
WantedBy=multi-user.target
```

### 3. Управление сервисом
```bash
# Перезагрузка конфигурации systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable time-tracker

# Запуск сервиса
sudo systemctl start time-tracker

# Проверка статуса
sudo systemctl status time-tracker

# Просмотр логов
sudo journalctl -u time-tracker -f

# Остановка сервиса
sudo systemctl stop time-tracker

# Перезапуск сервиса
sudo systemctl restart time-tracker
```

## 🔍 Мониторинг

### Проверка работы
```bash
# Статус сервиса
sudo systemctl is-active time-tracker

# Детальный статус
sudo systemctl status time-tracker -l

# Проверка порта
netstat -tlnp | grep 8001

# Health check
curl http://localhost:8001/health
```

### Логи
```bash
# Просмотр логов сервиса
sudo journalctl -u time-tracker -f

# Логи за последний час
sudo journalctl -u time-tracker --since "1 hour ago"

# Логи с ошибками
sudo journalctl -u time-tracker -p err

# Очистка логов (осторожно!)
sudo journalctl --vacuum-time=7d
```

## 🚨 Устранение неполадок

### Сервис не запускается
```bash
# Проверить логи
sudo journalctl -u time-tracker -n 50

# Проверить права на файлы
ls -la /home/ubuntu/time-tracker/

# Проверить виртуальное окружение
/home/ubuntu/time-tracker/venv/bin/python --version
```

### Сервис падает
```bash
# Проверить использование памяти
ps aux | grep python

# Проверить логи приложения
tail -f /home/ubuntu/time-tracker/cloud_deploy.log

# Проверить переменные окружения
sudo systemctl show time-tracker | grep Environment
```

### Перезапуск не работает
```bash
# Проверить настройки перезапуска
sudo systemctl show time-tracker | grep Restart

# Вручную перезапустить
sudo systemctl restart time-tracker
```

## 📊 Мониторинг с Prometheus + Grafana

### Настройка экспортера
```bash
# Установка Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvf node_exporter-1.6.1.linux-amd64.tar.gz
sudo mv node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/

# Создание сервиса для Node Exporter
sudo nano /etc/systemd/system/node-exporter.service
```

```ini
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node-exporter
Group=node-exporter
Type=simple
ExecStart=/usr/local/bin/node-exporter
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Запуск Node Exporter
sudo useradd -rs /bin/false node-exporter
sudo systemctl daemon-reload
sudo systemctl enable node-exporter
sudo systemctl start node-exporter
```

## 🔧 Оптимизация

### Настройка limits
```bash
# Увеличение лимитов
sudo nano /etc/security/limits.conf
# Добавить:
# ubuntu soft nofile 65536
# ubuntu hard nofile 65536
```

### Настройка sysctl
```bash
# Оптимизация сети
sudo nano /etc/sysctl.conf
# Добавить:
# net.core.somaxconn = 65536
# net.ipv4.tcp_max_syn_backlog = 65536
# net.ipv4.ip_local_port_range = 1024 65535

sudo sysctl -p
```

## 📈 Масштабирование

### Несколько инстансов
```bash
# Копирование сервиса для нескольких портов
sudo cp /etc/systemd/system/time-tracker.service /etc/systemd/system/time-tracker-8002.service

# Изменение порта в сервисе
sudo sed -i 's/PORT=8001/PORT=8002/' /etc/systemd/system/time-tracker-8002.service

# Запуск второго инстанса
sudo systemctl enable time-tracker-8002
sudo systemctl start time-tracker-8002
```

### Load Balancer (Nginx)
```nginx
# /etc/nginx/sites-available/time-tracker
upstream time_tracker_backend {
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://time_tracker_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔒 Безопасность

### Firewall
```bash
# Разрешить только необходимые порты
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### SELinux (если включен)
```bash
# Проверить статус SELinux
sestatus

# Если включен, настроить политики
sudo setsebool -P httpd_can_network_connect 1
```

## 📋 Проверка работы

### Автоматический тест
```bash
#!/bin/bash
# check_service.sh

SERVICE="time-tracker"
URL="http://localhost:8001/health"

# Проверка статуса сервиса
if systemctl is-active --quiet $SERVICE; then
    echo "✅ Сервис $SERVICE активен"

    # Проверка HTTP ответа
    if curl -s --max-time 5 $URL > /dev/null; then
        echo "✅ Health check пройден"
        exit 0
    else
        echo "❌ Health check не пройден"
        exit 1
    fi
else
    echo "❌ Сервис $SERVICE не активен"
    exit 1
fi
```

### Cron для регулярной проверки
```bash
# Добавить в crontab
crontab -e

# Проверка каждые 5 минут
*/5 * * * * /home/ubuntu/check_service.sh
```

---

**Systemd сервис обеспечивает надежную работу Time Tracker 24/7!** 🚀