from datetime import date, datetime
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

@router.get("/admin/planning", include_in_schema=False)
def admin_planning_fixed(request: Request, db: Session = Depends(get_db)):
    result = _ensure_admin(request, db)
    if isinstance(result, RedirectResponse):
        return result
    
    # Получаем текущий месяц
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # Инициализируем переменные
    employees = []
    stores = []
    current_schedules = []
    entry_map = {}
    
    try:
        # Получаем всех пользователей
        employees = db.query(User).filter(User.is_active == True).all()
        print(f"Найдено пользователей: {len(employees)}")
    except Exception as e:
        print(f"Ошибка при получении пользователей: {e}")
    
    try:
        # Получаем все магазины
        stores = db.query(Store).all()
        print(f"Найдено магазинов: {len(stores)}")
    except Exception as e:
        print(f"Ошибка при получении магазинов: {e}")
    
    try:
        # Получаем все записи расписания для текущего месяца
        current_schedules = db.query(ScheduleEntry).filter(
            ScheduleEntry.work_date >= date(current_year, current_month, 1),
            ScheduleEntry.work_date < date(current_year, current_month + 1, 1) if current_month < 12 else date(current_year + 1, 1, 1)
        ).all()
        print(f"Найдено записей расписания: {len(current_schedules)}")
    except Exception as e:
        print(f"Ошибка при получении расписания: {e}")
    
    try:
        # Создаем карту записей для быстрого поиска
        for schedule in current_schedules:
            key = f"{schedule.user_id}_{schedule.work_date.strftime('%Y-%m-%d')}"
            entry_map[key] = schedule
        print(f"Создана карта записей: {len(entry_map)}")
    except Exception as e:
        print(f"Ошибка при создании карты записей: {e}")
    
    return templates.TemplateResponse(
        "admin_fixed.html",
        {
            "request": request,
            "title": "Админ — планирование",
            "active_tab": "planning",
            "employees": employees,
            "stores": stores,
            "current_schedules": current_schedules,
            "entry_map": entry_map,
            "current_month": current_month,
            "current_year": current_year,
            "message": "Исправленное планирование смен",
            "date": date,
        },
    )

@router.post("/admin/planning/save", include_in_schema=False)
def save_schedule_fixed(
    request: Request,
    employee_id: int = Form(...),
    work_date: date = Form(...),
    shift_type: str = Form(...),
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
        
        # Проверяем, есть ли уже запись на эту дату
        existing = db.query(ScheduleEntry).filter(
            ScheduleEntry.user_id == employee_id,
            ScheduleEntry.work_date == work_date
        ).first()
        
        if existing:
            # Обновляем существующую запись
            existing.shift_type = shift_type
            existing.published = False
        else:
            # Создаем новую запись
            schedule = ScheduleEntry(
                user_id=employee_id,
                work_date=work_date,
                shift_type=shift_type,
                published=False
            )
            db.add(schedule)
        
        db.commit()
        return RedirectResponse(url="/admin/planning?success=saved", status_code=status.HTTP_303_SEE_OTHER)
        
    except Exception as e:
        print(f"Ошибка при сохранении расписания: {e}")
        return RedirectResponse(url="/admin/planning?error=server_error", status_code=status.HTTP_303_SEE_OTHER)

