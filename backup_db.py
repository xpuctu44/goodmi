import os
import shutil
from datetime import datetime
import sys

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

def _detect_db_path() -> str:
    """Определяет путь к SQLite БД.

    Приоритеты:
    1) DATABASE_URL из .env, если это sqlite:///...
    2) /goodmi/time_tracker.db (хостовой путь)
    3) time_tracker.db рядом со скриптом
    """
    project_dir = os.path.dirname(__file__)

    # 1) Пробуем прочитать .env
    if load_dotenv:
        try:
            load_dotenv()
            db_url = os.getenv('DATABASE_URL', '')
            if db_url.startswith('sqlite:///'):
                # поддержка форматов sqlite:///./file.db и sqlite:////abs/path.db
                raw_path = db_url[len('sqlite:///'):]
                # Если начинается с '/', это абсолютный путь, иначе относительный к project_dir
                db_candidate = raw_path if raw_path.startswith('/') else os.path.join(project_dir, raw_path)
                if os.path.exists(db_candidate):
                    return os.path.abspath(db_candidate)
        except Exception:
            pass

    # 2) Хостовой путь (фактический у вас)
    host_path = '/goodmi/time_tracker.db'
    if os.path.exists(host_path):
        return host_path

    # 3) Локально рядом со скриптом
    local_path = os.path.join(project_dir, 'time_tracker.db')
    if os.path.exists(local_path):
        return local_path

    # Ничего не нашли
    return ''


def backup_database():
    # Путь к базе данных (автоопределение)
    db_path = _detect_db_path()

    # Папка для резервных копий
    backup_dir = os.path.join(os.path.dirname(__file__), 'backups')

    # Создаем папку backups, если она не существует
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Проверяем, существует ли файл базы данных
    if not db_path or not os.path.exists(db_path):
        print(f"Ошибка: файл базы данных не найден. Проверьте DATABASE_URL или путь. Последний проверенный: '{db_path or 'не определен'}'")
        return False

    # Создаем имя файла резервной копии с timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"time_tracker_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        # Копируем файл базы данных
        shutil.copy2(db_path, backup_path)
        print(f"Резервная копия создана: {backup_path}")

        # Удаляем старые резервные копии (оставляем последние 10)
        cleanup_old_backups(backup_dir, keep_count=10)

        return True
    except Exception as e:
        print(f"Ошибка при создании резервной копии: {e}")
        return False


def cleanup_old_backups(backup_dir, keep_count=10):
    """Удаляет старые резервные копии, оставляя только последние keep_count файлов"""
    try:
        # Получаем список файлов резервных копий
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('time_tracker_backup_') and f.endswith('.db')]

        if len(backup_files) <= keep_count:
            return

        # Сортируем по дате создания (новые сначала)
        backup_files.sort(key=lambda x: os.path.getctime(os.path.join(backup_dir, x)), reverse=True)

        # Удаляем старые файлы
        for old_file in backup_files[keep_count:]:
            old_path = os.path.join(backup_dir, old_file)
            try:
                os.remove(old_path)
                print(f"Удалена старая резервная копия: {old_file}")
            except Exception as e:
                print(f"Ошибка при удалении {old_file}: {e}")

    except Exception as e:
        print(f"Ошибка при очистке старых резервных копий: {e}")

if __name__ == "__main__":
    success = backup_database()
    sys.exit(0 if success else 1)