# 🚀 Быстрый старт Time Tracker

## 📋 Доступные скрипты запуска

### 🎯 **Рекомендуемый способ (интерактивный)**
```bash
./start.sh
```
Выберите нужный режим:
- **1** - Только веб-сайт
- **2** - Только Telegram бот  
- **3** - Полная система (сайт + бот)

### 🌐 **Только веб-сайт**
```bash
python3 startmysite.py
```
- Запускает веб-сайт на порту 8001
- Доступен по адресу: http://localhost:8001
- Админ панель: http://localhost:8001/admin

### 🤖 **Только Telegram бот**
```bash
python3 startbot.py
```
- Запускает только Telegram бота
- Требует настройки токена в .env файле
- Работает параллельно с веб-сайтом

### 🚀 **Полная система (сайт + бот)**
```bash
python3 startall.py
```
- Запускает и веб-сайт, и Telegram бота одновременно
- Рекомендуется для продакшена

### 📱 **Оригинальный запуск бота**
```bash
python3 bot_runner.py
```
- Базовый скрипт для запуска бота
- Используется другими скриптами

## ⚙️ Настройка

### 1. Создайте файл `.env`
```env
# Настройки для продакшена
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8001
DOMAIN=work.maxmobiles.ru

# База данных
DATABASE_URL=sqlite:///./time_tracker.db

# Секретный ключ (ОБЯЗАТЕЛЬНО измените!)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Разрешенные хосты
ALLOWED_HOSTS=work.maxmobiles.ru,localhost,127.0.0.1

# Telegram бот (добавьте токен)
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 2. Получите токен Telegram бота
1. Напишите [@BotFather](https://t.me/botfather) в Telegram
2. Используйте команду `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `.env` файл

## 🌐 Доступ к системе

- **Веб-сайт**: http://localhost:8001
- **Админ панель**: http://localhost:8001/admin
- **Домен**: work.maxmobiles.ru (после настройки DNS)

## 🛑 Остановка

Нажмите `Ctrl+C` в терминале для остановки всех процессов.

## 📖 Подробная документация

- `PRODUCTION_SETUP.md` - полная инструкция по настройке
- `README_BOT.md` - документация по Telegram боту
- `README.md` - общая документация проекта
