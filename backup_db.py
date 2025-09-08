import os
import shutil
from datetime import datetime
import sys

def backup_database():
    # Путь к базе данных
    db_path = os.path.join(os.path.dirname(__file__), 'time_tracker.db')

    # Папка для резервных копий
    backup_dir = os.path.join(os.path.dirname(__file__), 'backups')

    # Создаем папку backups, если она не существует
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Проверяем, существует ли файл базы данных
    if not os.path.exists(db_path):
        print(f"Ошибка: файл базы данных не найден по пути {db_path}")
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