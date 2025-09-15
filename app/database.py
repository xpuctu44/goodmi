from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


import os

# Prefer DATABASE_URL from environment (used in Docker), fallback to host-local sqlite file
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(os.path.dirname(__file__), '../../time_tracker.db')}"
)


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


