import os
import shutil
import sqlite3

# 1. Define Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite3')
MEDIA_DIR = os.path.join(BASE_DIR, 'media')
MIGRATIONS_DIR = os.path.join(BASE_DIR, 'complaints', 'migrations')

def reset_data():
    print("🚀 Starting full project reset...")

    # Delete Database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("✅ Database deleted.")

    # Clear Media Folder
    if os.path.exists(MEDIA_DIR):
        for filename in os.listdir(MEDIA_DIR):
            file_path = os.path.join(MEDIA_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
        print("✅ Media folder cleared.")

    # Reset Migrations (Keep __init__.py)
    if os.path.exists(MIGRATIONS_DIR):
        for filename in os.listdir(MIGRATIONS_DIR):
            if filename != "__init__.py":
                file_path = os.path.join(MIGRATIONS_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        print("✅ Migration files reset.")

    # Run Django Commands to rebuild
    print("\n🛠 Rebuilding database structure...")
    os.system('python manage.py makemigrations')
    os.system('python manage.py migrate')

    print("\n✨ Reset complete! Your project is now a blank slate.")
    print("👉 Use 'python manage.py createsuperuser' to get started.")

if __name__ == "__main__":
    reset_data()