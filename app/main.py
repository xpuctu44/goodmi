from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse


# AutoLoginMiddleware temporarily removed


app = FastAPI(title="Time Tracker")
app.add_middleware(SessionMiddleware, secret_key="dev-secret-change-me")
# app.add_middleware(AutoLoginMiddleware)  # Temporarily disabled

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
def index():
    # Temporarily return simple response without session
    return {"message": "Time Tracker API", "status": "running"}


@app.on_event("startup")
def on_startup():
    # Create tables on first run
    Base.metadata.create_all(bind=engine)
    # Apply lightweight migrations for SQLite schema drift
    run_sqlite_migrations(engine)