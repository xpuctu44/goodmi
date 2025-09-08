from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware


app = FastAPI(title="Time Tracker")
app.add_middleware(SessionMiddleware, secret_key="dev-secret-change-me")

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Routers
from app.routers.health import router as health_router  # noqa: E402
from app.routers.auth import router as auth_router  # noqa: E402
from app.routers.attendance import router as attendance_router  # noqa: E402
from app.routers.admin import router as admin_router  # noqa: E402
from app.database import engine, Base
from app import models
from app.migrations import run_sqlite_migrations

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(attendance_router)
app.include_router(admin_router)


@app.get("/", include_in_schema=False)
def index(request: Request):
    # Check if user is logged in
    user_id = request.session.get("user_id")
    if user_id:
        # User is logged in, redirect to dashboard
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Show welcome page with login/register options
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Time Tracker - Система учета рабочего времени"},
    )


@app.on_event("startup")
def on_startup():
    # Create tables on first run
    Base.metadata.create_all(bind=engine)
    # Apply lightweight migrations for SQLite schema drift
    run_sqlite_migrations(engine)