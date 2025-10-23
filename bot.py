import telebot
import time
import logging
from telebot import apihelper
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, ADMIN_ID
from database import add_schedule, get_all_schedules, get_schedule, add_user, get_all_users, delete_schedule

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

apihelper.proxy = None
bot = telebot.TeleBot(BOT_TOKEN)

# Раздельные хранилища
admin_schedule_data = {}
admin_broadcast_data = {}

print(f"🔧 DEBUG: ADMIN_ID = {ADMIN_ID}")

def main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('📅 Расписание')
    keyboard.add('🗑️ Удалить расписание')
    keyboard.add('📢 Рассылка')
    return keyboard

def admin_confirm_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('✅ Подтвердить', '❌ Отменить')
    return keyboard

def broadcast_confirm_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('✅ Разослать', '❌ Отменить рассылку')
    return keyboard

def dates_keyboard():
    schedules = get_all_schedules()
    keyboard = InlineKeyboardMarkup()
    for date in sorted(schedules.keys(), reverse=True):
        keyboard.add(InlineKeyboardButton(date, callback_data=date))
    return keyboard

def delete_dates_keyboard():
    schedules = get_all_schedules()
    keyboard = InlineKeyboardMarkup()
    for date in sorted(schedules.keys(), reverse=True):
        keyboard.add(InlineKeyboardButton(f"🗑️ {date}", callback_data=f"delete_{date}"))
    return keyboard

# УНИВЕРСАЛЬНАЯ ФУНКЦИЯ РАССЫЛКИ
def broadcast_message(photo_id=None, text=None, message_type="text"):
    users = get_all_users()
    successful = 0
    failed = 0
    
    print(f"🔔 Рассылка для {len(users)} пользователей")
    
    for user_id in users:
        try:
            if message_type == "photo" and photo_id:
                bot.send_photo(user_id, photo_id, caption=text)
            else:
                bot.send_message(user_id, text)
            successful += 1
            print(f"✅ Отправлено в {user_id}")
        except Exception as e:
            failed += 1
            print(f"❌ Ошибка отправки {user_id}: {e}")
    
    print(f"📊 Итог рассылки: {successful} успешно, {failed} ошибок")
    return successful, failed

# КОМАНДА START - ПЕРВЫЙ ОБРАБОТЧИК
@bot.message_handler(commands=['start'])
def start_command(message):
    print(f"🎯 /start от {message.from_user.id}")
    add_user(message.chat.id)
    
    if message.chat.type == 'private':
        welcome_text = """Привет {name}! Я бот с расписанием. Здесь будут расписание для Школы №7.

В боте есть расписание пока что только на 7 классы, но в скором времени будут на все

Все сделано для того что бы вы не переходили на макс)

by @qwer4ik777""".format(name=message.from_user.first_name)
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard())

# КОМАНДА ADMIN - ВТОРОЙ ОБРАБОТЧИК
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    print(f"🎯 Команда /admin получена! От: {message.from_user.id}")
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет прав доступа")
        return
    
    # Выходим из любых других режимов
    if message.chat.id in admin_broadcast_data:
        del admin_broadcast_data[message.chat.id]
    
    admin_schedule_data[message.chat.id] = {'step': 'waiting_photo'}
    bot.send_message(message.chat.id, "📸 Отправьте фото с расписанием:")

# КОМАНДА DEBUG
@bot.message_handler(commands=['debug'])
def debug_command(message):
    print(f"🎯 Команда /debug от {message.from_user.id}")
    users = get_all_users()
    schedules = get_all_schedules()
    
    info = f"""
🔍 ДИАГНОСТИКА:
User ID: {message.from_user.id}
ADMIN_ID: {ADMIN_ID}
Статус: {'✅ АДМИН' if message.from_user.id == ADMIN_ID else '❌ НЕ АДМИН'}
Пользователей: {len(users)}
Расписаний: {len(schedules)}
"""
    bot.send_message(message.chat.id, info)

# КНОПКА РАССЫЛКА - ТРЕТИЙ ОБРАБОТЧИК
@bot.message_handler(func=lambda message: message.text == '📢 Рассылка')
def start_broadcast(message):
    print(f"🎯 Кнопка 'Рассылка' от {message.from_user.id}")
    
    # Выходим из режима админа если был
    if message.chat.id in admin_schedule_data:
        del admin_schedule_data[message.chat.id]
    
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет прав доступа")
        return
    
    admin_broadcast_data[message.chat.id] = {'step': 'waiting_message'}
    bot.send_message(
        message.chat.id,
        "📢 РЕЖИМ РАССЫЛКИ:\n\nОтправьте сообщение для рассылки (текст или фото):",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add('❌ Отмена рассылки')
    )

# КНОПКА РАСПИСАНИЕ
@bot.message_handler(func=lambda message: message.text == '📅 Расписание')
def show_schedule_menu(message):
    print(f"🎯 Кнопка 'Расписание' от {message.from_user.id}")
    schedules = get_all_schedules()
    if not schedules:
        bot.send_message(message.chat.id, "📭 Расписание пока не добавлено")
        return
    bot.send_message(message.chat.id, "📅 Выберите дату:", reply_markup=dates_keyboard())

# КНОПКА УДАЛИТЬ РАСПИСАНИЕ
@bot.message_handler(func=lambda message: message.text == '🗑️ Удалить расписание')
def show_delete_menu(message):
    print(f"🎯 Кнопка 'Удалить' от {message.from_user.id}")
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Нет прав доступа")
        return
    schedules = get_all_schedules()
    if not schedules:
        bot.send_message(message.chat.id, "📭 Нет расписаний для удаления")
        return
    bot.send_message(message.chat.id, "🗑️ Выберите для удаления:", reply_markup=delete_dates_keyboard())

# ОБРАБОТЧИК ДЛЯ КНОПОК ПОДТВЕРЖДЕНИЯ РАССЫЛКИ - ДОЛЖЕН БЫТЬ ВЫШЕ ОБРАБОТЧИКА ТЕКСТА
@bot.message_handler(func=lambda message: message.text in ['✅ Разослать', '❌ Отменить рассылку'])
def handle_broadcast_confirmation(message):
    print(f"🎯 Подтверждение рассылки: '{message.text}' от {message.from_user.id}")
    
    if message.from_user.id != ADMIN_ID or message.chat.id not in admin_broadcast_data:
        print(f"❌ Неправильные условия: user_id={message.from_user.id}, in_data={message.chat.id in admin_broadcast_data}")
        return
    
    data = admin_broadcast_data[message.chat.id]
    
    if message.text == '✅ Разослать':
        print(f"🔄 Начинаем рассылку. Данные: {data}")
        bot.send_message(message.chat.id, "🔄 Начинаю рассылку...")
        
        if data['type'] == 'photo':
            successful, failed = broadcast_message(
                photo_id=data['photo_id'],
                text=data['text'],
                message_type="photo"
            )
        else:
            successful, failed = broadcast_message(
                text=data['text'],
                message_type="text"
            )
        
        bot.send_message(
            message.chat.id,
            f"✅ Рассылка завершена!\nУспешно: {successful}\nОшибок: {failed}",
            reply_markup=main_keyboard()
        )
    else:
        bot.send_message(message.chat.id, "❌ Рассылка отменена", reply_markup=main_keyboard())
    
    # Очищаем состояние рассылки
    if message.chat.id in admin_broadcast_data:
        del admin_broadcast_data[message.chat.id]

# ОБРАБОТКА ФОТО ДЛЯ РАССЫЛКИ И РАСПИСАНИЯ
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    print(f"🎯 Получено фото от {message.from_user.id}")
    
    # Проверяем режим рассылки
    if (message.from_user.id == ADMIN_ID and 
        message.chat.id in admin_broadcast_data and 
        admin_broadcast_data[message.chat.id].get('step') == 'waiting_message'):
        
        print("🔄 Фото для рассылки")
        admin_broadcast_data[message.chat.id]['photo_id'] = message.photo[-1].file_id
        admin_broadcast_data[message.chat.id]['text'] = message.caption or ""
        admin_broadcast_data[message.chat.id]['type'] = 'photo'
        admin_broadcast_data[message.chat.id]['step'] = 'waiting_confirmation'
        
        preview_text = "📷 Фото" + (f" с подписью: {message.caption}" if message.caption else "")
        users_count = len(get_all_users())
        
        bot.send_message(
            message.chat.id,
            f"📢 ПРЕДПРОСМОТР РАССЫЛКИ:\n\n{preview_text}\n\nПолучателей: {users_count}",
            reply_markup=broadcast_confirm_keyboard()
        )
        return
    
    # Проверяем режим добавления расписания
    if (message.from_user.id == ADMIN_ID and 
        message.chat.id in admin_schedule_data and 
        admin_schedule_data[message.chat.id].get('step') == 'waiting_photo'):
        
        print("🔄 Фото для расписания")
        admin_schedule_data[message.chat.id]['photo_id'] = message.photo[-1].file_id
        admin_schedule_data[message.chat.id]['text'] = message.caption or ""
        admin_schedule_data[message.chat.id]['step'] = 'waiting_date'
        
        bot.send_message(message.chat.id, "📅 Введите дату в формате ДД.ММ.ГГГГ:")
        return

# ОБРАБОТКА ТЕКСТА ДЛЯ РАССЫЛКИ И РАСПИСАНИЯ
@bot.message_handler(content_types=['text'])
def handle_text(message):
    print(f"📨 Текст: '{message.text}' от {message.from_user.id}")
    
    # Пропускаем команды
    if message.text and message.text.startswith('/'):
        print(f"⚡ Пропускаем команду: {message.text}")
        return
    
    # Пропускаем кнопки подтверждения (они уже обработаны выше)
    if message.text in ['✅ Разослать', '❌ Отменить рассылку', '✅ Подтвердить', '❌ Отменить']:
        print(f"⚡ Пропускаем кнопку подтверждения: {message.text}")
        return
    
    # Обработка для режима рассылки
    if (message.from_user.id == ADMIN_ID and 
        message.chat.id in admin_broadcast_data and 
        admin_broadcast_data[message.chat.id].get('step') == 'waiting_message'):
        
        print("🔄 Текст для рассылки")
        # Если пользователь отменяет рассылку
        if message.text == '❌ Отмена рассылки':
            if message.chat.id in admin_broadcast_data:
                del admin_broadcast_data[message.chat.id]
            bot.send_message(message.chat.id, "❌ Рассылка отменена", reply_markup=main_keyboard())
            return
        
        admin_broadcast_data[message.chat.id]['text'] = message.text
        admin_broadcast_data[message.chat.id]['type'] = 'text'
        admin_broadcast_data[message.chat.id]['step'] = 'waiting_confirmation'
        
        users_count = len(get_all_users())
        
        bot.send_message(
            message.chat.id,
            f"📢 ПРЕДПРОСМОТР РАССЫЛКИ:\n\n📝 Текст: {message.text}\n\nПолучателей: {users_count}",
            reply_markup=broadcast_confirm_keyboard()
        )
        return
    
    # Обработка для режима расписания (ввод даты)
    if (message.from_user.id == ADMIN_ID and 
        message.chat.id in admin_schedule_data and 
        admin_schedule_data[message.chat.id].get('step') == 'waiting_date'):
        
        print(f"🎯 Дата для расписания: {message.text}")
        admin_schedule_data[message.chat.id]['date'] = message.text
        admin_schedule_data[message.chat.id]['step'] = 'waiting_confirmation'
        
        bot.send_message(
            message.chat.id, 
            f"✅ Добавить расписание на {message.text}?", 
            reply_markup=admin_confirm_keyboard()
        )
        return

# ПОДТВЕРЖДЕНИЕ ДОБАВЛЕНИЯ РАСПИСАНИЯ
@bot.message_handler(func=lambda message: message.text in ['✅ Подтвердить', '❌ Отменить'])
def handle_schedule_confirmation(message):
    print(f"🎯 Подтверждение расписания: {message.text}")
    if message.from_user.id != ADMIN_ID or message.chat.id not in admin_schedule_data:
        return
    
    data = admin_schedule_data[message.chat.id]
    
    if message.text == '✅ Подтвердить':
        if all(k in data for k in ['date', 'photo_id']):
            add_schedule(data['date'], data['photo_id'], data['text'])
            successful, failed = broadcast_message(
                photo_id=data['photo_id'],
                text=f"📅 Новое расписание на {data['date']}!\n\n{data['text']}",
                message_type="photo"
            )
            bot.send_message(
                message.chat.id, 
                f"✅ Расписание добавлено! Рассылка: {successful} успешно, {failed} ошибок", 
                reply_markup=main_keyboard()
            )
        else:
            bot.send_message(message.chat.id, "❌ Данные неполные", reply_markup=main_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Отменено", reply_markup=main_keyboard())
    
    # Очищаем состояние расписания
    if message.chat.id in admin_schedule_data:
        del admin_schedule_data[message.chat.id]

# INLINE КНОПКИ
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    print(f"🎯 Inline кнопка: {call.data}")
    if call.data.startswith('delete_'):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Нет прав")
            return
        date = call.data.replace('delete_', '')
        if delete_schedule(date):
            bot.answer_callback_query(call.id, f"✅ Удалено: {date}")
            bot.edit_message_text(
                f"🗑️ Расписание на {date} удалено", 
                call.message.chat.id, 
                call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка удаления")
    else:
        schedule = get_schedule(call.data)
        if schedule:
            bot.send_photo(
                call.message.chat.id, 
                schedule['photo_id'], 
                caption=f"📅 {call.data}\n{schedule['text']}"
            )
        else:
            bot.answer_callback_query(call.id, "❌ Расписание не найдено")

if __name__ == '__main__':
    print("🤖 Бот запускается с улучшенной отладкой...")
    
    # Принудительно сбрасываем вебхуки и предыдущие сессии
    try:
        import requests
        # Закрываем предыдущие соединения
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1", timeout=5)
        print("✅ Сброшены предыдущие сессии")
    except:
        pass
    
    # Проверка подключения
    try:
        bot_info = bot.get_me()
        print(f"✅ Бот @{bot_info.username} подключен!")
        print(f"🆔 ID бота: {bot_info.id}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # Основной цикл с улучшенным polling
    while True:
        try:
            print("🔄 Запуск polling...")
            # Используем skip_pending чтобы пропустить старые сообщения
            bot.polling(
                none_stop=True, 
                timeout=30,
                long_polling_timeout=30,
                skip_pending=True
            )
        except Exception as e:
            print(f"❌ Ошибка polling: {e}")
            print("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)