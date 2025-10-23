import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

class Config:
    # Берем токен из .env или используем fallback (для совместимости)
    BOT_TOKEN = os.getenv('BOT_TOKEN', "8228608268:AAFRwTGtJG0bigDSc_VBQQ9AeuXLz8gEJ8o")
    
    # ADMIN_ID -> ADMIN_IDS (список для поддержки нескольких админов)
    admin_ids_str = os.getenv('ADMIN_IDS', "6872547230")
    ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
    
    # Файлы базы данных
    DATABASE_FILE = os.getenv('DATABASE_FILE', "schedules.json")
    USERS_FILE = os.getenv('USERS_FILE', "users.json")
    
    @classmethod
    def validate(cls):
        """Проверяем, что все необходимые переменные загружены"""
        if not cls.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN не найден!")
        if not cls.ADMIN_IDS:
            raise ValueError("❌ ADMIN_IDS не найдены!")
        print("✅ Конфигурация загружена успешно!")
        
        # Предупреждение, если используется fallback токен
        if os.getenv('BOT_TOKEN') is None:
            print("⚠️  Используется токен из кода. Добавьте BOT_TOKEN в .env файл!")

# Проверяем конфигурацию при импорте
Config.validate()

# Для обратной совместимости оставляем старые переменные
BOT_TOKEN = Config.BOT_TOKEN
ADMIN_ID = Config.ADMIN_IDS[0]  # Первый админ как основной (для совместимости)
ADMIN_IDS = Config.ADMIN_IDS    # Список всех админов (рекомендуется использовать это)
DATABASE_FILE = Config.DATABASE_FILE
USERS_FILE = Config.USERS_FILE
