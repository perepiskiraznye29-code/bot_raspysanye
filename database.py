import json
import os
from config import DATABASE_FILE, USERS_FILE

# Функции для работы с расписанием
def load_schedules():
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_schedules(schedules):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedules, f, ensure_ascii=False, indent=2)

def add_schedule(date, photo_id, text):
    schedules = load_schedules()
    schedules[date] = {
        'photo_id': photo_id,
        'text': text or ""
    }
    save_schedules(schedules)

def get_all_schedules():
    return load_schedules()

def get_schedule(date):
    schedules = load_schedules()
    return schedules.get(date)

def delete_schedule(date):
    schedules = load_schedules()
    if date in schedules:
        del schedules[date]
        save_schedules(schedules)
        return True
    return False

# Функции для работы с пользователями
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)
        print(f"✅ Добавлен пользователь/чат: {user_id}")

def get_all_users():
    return load_users()

def debug_users():
    users = load_users()
    print(f"Всего пользователей/чатов: {len(users)}")
    for user_id in users:
        print(f" - {user_id} ({'ЛС' if user_id > 0 else 'Чат'})")
    return users