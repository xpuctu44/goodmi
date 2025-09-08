from datetime import date, datetime, time
from typing import List

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, ScheduleEntry, Store


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


def _admin_guard(request: Request, db: Session) -> User | None:
    user = _current_user(request, db)
    if not user:
        return None
    if user.role != "admin":
        return None
    return user


def _ensure_admin(request: Request, db: Session):
    user = _admin_guard(request, db)
    if not user:
        if not request.session.get("user_id"):
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return user


@router.get("/admin", include_in_schema=False)
def admin_root(request: Request, db: Session = Depends(get_db)):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    # Получаем статистику
    total_users = db.query(User).filter(User.is_active == True).count()
    total_employees = db.query(User).filter(User.role == "employee", User.is_active == True).count()
    total_admins = db.query(User).filter(User.role == "admin", User.is_active == True).count()
    total_stores = db.query(Store).count()
    today_schedules = db.query(ScheduleEntry).filter(ScheduleEntry.work_date == date.today()).count()
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request, 
            "title": "Админ — панель", 
            "active_tab": "dashboard",
            "message": "Добро пожаловать в админ панель!",
            "employees": [],
            "stats": {
                "total_users": total_users,
                "total_employees": total_employees,
                "total_admins": total_admins,
                "total_stores": total_stores,
                "today_schedules": today_schedules
            }
        },
    )


@router.get("/admin/planning", include_in_schema=False)
def admin_planning(request: Request, db: Session = Depends(get_db)):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    try:
        # Получаем всех пользователей (сотрудников и администраторов)
        employees = db.query(User).filter(User.is_active == True).all()
        
        # Получаем все магазины
        stores = db.query(Store).all()
        
        # Получаем текущие записи расписания
        current_schedules = db.query(ScheduleEntry).filter(
            ScheduleEntry.work_date >= date.today()
        ).order_by(ScheduleEntry.work_date, ScheduleEntry.start_time).all()
        
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        employees = []
        stores = []
        current_schedules = []
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "title": "Админ — планирование",
            "active_tab": "planning",
            "employees": employees,
            "stores": stores,
            "current_schedules": current_schedules,
            "message": "Создание и управление графиками смен",
        },
    )


@router.post("/admin/planning/create", include_in_schema=False)
def create_schedule(
    request: Request,
    employee_id: int = Form(...),
    work_date: date = Form(...),
    start_time: time = Form(...),
    end_time: time = Form(...),
    store_id: int = Form(None),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    try:
        # Проверяем, что пользователь существует
        employee = db.query(User).filter(User.id == employee_id, User.is_active == True).first()
        if not employee:
            return RedirectResponse(url="/admin/planning?error=employee_not_found", status_code=status.HTTP_303_SEE_OTHER)
        
        # Проверяем, что время корректное
        if start_time >= end_time:
            return RedirectResponse(url="/admin/planning?error=invalid_time", status_code=status.HTTP_303_SEE_OTHER)
        
        # Проверяем, что нет конфликта с существующими сменами
        existing = db.query(ScheduleEntry).filter(
            ScheduleEntry.user_id == employee_id,
            ScheduleEntry.work_date == work_date,
            ScheduleEntry.start_time < end_time,
            ScheduleEntry.end_time > start_time
        ).first()
        
        if existing:
            return RedirectResponse(url="/admin/planning?error=conflict", status_code=status.HTTP_303_SEE_OTHER)
        
        # Создаем новую запись расписания
        schedule = ScheduleEntry(
            user_id=employee_id,
            work_date=work_date,
            start_time=start_time,
            end_time=end_time,
            store_id=store_id,
            notes=notes
        )
        
        db.add(schedule)
        db.commit()
        
        return RedirectResponse(url="/admin/planning?success=created", status_code=status.HTTP_303_SEE_OTHER)
        
    except Exception as e:
        print(f"Ошибка при создании расписания: {e}")
        return RedirectResponse(url="/admin/planning?error=server_error", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/planning/delete/{schedule_id}", include_in_schema=False)
def delete_schedule(schedule_id: int, request: Request, db: Session = Depends(get_db)):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    try:
        schedule = db.query(ScheduleEntry).filter(ScheduleEntry.id == schedule_id).first()
        if schedule:
            db.delete(schedule)
            db.commit()
        
        return RedirectResponse(url="/admin/planning?success=deleted", status_code=status.HTTP_303_SEE_OTHER)
        
    except Exception as e:
        print(f"Ошибка при удалении расписания: {e}")
        return RedirectResponse(url="/admin/planning?error=delete_error", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/schedule", include_in_schema=False)
def admin_schedule(request: Request, db: Session = Depends(get_db)):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    try:
        # Получаем все записи расписания
        schedules = db.query(ScheduleEntry).join(User).filter(
            ScheduleEntry.work_date >= date.today()
        ).order_by(ScheduleEntry.work_date, ScheduleEntry.start_time).all()
        
        # Группируем по датам
        schedule_by_date = {}
        for schedule in schedules:
            date_key = schedule.work_date.strftime("%Y-%m-%d")
            if date_key not in schedule_by_date:
                schedule_by_date[date_key] = []
            schedule_by_date[date_key].append(schedule)
        
    except Exception as e:
        print(f"Ошибка при получении расписания: {e}")
        schedules = []
        schedule_by_date = {}
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "title": "Админ — график",
            "active_tab": "schedule",
            "schedules": schedules,
            "schedule_by_date": schedule_by_date,
            "message": "Просмотр текущих графиков и расписаний",
        },
    )


@router.get("/admin/reports", include_in_schema=False)
def admin_reports(request: Request, db: Session = Depends(get_db)):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    try:
        # Получаем статистику по всем пользователям
        employees = db.query(User).filter(User.is_active == True).all()
        
        # Получаем статистику по расписанию
        total_schedules = db.query(ScheduleEntry).count()
        this_week_schedules = db.query(ScheduleEntry).filter(
            ScheduleEntry.work_date >= date.today(),
            ScheduleEntry.work_date <= date.today().replace(day=date.today().day + 7)
        ).count()
        
    except Exception as e:
        print(f"Ошибка при получении отчетов: {e}")
        employees = []
        total_schedules = 0
        this_week_schedules = 0
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "title": "Админ — отчеты",
            "active_tab": "reports",
            "employees": employees,
            "stats": {
                "total_schedules": total_schedules,
                "this_week_schedules": this_week_schedules
            },
            "message": "Аналитика и отчеты по рабочему времени",
        },
    )


@router.get("/admin/stores", include_in_schema=False)
def admin_stores(request: Request, db: Session = Depends(get_db)):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    try:
        # Получаем все магазины
        stores = db.query(Store).all()
        
    except Exception as e:
        print(f"Ошибка при получении магазинов: {e}")
        stores = []
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "title": "Админ — магазины",
            "active_tab": "stores",
            "stores": stores,
            "message": "Управление магазинами и филиалами",
        },
    )


@router.get("/admin/employees", include_in_schema=False)
def admin_employees(request: Request, db: Session = Depends(get_db)):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    try:
        # Получаем всех пользователей
        employees = db.query(User).filter(User.is_active == True).all()
        
        # Получаем все магазины
        stores = db.query(Store).all()
        
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        employees = []
        stores = []
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "title": "Админ — сотрудники",
            "active_tab": "employees",
            "employees": employees,
            "stores": stores,
            "message": "Управление сотрудниками и назначение магазинов",
        },
    )


@router.post("/admin/employees/assign-store", include_in_schema=False)
def assign_store_to_employee(
    request: Request,
    employee_id: int = Form(...),
    store_id: int = Form(None),
    db: Session = Depends(get_db)
):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    try:
        # Находим сотрудника
        employee = db.query(User).filter(User.id == employee_id).first()
        if not employee:
            return RedirectResponse(url="/admin/employees?error=employee_not_found", status_code=status.HTTP_303_SEE_OTHER)
        
        # Назначаем магазин (может быть None для снятия назначения)
        employee.store_id = store_id if store_id else None
        db.commit()
        
        return RedirectResponse(url="/admin/employees?success=store_assigned", status_code=status.HTTP_303_SEE_OTHER)
        
    except Exception as e:
        print(f"Ошибка при назначении магазина: {e}")
        return RedirectResponse(url="/admin/employees?error=server_error", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/employees/toggle-status", include_in_schema=False)
def toggle_employee_status(
    request: Request,
    employee_id: int = Form(...),
    db: Session = Depends(get_db)
):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    try:
        # Находим сотрудника
        employee = db.query(User).filter(User.id == employee_id).first()
        if not employee:
            return RedirectResponse(url="/admin/employees?error=employee_not_found", status_code=status.HTTP_303_SEE_OTHER)
        
        # Переключаем статус
        employee.is_active = not employee.is_active
        db.commit()
        
        return RedirectResponse(url="/admin/employees?success=status_changed", status_code=status.HTTP_303_SEE_OTHER)
        
    except Exception as e:
        print(f"Ошибка при изменении статуса: {e}")
        return RedirectResponse(url="/admin/employees?error=server_error", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/stores/create", include_in_schema=False)
def create_store(
    request: Request,
    name: str = Form(...),
    address: str = Form(""),
    phone: str = Form(""),
    db: Session = Depends(get_db)
):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    try:
        store = Store(
            name=name,
            address=address,
            phone=phone
        )
        
        db.add(store)
        db.commit()
        
        return RedirectResponse(url="/admin/stores?success=created", status_code=status.HTTP_303_SEE_OTHER)
        
    except Exception as e:
        print(f"Ошибка при создании магазина: {e}")
        return RedirectResponse(url="/admin/stores?error=server_error", status_code=status.HTTP_303_SEE_OTHER)
