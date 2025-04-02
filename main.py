import sqlite3
import random
import telebot
from datetime import datetime

# Настройки бота
TOKEN = "7230163062:AAEPIIfr5skmmV_Cj8VayKhIUHAcpp7Ct5s"  # Замените на свой токен
bot = telebot.TeleBot(TOKEN)


# Подключение к базе данных
def init_db():
    conn = sqlite3.connect('unique_numbers.db', check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        random_number INTEGER UNIQUE,
        registration_date TEXT,
        last_request_date TEXT
    )
    ''')

    # Индексы для быстрого поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_number ON users(random_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user ON users(user_id)')

    conn.commit()
    return conn


db_conn = init_db()


def generate_unique_number():
    """Генерирует уникальное число, которого нет в базе"""
    while True:
        num = random.randint(1, 10000)  # Большой диапазон для уникальности
        cursor = db_conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE random_number = ?', (num,))
        if not cursor.fetchone():
            return num


def get_user_number(user_id):
    """Получает информацию о числе пользователя"""
    cursor = db_conn.cursor()
    cursor.execute(
        'SELECT random_number, registration_date FROM users WHERE user_id = ?',
        (user_id,)
    )
    return cursor.fetchone()


# Обработчик команды /start
@bot.message_handler(commands=['start', 'число', 'number'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Проверяем, есть ли пользователь в базе
    existing_data = get_user_number(user_id)

    if existing_data:
        number, reg_date = existing_data
        response = (
            f"ЭЭЭЭ туох дьигин дэээ! (ง︡'-'︠)ง Не жульничай, у тебя уже есть билетик!\n\n"
            f"Твой билетик: {number}\n"
        )
    else:
        try:
            number = generate_unique_number()
            cursor = db_conn.cursor()
            cursor.execute(
                '''
                INSERT INTO users 
                (user_id, username, first_name, random_number, registration_date, last_request_date) 
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (user_id, username, first_name, number, current_time, current_time)
            )
            db_conn.commit()

            response = (
                f"( ͡° ͜つ ͡°) Дарова, {first_name}!\n\n"
                f"Твой билетик: {number}\n\n"
                "Говорю сразу: повторно билетик получить не выйдет, так шо запоминай!"
            )
        except sqlite3.IntegrityError:
            response = "⚠️ Произошла ошибка. Пожалуйста, попробуй еще раз."
            db_conn.rollback()

    bot.send_message(message.chat.id, response)


# Обработчик всех остальных сообщений
@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    help_text = (
        "Чего? Не понял. Чтобы получить билетик на розыгрыш, введи /start\n"
    )
    bot.send_message(message.chat.id, help_text)


if __name__ == '__main__':
    print("Бот запущен и готов к работе!")
    try:
        bot.infinity_polling()
    finally:
        db_conn.close()