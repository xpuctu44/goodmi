# 🚀 Руководство по деплою Time Tracker

## Быстрый старт

### 1. Подготовка сервера

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Устанавливаем Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагружаемся для применения изменений
sudo reboot
```

### 2. Деплой приложения

```bash
# Клонируем репозиторий
git clone <your-repo-url> time-tracker
cd time-tracker

# Запускаем скрипт деплоя
./deploy.sh
```

### 3. Настройка домена

1. Настройте DNS запись для вашего домена
2. Отредактируйте `nginx.conf` и замените `yourdomain.com` на ваш домен
3. Получите SSL сертификаты (Let's Encrypt)

## Ручной деплой

### Вариант 1: Docker Compose (Рекомендуется)

```bash
# Копируем файлы на сервер
scp -r . user@server:/opt/time-tracker/

# На сервере
cd /opt/time-tracker
cp env.example .env
# Отредактируйте .env файл

# Запускаем
docker-compose up -d
```

### Вариант 2: Systemd сервис

```bash
# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Копируем systemd сервис
sudo cp time-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable time-tracker
sudo systemctl start time-tracker
```

## Настройка SSL (Let's Encrypt)

```bash
# Устанавливаем Certbot
sudo apt install certbot python3-certbot-nginx

# Получаем сертификат
sudo certbot --nginx -d yourdomain.com

# Автообновление
sudo crontab -e
# Добавляем: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Мониторинг и логи

### Просмотр логов

```bash
# Docker Compose
docker-compose logs -f

# Systemd
sudo journalctl -u time-tracker -f

# Файловые логи
tail -f logs/app.log
```

### Мониторинг ресурсов

```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Статус сервиса
sudo systemctl status time-tracker
```

## Резервное копирование

### Автоматическое (настроено в deploy.sh)

```bash
# Ручное создание бэкапа
python3 backup_db.py

# Восстановление из бэкапа
cp backups/time_tracker_backup_YYYYMMDD_HHMMSS.db time_tracker.db
```

### Настройка удаленного бэкапа

```bash
# Добавляем в crontab
crontab -e

# Ежедневный бэкап в 2:00
0 2 * * * cd /opt/time-tracker && python3 backup_db.py && rsync -av backups/ user@backup-server:/backups/time-tracker/
```

## Обновление приложения

```bash
# Останавливаем сервис
docker-compose down

# Обновляем код
git pull origin main

# Пересобираем и запускаем
docker-compose up -d --build
```

## Безопасность

### Firewall

```bash
# Настраиваем UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### Обновления

```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Устранение неполадок

### Приложение не запускается

```bash
# Проверяем логи
docker-compose logs

# Проверяем конфигурацию
docker-compose config

# Проверяем порты
sudo netstat -tlnp | grep :8000
```

### База данных повреждена

```bash
# Восстанавливаем из бэкапа
cp backups/latest_backup.db time_tracker.db

# Или пересоздаем
rm time_tracker.db
docker-compose restart
```

### Проблемы с SSL

```bash
# Проверяем сертификат
sudo certbot certificates

# Обновляем сертификат
sudo certbot renew --force-renewal
```

## Производительность

### Оптимизация для продакшена

1. **Увеличьте количество воркеров** в `docker-compose.yml`:
   ```yaml
   command: ["gunicorn", "app.main:app", "-w", "8", "-k", "uvicorn.workers.UvicornWorker"]
   ```

2. **Настройте кэширование** в nginx
3. **Используйте PostgreSQL** вместо SQLite для больших нагрузок
4. **Настройте мониторинг** (Prometheus + Grafana)

## Контакты

При возникновении проблем:
- Проверьте логи: `docker-compose logs -f`
- Создайте issue в репозитории
- Обратитесь к документации FastAPI
