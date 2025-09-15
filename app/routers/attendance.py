from datetime import datetime, date, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Attendance, User, AllowedIP, ScheduleEntry, Store
from fastapi.responses import StreamingResponse
import io


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_current_user(request: Request, db: Session) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


def _get_client_ip(request: Request) -> str:
    """Получает реальный IP адрес клиента, учитывая прокси"""
    # Сначала проверяем заголовок X-Forwarded-For (для прокси)
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # Берем первый IP из списка (реальный клиент)
        client_ip = x_forwarded_for.split(",")[0].strip()
    else:
        # Используем прямой IP от клиента
        client_ip = request.client.host

    return client_ip


def _get_moscow_time() -> datetime:
    """Получает текущее время в московском часовом поясе (UTC+3)"""
    moscow_tz = timezone(timedelta(hours=3))
    return datetime.now(moscow_tz)


def _to_moscow_time(moscow_time: datetime) -> datetime:
    """Обеспечивает, что время в московском часовом поясе для отображения"""
    if moscow_time is None:
        return None
    moscow_tz = timezone(timedelta(hours=3))
    if moscow_time.tzinfo is None:
        # Assume it's already Moscow time if no timezone info
        return moscow_time.replace(tzinfo=moscow_tz)
    return moscow_time.astimezone(moscow_tz)


def _calculate_total_work_time_today(user_id: int, db: Session, current_time: datetime = None) -> float:
    """Подсчитывает общее время работы за сегодня, включая активную сессию"""
    if current_time is None:
        current_time = _get_moscow_time()

    # Ensure current_time is in Moscow timezone
    current_time = _to_moscow_time(current_time)
    today = current_time.date()
    total_work_seconds = 0

    # Get all attendance records for today
    today_records = (
        db.query(Attendance)
        .filter(
            Attendance.user_id == user_id,
            Attendance.work_date == today
        )
        .order_by(Attendance.started_at)
        .all()
    )

    # Calculate total time from all completed sessions
    for record in today_records:
        if record.ended_at is not None:
            # This session is completed, add its duration
            started_at = _to_moscow_time(record.started_at)
            ended_at = _to_moscow_time(record.ended_at)

            session_seconds = (ended_at - started_at).total_seconds()
            total_work_seconds += session_seconds
        else:
            # This is the active session, add time from start to now
            started_at = _to_moscow_time(record.started_at)

            current_session_seconds = (current_time - started_at).total_seconds()
            total_work_seconds += current_session_seconds

    return total_work_seconds / 3600.0  # Convert to hours


def _check_ip_allowed(request: Request, db: Session) -> bool:
    """Проверяет, разрешен ли IP адрес для отметки прихода/ухода"""
    # Получаем IP адрес клиента
    client_ip = _get_client_ip(request)

    # Если нет разрешенных IP, разрешаем всем
    allowed_ips = db.query(AllowedIP).filter(AllowedIP.is_active == True).all()
    if not allowed_ips:
        return True

    # Проверяем первые 3 октета IP (например, 192.168.1.x)
    client_parts = client_ip.split('.')
    if len(client_parts) != 4:
        return False

    client_prefix = '.'.join(client_parts[:3])  # Получаем первые 3 октета

    # Проверяем, есть ли совпадение с разрешенными IP
    for allowed_ip in allowed_ips:
        allowed_parts = allowed_ip.ip_address.split('.')
        if len(allowed_parts) >= 3:
            allowed_prefix = '.'.join(allowed_parts[:3])
            if client_prefix == allowed_prefix:
                return True

    return False


@router.get("/dashboard", include_in_schema=False)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Only employee flow shows single toggle button
    active = (
        db.query(Attendance)
        .filter(Attendance.user_id == user.id, Attendance.ended_at.is_(None))
        .first()
    )

    # Get current month schedule for employees
    employee_schedule = []
    calendar_data = []
    # Coworkers schedule (same store)
    coworkers = []
    month_dates = []
    coworker_schedule_map = {}
    employee_store = None
    if user.role == "employee":
        now = _get_moscow_time()
        current_year = now.year
        current_month = now.month

        # Calculate first and last day of current month
        from calendar import monthrange, monthcalendar
        first_day = date(current_year, current_month, 1)
        last_day_of_month = monthrange(current_year, current_month)[1]
        last_day = date(current_year, current_month, last_day_of_month)

        # Get published schedule entries for the current month (current user)
        employee_schedule = (
            db.query(ScheduleEntry)
            .filter(
                ScheduleEntry.user_id == user.id,
                ScheduleEntry.work_date >= first_day,
                ScheduleEntry.work_date <= last_day,
                ScheduleEntry.published == True
            )
            .order_by(ScheduleEntry.work_date)
            .all()
        )

        # Get attendance records for the current month
        attendance_records = (
            db.query(Attendance)
            .filter(
                Attendance.user_id == user.id,
                Attendance.work_date >= first_day,
                Attendance.work_date <= last_day,
                Attendance.ended_at.isnot(None)  # Only completed sessions
            )
            .order_by(Attendance.work_date, Attendance.started_at)
            .all()
        )

        # Create calendar data structure
        import calendar
        cal = monthcalendar(current_year, current_month)

        # Russian day names
        russian_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

        # Create schedule dictionary for quick lookup
        schedule_dict = {entry.work_date: entry for entry in employee_schedule}

        # Create attendance dictionary for quick lookup
        # Group attendance records by date
        attendance_dict = {}
        for attendance in attendance_records:
            day_date = attendance.work_date
            if day_date not in attendance_dict:
                attendance_dict[day_date] = []
            attendance_dict[day_date].append(attendance)

        # Build calendar weeks
        calendar_data = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    # Empty cell for days not in this month
                    week_data.append({'day': '', 'schedule': None, 'attendance': [], 'is_empty': True})
                else:
                    day_date = date(current_year, current_month, day)
                    schedule_entry = schedule_dict.get(day_date)
                    day_attendance = attendance_dict.get(day_date, [])
                    
                    # Convert attendance times to Moscow timezone for display
                    moscow_attendance = []
                    for attendance in day_attendance:
                        # Create a copy-like object with Moscow times
                        moscow_att = type('AttendanceDisplay', (), {
                            'started_at': _to_moscow_time(attendance.started_at),
                            'ended_at': _to_moscow_time(attendance.ended_at),
                            'hours': attendance.hours
                        })()
                        moscow_attendance.append(moscow_att)
                    
                    week_data.append({
                        'day': day,
                        'date': day_date,
                        'schedule': schedule_entry,
                        'attendance': moscow_attendance,
                        'is_empty': False,
                        'is_today': day_date == now.date()
                    })
            calendar_data.append(week_data)

        # Coworkers schedule for the same store
        if user.store_id:
            employee_store = db.get(Store, user.store_id)
            # Month dates list for table
            month_dates = [date(current_year, current_month, d) for d in range(1, last_day_of_month + 1)]

            coworkers = (
                db.query(User)
                .filter(
                    User.is_active == True,
                    User.role == 'employee',
                    User.store_id == user.store_id,
                )
                .order_by(User.full_name, User.email)
                .all()
            )

            if coworkers:
                # Fetch all published entries for coworkers in one query
                coworker_entries = (
                    db.query(ScheduleEntry)
                    .filter(
                        ScheduleEntry.user_id.in_([c.id for c in coworkers]),
                        ScheduleEntry.work_date >= first_day,
                        ScheduleEntry.work_date <= last_day,
                        ScheduleEntry.published == True,
                    )
                    .all()
                )

                # Build map: (user_id, work_date) -> entry
                for entry in coworker_entries:
                    coworker_schedule_map[(entry.user_id, entry.work_date)] = entry

    # Calculate total work time for today
    total_work_hours_today = 0
    if user.role == "employee":
        total_work_hours_today = _calculate_total_work_time_today(user.id, db)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Dashboard",
            "user": user,
            "is_active": bool(active),
            "start_time": _to_moscow_time(active.started_at) if active else None,  # Moscow time for display
            "start_time_moscow": active.started_at if active else None,  # Moscow time for JavaScript
            "total_work_hours_today": total_work_hours_today,
            "employee_schedule": employee_schedule,
            "calendar_data": calendar_data,
            "russian_days": ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'] if user.role == "employee" else [],
            # Coworkers schedule context
            "coworkers": coworkers,
            "employee_store": employee_store,
            "month_dates": month_dates,
            "coworker_schedule_map": coworker_schedule_map,
        },
    )


@router.post("/attendance/start", include_in_schema=False)
def start_attendance(request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Проверяем IP адрес
    if not _check_ip_allowed(request, db):
        return RedirectResponse(url="/dashboard?error=ip_not_allowed", status_code=status.HTTP_303_SEE_OTHER)

    now = _get_moscow_time()
    today = now.date()

    # If already started today, just redirect
    existing_active = (
        db.query(Attendance)
        .filter(Attendance.user_id == user.id, Attendance.ended_at.is_(None))
        .first()
    )
    if existing_active:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    # Check if there's a completed record for today that we can continue
    existing_today = (
        db.query(Attendance)
        .filter(
            Attendance.user_id == user.id, 
            Attendance.work_date == today,
            Attendance.ended_at.isnot(None)
        )
        .order_by(Attendance.ended_at.desc())
        .first()
    )

    if existing_today:
        # Continue the previous timer by creating a new session
        # We don't modify the existing record, we create a new one
        record = Attendance(
            user_id=user.id,
            started_at=now,
            work_date=today,
        )
        db.add(record)
    else:
        # Create new record
        record = Attendance(
            user_id=user.id,
            started_at=now,
            work_date=today,
        )
        db.add(record)
    
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


# QR-based attendance: user scans QR that encodes a URL like /q/start/{token}
@router.get("/q/start/{token}", include_in_schema=False)
def qr_start(token: str, request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    store = db.query(Store).filter(Store.qr_token == token, Store.is_active == True).first()
    if not store:
        return RedirectResponse(url="/dashboard?error=qr_invalid", status_code=status.HTTP_303_SEE_OTHER)

    # Optional: ensure user belongs to the store if assigned
    if user.store_id and user.store_id != store.id:
        return RedirectResponse(url="/dashboard?error=qr_wrong_store", status_code=status.HTTP_303_SEE_OTHER)

    # Start attendance (QR bypasses IP check as presence proof)
    existing = (
        db.query(Attendance)
        .filter(Attendance.user_id == user.id, Attendance.ended_at.is_(None))
        .first()
    )
    if existing:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    now = _get_moscow_time()
    record = Attendance(
        user_id=user.id,
        started_at=now,
        work_date=now.date(),
    )
    db.add(record)
    db.commit()
    return RedirectResponse(url="/dashboard?ok=started", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/q/stop/{token}", include_in_schema=False)
def qr_stop(token: str, request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    store = db.query(Store).filter(Store.qr_token == token, Store.is_active == True).first()
    if not store:
        return RedirectResponse(url="/dashboard?error=qr_invalid", status_code=status.HTTP_303_SEE_OTHER)

    if user.store_id and user.store_id != store.id:
        return RedirectResponse(url="/dashboard?error=qr_wrong_store", status_code=status.HTTP_303_SEE_OTHER)

    active = (
        db.query(Attendance)
        .filter(Attendance.user_id == user.id, Attendance.ended_at.is_(None))
        .first()
    )
    if not active:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    now = _get_moscow_time()
    active.ended_at = now

    started_at = active.started_at
    ended_at = active.ended_at
    if started_at.tzinfo is None:
        utc_tz = timezone.utc
        started_at = started_at.replace(tzinfo=utc_tz)
    elapsed_seconds = (ended_at - started_at).total_seconds()
    active.hours = round(elapsed_seconds / 3600.0, 4)
    db.add(active)
    db.commit()
    return RedirectResponse(url="/dashboard?ok=stopped", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/attendance/stop", include_in_schema=False)
def stop_attendance(request: Request, db: Session = Depends(get_db)):
    user = _get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Проверяем IP адрес
    if not _check_ip_allowed(request, db):
        return RedirectResponse(url="/dashboard?error=ip_not_allowed", status_code=status.HTTP_303_SEE_OTHER)

    active = (
        db.query(Attendance)
        .filter(Attendance.user_id == user.id, Attendance.ended_at.is_(None))
        .first()
    )
    if not active:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    now = _get_moscow_time()
    today = now.date()
    
    # Calculate total work time for today including all previous sessions
    total_work_seconds = 0
    
    # Get all attendance records for today
    today_records = (
        db.query(Attendance)
        .filter(
            Attendance.user_id == user.id,
            Attendance.work_date == today
        )
        .order_by(Attendance.started_at)
        .all()
    )
    
    # Calculate total time from all completed sessions
    for record in today_records:
        if record.ended_at is not None:
            # This session is completed, add its duration
            started_at = record.started_at
            ended_at = record.ended_at
            
            # Handle timezone-aware and naive datetimes
            if started_at.tzinfo is None:
                utc_tz = timezone.utc
                started_at = started_at.replace(tzinfo=utc_tz)
            if ended_at.tzinfo is None:
                utc_tz = timezone.utc
                ended_at = ended_at.replace(tzinfo=utc_tz)
                
            session_seconds = (ended_at - started_at).total_seconds()
            total_work_seconds += session_seconds
    
    # Add current session time
    current_started_at = active.started_at
    if current_started_at.tzinfo is None:
        utc_tz = timezone.utc
        current_started_at = current_started_at.replace(tzinfo=utc_tz)
    
    current_session_seconds = (now - current_started_at).total_seconds()
    total_work_seconds += current_session_seconds
    
    # Update the current record
    active.ended_at = now
    active.hours = round(total_work_seconds / 3600.0, 4)
    
    db.add(active)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
