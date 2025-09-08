import os
import asyncio
import secrets
import string
from datetime import datetime, timezone, timedelta, date
import re
from typing import Dict, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User, Attendance, Store, AllowedIP
from app.security import verify_password, hash_password


class TelegramBot:
    def __init__(self):
        self.application = None
        self.user_sessions: Dict[int, Dict] = {}  # telegram_id -> session data

    def _get_moscow_time(self) -> datetime:
        """Получает текущее время в московском часовом поясе (UTC+3)"""
        moscow_tz = timezone(timedelta(hours=3))
        return datetime.now(moscow_tz)

    def _get_db_session(self) -> Session:
        """Получает сессию базы данных"""
        return next(get_db())

    def _check_telegram_user_allowed(self, user_id: int) -> tuple[bool, str]:
        """Проверяет, разрешен ли Telegram пользователь для отметки прихода/ухода

        Returns:
            tuple: (is_allowed: bool, message: str)
        """
        db = self._get_db_session()

        # Получаем пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Пользователь не найден"

        # Получаем список разрешенных IP
        allowed_ips = db.query(AllowedIP).filter(AllowedIP.is_active == True).all()

        # Если нет разрешенных IP вообще, разрешаем всем
        if not allowed_ips:
            return True, "IP проверка отключена (нет разрешенных IP)"

        # Для Telegram пользователей мы не можем получить реальный IP адрес,
        # поэтому проверяем альтернативные критерии:

        # 1. Проверяем, есть ли у пользователя недавняя активность через веб-интерфейс
        # (это косвенно указывает на то, что пользователь имеет доступ к разрешенной сети)
        recent_attendance = db.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.started_at >= datetime.now() - timedelta(days=7)  # Последние 7 дней
        ).first()

        if recent_attendance:
            return True, "Разрешено на основе недавней активности"

        # 2. Проверяем, есть ли у пользователя опубликованный график на текущий месяц
        # (это указывает на то, что пользователь является активным сотрудником)
        current_month = date.today().replace(day=1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)

        from app.models import ScheduleEntry
        active_schedule = db.query(ScheduleEntry).filter(
            ScheduleEntry.user_id == user_id,
            ScheduleEntry.work_date >= current_month,
            ScheduleEntry.work_date < next_month,
            ScheduleEntry.published == True
        ).first()

        if active_schedule:
            return True, "Разрешено для активного сотрудника с графиком"

        # Если ни одного критерия не выполнено, но есть разрешенные IP,
        # показываем предупреждение, но разрешаем действие с уведомлением
        return True, "⚠️ Внимание: IP проверка активна, но для Telegram пользователей проверка ограничена. Рекомендуется использовать веб-интерфейс с разрешенного IP."

    def _generate_web_credentials(self, name: str) -> tuple[str, str]:
        """Генерирует логин и пароль для веб-доступа"""
        # Генерируем логин на основе имени
        base_username = name.lower().replace(' ', '_').replace('-', '_')
        username = base_username

        # Проверяем уникальность логина
        db = self._get_db_session()
        counter = 1
        while db.query(User).filter(User.web_username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1

        # Генерируем случайный пароль
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(8))

        return username, password

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        telegram_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Проверяем, зарегистрирован ли пользователь
        db = self._get_db_session()
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if user:
            self.user_sessions[telegram_id] = {"user_id": user.id, "step": "main_menu"}
            await update.message.reply_text(
                f"Привет, {user.full_name or username}!\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user.id)
            )
        else:
            # Проверяем, есть ли пользователь с новыми учетными данными
            # Ищем по telegram_id в сессиях или по другим признакам
            # Для обратной совместимости проверяем все возможные форматы
            self.user_sessions[telegram_id] = {
                "step": "register_full_name",
                "registration_data": {}
            }
            await update.message.reply_text(
                "Добро пожаловать в систему учета рабочего времени!\n\n"
                "Для начала работы нужно зарегистрироваться.\n\n"
                "📝 Шаг 1 из 4: Введите ваше полное имя (Фамилия Имя Отчество):"
            )

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /register"""
        telegram_id = update.effective_user.id
        self.user_sessions[telegram_id] = {
            "step": "register_full_name",
            "registration_data": {}
        }
        await update.message.reply_text(
            "Регистрация в системе учета рабочего времени.\n\n"
            "📝 Шаг 1 из 4: Введите ваше полное имя (Фамилия Имя Отчество):"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        telegram_id = update.effective_user.id
        text = update.message.text

        if telegram_id not in self.user_sessions:
            await update.message.reply_text("Используйте /start для начала работы")
            return

        session = self.user_sessions[telegram_id]
        step = session.get("step")

        if step.startswith("register_"):
            await self._handle_registration_step(update, text)
        elif step == "main_menu":
            await self._handle_main_menu(update, text)
        else:
            await update.message.reply_text("Неизвестная команда. Используйте меню.")

    async def _handle_registration_step(self, update, text):
        """Обработка шагов регистрации пользователя"""
        telegram_id = update.effective_user.id
        session = self.user_sessions[telegram_id]
        step = session["step"]
        registration_data = session["registration_data"]

        if step == "register_full_name":
            # Шаг 1: Полное имя
            if len(text.strip()) < 2:
                await update.message.reply_text("Пожалуйста, введите корректное полное имя (минимум 2 символа):")
                return

            registration_data["full_name"] = text.strip()
            session["step"] = "register_email"
            await update.message.reply_text(
                "📧 Шаг 2 из 4: Введите ваш email адрес\n"
                "(Этот email будет использоваться как логин для веб-версии):"
            )

        elif step == "register_email":
            # Шаг 2: Email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, text.strip()):
                await update.message.reply_text("Пожалуйста, введите корректный email адрес:")
                return

            # Проверяем, не занят ли email
            db = self._get_db_session()
            existing_user = db.query(User).filter(User.email == text.strip()).first()
            if existing_user:
                await update.message.reply_text("Этот email уже зарегистрирован. Введите другой email:")
                return

            registration_data["email"] = text.strip()
            session["step"] = "register_password"
            await update.message.reply_text(
                "🔒 Шаг 3 из 4: Придумайте пароль для веб-версии\n"
                "(Пароль должен содержать минимум 6 символов):"
            )

        elif step == "register_password":
            # Шаг 3: Пароль
            if len(text.strip()) < 6:
                await update.message.reply_text("Пароль должен содержать минимум 6 символов. Придумайте пароль:")
                return

            registration_data["password"] = text.strip()
            session["step"] = "register_date_of_birth"
            await update.message.reply_text(
                "📅 Шаг 4 из 4: Введите вашу дату рождения\n"
                "(Формат: ДД.ММ.ГГГГ, например: 15.05.1990):"
            )

        elif step == "register_date_of_birth":
            # Шаг 4: Дата рождения
            date_pattern = r'^\d{2}\.\d{2}\.\d{4}$'
            if not re.match(date_pattern, text.strip()):
                await update.message.reply_text("Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:")
                return

            try:
                day, month, year = map(int, text.strip().split('.'))
                date_of_birth = date(year, month, day)

                # Проверяем, что дата не в будущем и не слишком старая
                today = date.today()
                if date_of_birth >= today:
                    await update.message.reply_text("Дата рождения не может быть в будущем. Введите корректную дату:")
                    return
                if year < 1900:
                    await update.message.reply_text("Пожалуйста, введите реальную дату рождения:")
                    return

                registration_data["date_of_birth"] = date_of_birth

                # Все данные собраны, создаем пользователя
                await self._create_user_from_registration(update, registration_data)

            except ValueError:
                await update.message.reply_text("Некорректная дата. Введите дату в формате ДД.ММ.ГГГГ:")
                return

    async def _create_user_from_registration(self, update, registration_data):
        """Создание пользователя из данных регистрации"""
        telegram_id = update.effective_user.id

        db = self._get_db_session()

        try:
            # Создаем пользователя с предоставленными данными
            user = User(
                email=registration_data["email"],
                full_name=registration_data["full_name"],
                password_hash=hash_password(registration_data["password"]),
                date_of_birth=registration_data["date_of_birth"],
                role="employee",
                is_active=True,
                telegram_id=telegram_id,  # Сохраняем Telegram ID для связи
                web_username=registration_data["email"],  # Email как логин для веб
                web_password_plain=registration_data["password"]  # Сохраняем пароль в открытом виде
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            # Обновляем сессию
            self.user_sessions[telegram_id] = {"user_id": user.id, "step": "main_menu"}

            await update.message.reply_text(
                f"✅ Регистрация завершена!\n\n"
                f"Добро пожаловать, {registration_data['full_name']}!\n\n"
                f"🔑 Ваши учетные данные для веб-версии:\n"
                f"Логин: {registration_data['email']}\n"
                f"Пароль: {registration_data['password']}\n\n"
                "Сохраните эти данные для входа на сайт.\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user.id)
            )

        except IntegrityError:
            db.rollback()
            await update.message.reply_text("Ошибка: этот email уже зарегистрирован. Попробуйте другой email.")
        except Exception as e:
            db.rollback()
            await update.message.reply_text("Ошибка при регистрации. Попробуйте еще раз.")

    async def _handle_main_menu(self, update, text):
        """Обработка команд главного меню"""
        telegram_id = update.effective_user.id
        user_id = self.user_sessions[telegram_id]["user_id"]

        if text == "✅ Приход":
            await self._handle_checkin(update, user_id)
        elif text == "❌ Уход":
            await self._handle_checkout(update, user_id)
        elif text == "📊 Статус":
            await self._handle_status(update, user_id)
        else:
            await update.message.reply_text("Выберите действие из меню:")

    async def _handle_checkin(self, update, user_id):
        """Обработка прихода на работу"""
        db = self._get_db_session()
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            await update.message.reply_text("Пользователь не найден")
            return

        # Проверяем разрешение для отметки прихода
        is_allowed, message = self._check_telegram_user_allowed(user_id)
        if not is_allowed:
            await update.message.reply_text(
                f"❌ Доступ запрещен!\n\n{message}\n\n"
                "Обратитесь к администратору для решения проблемы.\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
            return

        # Если есть предупреждение, показываем его
        if "⚠️" in message:
            await update.message.reply_text(
                f"{message}\n\n"
                "Продолжаем выполнение действия...\n"
            )

        now = self._get_moscow_time()
        today = now.date()

        # Проверяем, есть ли запись на сегодня
        existing = db.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.work_date == today
        ).first()

        if existing:
            if existing.ended_at is None:
                # Уже есть активная смена на сегодня
                await update.message.reply_text(
                    f"У вас уже активная смена на сегодня!\n"
                    f"Начало: {existing.started_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                    "Используйте 'Я ушел' для завершения смены",
                    reply_markup=self._get_main_menu_keyboard(user_id)
                )
                return
            else:
                # Есть завершенная смена, начинаем новую смену в тот же день
                existing.started_at = now
                existing.ended_at = None
                # Не сбрасываем hours, чтобы суммировать время
                db.add(existing)
                db.commit()
                await update.message.reply_text(
                    f"✅ Приход зафиксирован!\n"
                    f"Время: {now.strftime('%d.%m.%Y %H:%M')}\n\n"
                    "Удачной работы!",
                    reply_markup=self._get_main_menu_keyboard(user_id)
                )
                return

        # Создаем новую запись на сегодня
        record = Attendance(
            user_id=user_id,
            started_at=now,
            work_date=today
        )

        try:
            db.add(record)
            db.commit()
            await update.message.reply_text(
                f"✅ Приход зафиксирован!\n"
                f"Время: {now.strftime('%d.%m.%Y %H:%M')}\n\n"
                "Удачной работы!",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
        except Exception as e:
            db.rollback()
            await update.message.reply_text("Ошибка при фиксации прихода")

    async def _handle_checkout(self, update, user_id):
        """Обработка ухода с работы"""
        db = self._get_db_session()

        # Проверяем разрешение для отметки ухода
        is_allowed, message = self._check_telegram_user_allowed(user_id)
        if not is_allowed:
            await update.message.reply_text(
                f"❌ Доступ запрещен!\n\n{message}\n\n"
                "Обратитесь к администратору для решения проблемы.\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
            return

        # Если есть предупреждение, показываем его
        if "⚠️" in message:
            await update.message.reply_text(
                f"{message}\n\n"
                "Продолжаем выполнение действия...\n"
            )

        now = self._get_moscow_time()
        today = now.date()

        # Находим активную смену на сегодня
        active = db.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.work_date == today,
            Attendance.ended_at.is_(None)
        ).first()

        if not active:
            await update.message.reply_text(
                "У вас нет активной смены на сегодня\n\n"
                "Используйте 'Я пришел' для начала смены",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
            return

        # Завершаем смену
        active.ended_at = now

        # Рассчитываем время работы для этой смены
        started_at = active.started_at
        if started_at.tzinfo is None:
            # Если время naive, предполагаем что оно в московском времени
            moscow_tz = timezone(timedelta(hours=3))
            started_at = started_at.replace(tzinfo=moscow_tz)

        elapsed_seconds = (now - started_at).total_seconds()
        current_hours = round(elapsed_seconds / 3600.0, 2)

        # Суммируем с предыдущим временем
        if active.hours:
            active.hours += current_hours
        else:
            active.hours = current_hours

        try:
            db.add(active)
            db.commit()

            hours = int(active.hours)
            minutes = int((active.hours - hours) * 60)

            await update.message.reply_text(
                f"❌ Уход зафиксирован!\n"
                f"Время: {now.strftime('%d.%m.%Y %H:%M')}\n"
                f"Отработано сегодня: {hours}ч {minutes}мин\n\n"
                "Хорошего отдыха!",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
        except Exception as e:
            db.rollback()
            await update.message.reply_text("Ошибка при фиксации ухода")

    async def _handle_status(self, update, user_id):
        """Показать текущий статус"""
        db = self._get_db_session()
        today = date.today()

        # Получаем активную смену на сегодня
        active = db.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.work_date == today,
            Attendance.ended_at.is_(None)
        ).first()

        if active:
            now = self._get_moscow_time()
            started_at = active.started_at
            if started_at.tzinfo is None:
                # Если время naive, предполагаем что оно в московском времени
                moscow_tz = timezone(timedelta(hours=3))
                started_at = started_at.replace(tzinfo=moscow_tz)

            elapsed_seconds = (now - started_at).total_seconds()
            hours = int(elapsed_seconds / 3600)
            minutes = int((elapsed_seconds % 3600) / 60)

            # Показываем общее время за день
            total_hours = active.hours or 0
            total_h = int(total_hours)
            total_m = int((total_hours - total_h) * 60)

            await update.message.reply_text(
                f"📊 Текущий статус:\n\n"
                f"🟢 На работе\n"
                f"Начало смены: {active.started_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"Отработано в этой смене: {hours}ч {minutes}мин\n"
                f"Всего за сегодня: {total_h}ч {total_m}мин",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
        else:
            # Проверяем, есть ли завершенная смена на сегодня
            completed = db.query(Attendance).filter(
                Attendance.user_id == user_id,
                Attendance.work_date == today,
                Attendance.ended_at.isnot(None)
            ).first()

            if completed:
                total_hours = completed.hours or 0
                total_h = int(total_hours)
                total_m = int((total_hours - total_h) * 60)
                await update.message.reply_text(
                    f"📊 Текущий статус:\n\n"
                    f"🔴 Не на работе\n"
                    f"Отработано сегодня: {total_h}ч {total_m}мин\n\n"
                    "Используйте кнопку 'Я пришел' для начала новой смены",
                    reply_markup=self._get_main_menu_keyboard(user_id)
                )
            else:
                await update.message.reply_text(
                    f"📊 Текущий статус:\n\n"
                    f"🔴 Не на работе\n\n"
                    "Используйте кнопку 'Я пришел' для начала смены",
                    reply_markup=self._get_main_menu_keyboard(user_id)
                )

    def _get_main_menu_keyboard(self, user_id=None):
        """Создает клавиатуру главного меню в зависимости от статуса пользователя"""
        if user_id:
            # Проверяем, есть ли активная смена на сегодня
            db = self._get_db_session()
            today = date.today()
            active = db.query(Attendance).filter(
                Attendance.user_id == user_id,
                Attendance.work_date == today,
                Attendance.ended_at.is_(None)
            ).first()

            if active:
                # Пользователь на работе - показываем "я ушел" и "статус"
                keyboard = [
                    [InlineKeyboardButton("❌ Я ушел", callback_data="checkout")],
                    [InlineKeyboardButton("📊 Статус", callback_data="status")],
                    [InlineKeyboardButton("🔑 Логин/Пароль", callback_data="show_credentials")]
                ]
            else:
                # Пользователь не на работе - показываем "я пришел" и "статус"
                keyboard = [
                    [InlineKeyboardButton("✅ Я пришел", callback_data="checkin")],
                    [InlineKeyboardButton("📊 Статус", callback_data="status")],
                    [InlineKeyboardButton("🔑 Логин/Пароль", callback_data="show_credentials")]
                ]
        else:
            # По умолчанию показываем "я пришел" и "статус"
            keyboard = [
                [InlineKeyboardButton("✅ Я пришел", callback_data="checkin")],
                [InlineKeyboardButton("📊 Статус", callback_data="status")],
                [InlineKeyboardButton("🔑 Логин/Пароль", callback_data="show_credentials")]
            ]

        return InlineKeyboardMarkup(keyboard)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()

        telegram_id = query.from_user.id
        if telegram_id not in self.user_sessions:
            await query.edit_message_text("Сессия истекла. Используйте /start")
            return

        user_id = self.user_sessions[telegram_id]["user_id"]
        action = query.data

        if action == "checkin":
            await self._handle_checkin_via_callback(query, user_id)
        elif action == "checkout":
            await self._handle_checkout_via_callback(query, user_id)
        elif action == "status":
            await self._handle_status_via_callback(query, user_id)
        elif action == "show_credentials":
            await self._handle_show_credentials_via_callback(query, user_id)

    async def _handle_checkin_via_callback(self, query, user_id):
        """Обработка прихода через callback"""
        db = self._get_db_session()
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            await query.edit_message_text("Пользователь не найден")
            return

        # Проверяем разрешение для отметки прихода
        is_allowed, message = self._check_telegram_user_allowed(user_id)
        if not is_allowed:
            await query.edit_message_text(
                f"❌ Доступ запрещен!\n\n{message}\n\n"
                "Обратитесь к администратору для решения проблемы.\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
            return

        # Если есть предупреждение, показываем его
        if "⚠️" in message:
            await query.edit_message_text(
                f"{message}\n\n"
                "Продолжаем выполнение действия...\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
            return

        now = self._get_moscow_time()
        today = now.date()

        # Проверяем, есть ли запись на сегодня
        existing = db.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.work_date == today
        ).first()

        if existing:
            if existing.ended_at is None:
                # Уже есть активная смена на сегодня
                await query.edit_message_text(
                    f"У вас уже активная смена на сегодня!\n"
                    f"Начало: {existing.started_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                    "Используйте 'Я ушел' для завершения смены\n\n"
                    "Выберите действие:",
                    reply_markup=self._get_main_menu_keyboard(user_id)
                )
                return
            else:
                # Есть завершенная смена, начинаем новую смену в тот же день
                existing.started_at = now
                existing.ended_at = None
                # Не сбрасываем hours, чтобы суммировать время
                db.add(existing)
                db.commit()
                try:
                    await query.edit_message_text(
                        f"✅ Приход зафиксирован!\n"
                        f"Время: {now.strftime('%d.%m.%Y %H:%M')}\n\n"
                        "Удачной работы!\n\n"
                        "Выберите действие:",
                        reply_markup=self._get_main_menu_keyboard(user_id)
                    )
                except Exception as e:
                    if "Message is not modified" in str(e):
                        await query.answer("Приход уже зафиксирован")
                    else:
                        await query.answer("Ошибка при фиксации прихода")
                return

        # Создаем новую запись на сегодня
        record = Attendance(
            user_id=user_id,
            started_at=now,
            work_date=today
        )

        try:
            db.add(record)
            db.commit()
            try:
                await query.edit_message_text(
                    f"✅ Приход зафиксирован!\n"
                    f"Время: {now.strftime('%d.%m.%Y %H:%M')}\n\n"
                    "Удачной работы!\n\n"
                    "Выберите действие:",
                    reply_markup=self._get_main_menu_keyboard(user_id)
                )
            except Exception as e:
                if "Message is not modified" in str(e):
                    await query.answer("Приход уже зафиксирован")
                else:
                    await query.answer("Ошибка при фиксации прихода")
        except Exception as e:
            db.rollback()
            await query.answer("Ошибка при фиксации прихода")

    async def _handle_checkout_via_callback(self, query, user_id):
        """Обработка ухода через callback"""
        db = self._get_db_session()

        # Проверяем разрешение для отметки ухода
        is_allowed, message = self._check_telegram_user_allowed(user_id)
        if not is_allowed:
            await query.edit_message_text(
                f"❌ Доступ запрещен!\n\n{message}\n\n"
                "Обратитесь к администратору для решения проблемы.\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
            return

        # Если есть предупреждение, показываем его
        if "⚠️" in message:
            await query.edit_message_text(
                f"{message}\n\n"
                "Продолжаем выполнение действия...\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
            return

        now = self._get_moscow_time()
        today = now.date()

        # Находим активную смену на сегодня
        active = db.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.work_date == today,
            Attendance.ended_at.is_(None)
        ).first()

        if not active:
            await query.edit_message_text(
                "У вас нет активной смены на сегодня\n\n"
                "Используйте 'Я пришел' для начала смены\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
            return

        # Завершаем смену
        active.ended_at = now

        # Рассчитываем время работы для этой смены
        started_at = active.started_at
        if started_at.tzinfo is None:
            # Если время naive, предполагаем что оно в московском времени
            moscow_tz = timezone(timedelta(hours=3))
            started_at = started_at.replace(tzinfo=moscow_tz)

        elapsed_seconds = (now - started_at).total_seconds()
        current_hours = round(elapsed_seconds / 3600.0, 2)

        # Суммируем с предыдущим временем
        if active.hours:
            active.hours += current_hours
        else:
            active.hours = current_hours

        try:
            db.add(active)
            db.commit()

            hours = int(active.hours)
            minutes = int((active.hours - hours) * 60)

            try:
                await query.edit_message_text(
                    f"❌ Уход зафиксирован!\n"
                    f"Время: {now.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Отработано сегодня: {hours}ч {minutes}мин\n\n"
                    "Хорошего отдыха!\n\n"
                    "Выберите действие:",
                    reply_markup=self._get_main_menu_keyboard(user_id)
                )
            except Exception as e:
                if "Message is not modified" in str(e):
                    await query.answer("Уход уже зафиксирован")
                else:
                    await query.answer("Ошибка при фиксации ухода")
        except Exception as e:
            db.rollback()
            await query.answer("Ошибка при фиксации ухода")

    async def _handle_status_via_callback(self, query, user_id):
        """Показать статус через callback"""
        db = self._get_db_session()
        today = date.today()

        # Получаем активную смену на сегодня
        active = db.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.work_date == today,
            Attendance.ended_at.is_(None)
        ).first()

        if active:
            now = self._get_moscow_time()
            started_at = active.started_at
            if started_at.tzinfo is None:
                # Если время naive, предполагаем что оно в московском времени
                moscow_tz = timezone(timedelta(hours=3))
                started_at = started_at.replace(tzinfo=moscow_tz)

            elapsed_seconds = (now - started_at).total_seconds()
            hours = int(elapsed_seconds / 3600)
            minutes = int((elapsed_seconds % 3600) / 60)

            # Показываем общее время за день
            total_hours = active.hours or 0
            total_h = int(total_hours)
            total_m = int((total_hours - total_h) * 60)

            try:
                await query.edit_message_text(
                    f"📊 Текущий статус:\n\n"
                    f"🟢 На работе\n"
                    f"Начало смены: {active.started_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Отработано в этой смене: {hours}ч {minutes}мин\n"
                    f"Всего за сегодня: {total_h}ч {total_m}мин\n\n"
                    "Выберите действие:",
                    reply_markup=self._get_main_menu_keyboard(user_id)
                )
            except Exception as e:
                # Если сообщение не изменилось, просто отвечаем
                if "Message is not modified" in str(e):
                    await query.answer("Статус не изменился")
                else:
                    await query.answer("Ошибка при обновлении статуса")
        else:
            # Проверяем, есть ли завершенная смена на сегодня
            completed = db.query(Attendance).filter(
                Attendance.user_id == user_id,
                Attendance.work_date == today,
                Attendance.ended_at.isnot(None)
            ).first()

            if completed:
                total_hours = completed.hours or 0
                total_h = int(total_hours)
                total_m = int((total_hours - total_h) * 60)
                try:
                    await query.edit_message_text(
                        f"📊 Текущий статус:\n\n"
                        f"🔴 Не на работе\n"
                        f"Отработано сегодня: {total_h}ч {total_m}мин\n\n"
                        "Используйте кнопку 'Я пришел' для начала новой смены\n\n"
                        "Выберите действие:",
                        reply_markup=self._get_main_menu_keyboard(user_id)
                    )
                except Exception as e:
                    if "Message is not modified" in str(e):
                        await query.answer("Статус не изменился")
                    else:
                        await query.answer("Ошибка при обновлении статуса")
            else:
                try:
                    await query.edit_message_text(
                        f"📊 Текущий статус:\n\n"
                        f"🔴 Не на работе\n\n"
                        "Используйте кнопку 'Я пришел' для начала смены\n\n"
                        "Выберите действие:",
                        reply_markup=self._get_main_menu_keyboard(user_id)
                    )
                except Exception as e:
                    if "Message is not modified" in str(e):
                        await query.answer("Статус не изменился")
                    else:
                        await query.answer("Ошибка при обновлении статуса")

    async def _handle_show_credentials_via_callback(self, query, user_id):
        """Показать логин и пароль для веб-версии через callback"""
        db = self._get_db_session()
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            await query.edit_message_text("Пользователь не найден")
            return

        # Используем сохраненные учетные данные
        if not user.web_username or not user.web_password_plain:
            await query.edit_message_text(
                "Учетные данные для веб-версии не найдены.\n"
                "Возможно, аккаунт был создан до обновления системы.\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
            return

        try:
            await query.edit_message_text(
                f"🔑 Ваши учетные данные для веб-версии:\n\n"
                f"Логин: {user.web_username}\n"
                f"Пароль: {user.web_password_plain}\n\n"
                "Используйте эти данные для входа на сайт.\n\n"
                "Выберите действие:",
                reply_markup=self._get_main_menu_keyboard(user_id)
            )
        except Exception as e:
            if "Message is not modified" in str(e):
                await query.answer("Учетные данные уже показаны")
            else:
                await query.answer("Ошибка при показе учетных данных")

    def setup_bot(self, token: str):
        """Настройка и запуск бота"""
        self.application = Application.builder().token(token).build()

        # Добавляем обработчики
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("register", self.register_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

    async def run_bot(self):
        """Запуск бота"""
        if self.application:
            await self.application.run_polling()
        else:
            raise ValueError("Bot not set up. Call setup_bot() first")

    def run_sync(self):
        """Синхронный запуск бота"""
        if self.application:
            self.application.run_polling()
        else:
            raise ValueError("Bot not set up. Call setup_bot() first")


# Глобальный экземпляр бота
telegram_bot = TelegramBot()