from sqlalchemy import text
from sqlalchemy.engine import Engine


def _table_exists(engine: Engine, table: str) -> bool:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table"), {"table": table})
        return result.fetchone() is not None


def _column_exists(engine: Engine, table: str, column: str) -> bool:
    if not _table_exists(engine, table):
        return False
    with engine.connect() as connection:
        result = connection.execute(text(f"PRAGMA table_info('{table}')"))
        rows = result.mappings().all()
        return any(row["name"] == column for row in rows)


def run_sqlite_migrations(engine: Engine) -> None:
    # users.role
    if not _column_exists(engine, "users", "role"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'employee'")
            )

    # users.date_of_birth
    if not _column_exists(engine, "users", "date_of_birth"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN date_of_birth DATE NULL")
            )

    # attendance table creation if missing
    with engine.connect() as connection:
        exists = connection.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='attendance'
        """)).fetchone()
        if not exists:
            connection.execute(text("""
                CREATE TABLE attendance (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    started_at DATETIME NOT NULL,
                    ended_at DATETIME NULL,
                    work_date DATE NOT NULL,
                    hours REAL NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))

    # schedule_entries table
    with engine.connect() as connection:
        exists = connection.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='schedule_entries'
        """
        )).fetchone()
        if not exists:
            connection.execute(text("""
                CREATE TABLE schedule_entries (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    work_date DATE NOT NULL,
                    shift_type VARCHAR(20) NOT NULL,
                    published BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))

    # stores table
    with engine.connect() as connection:
        exists = connection.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='stores'
        """)).fetchone()
        if not exists:
            connection.execute(text("""
                CREATE TABLE stores (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    address TEXT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                )
            """))

    # users.store_id column
    if not _column_exists(engine, "users", "store_id"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN store_id INTEGER NULL REFERENCES stores(id)")
            )

    # schedule_entries.start_time column
    if not _column_exists(engine, "schedule_entries", "start_time"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE schedule_entries ADD COLUMN start_time TIME NULL")
            )

    # schedule_entries.end_time column
    if not _column_exists(engine, "schedule_entries", "end_time"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE schedule_entries ADD COLUMN end_time TIME NULL")
            )

    # schedule_entries.store_id column
    if not _column_exists(engine, "schedule_entries", "store_id"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE schedule_entries ADD COLUMN store_id INTEGER NULL REFERENCES stores(id)")
            )

    # schedule_entries.notes column
    if not _column_exists(engine, "schedule_entries", "notes"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE schedule_entries ADD COLUMN notes TEXT NULL")
            )

    # allowed_ips table
    with engine.connect() as connection:
        exists = connection.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='allowed_ips'
        """)).fetchone()
        if not exists:
            connection.execute(text("""
                CREATE TABLE allowed_ips (
                    id INTEGER PRIMARY KEY,
                    ip_address VARCHAR(45) NOT NULL UNIQUE,
                    description VARCHAR(255) NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL,
                    created_by INTEGER NULL REFERENCES users(id)
                )
            """))

    # stores.phone column
    if not _column_exists(engine, "stores", "phone"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE stores ADD COLUMN phone VARCHAR(20) NULL")
            )

    # users.web_username column
    if not _column_exists(engine, "users", "web_username"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN web_username VARCHAR(100) NULL")
            )

    # users.web_password_plain column
    if not _column_exists(engine, "users", "web_password_plain"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN web_password_plain VARCHAR(100) NULL")
            )

    # users.telegram_id column
    if not _column_exists(engine, "users", "telegram_id"):
        with engine.connect() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN telegram_id INTEGER NULL")
            )
            connection.execute(
                text("CREATE UNIQUE INDEX ix_users_telegram_id ON users(telegram_id)")
            )


