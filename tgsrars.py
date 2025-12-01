import telebot
import sqlite3
from datetime import datetime

# Токен бота от BotFather
API_TOKEN = '8508567870:AAE2S7I7jPLmN6LNpf6Gropt8vJ4w9udLg'
bot = telebot.TeleBot(API_TOKEN)

# База данных
conn = sqlite3.connect('stars_db.db', check_same_thread=False)
cursor = conn.cursor()

# ТАБЛИЦЫ БД
#------------------------------------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    total_stars INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    star_name TEXT,
    stars_count INTEGER,
    status TEXT DEFAULT 'pending',
    order_date TEXT
)
''')
conn.commit()
#-------------------------------------------------------------------------


# Каталог звезд
stars_catalog = {
    "1": {"name": "Обычная звезда", "price": 10, "desc": "Базовая звезда"},
    "2": {"name": "Золотая звезда", "price": 50, "desc": "Особая звезда"},
    "3": {"name": "Алмазная звезда", "price": 100, "desc": "Эксклюзив"}
}

# Стартовая команда
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Регистрируем пользователя если его нет
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    
    welcome_text = """🌟 Добро пожаловать в магазин Telegram Stars!
    
✨ Что такое Telegram Stars?
Это внутриигровая валюта в Telegram, которую можно использовать для покупки виртуальных товаров.

🛍️ Доступные звезды:
/1 - Обычная звезда (10 Stars)
/2 - Золотая звезда (50 Stars)  
/3 - Алмазная звезда (100 Stars)

📋 Команды:
/mybalance - Мой баланс
/buy - Купить звезду
/mystars - Мои покупки
/help - Помощь"""
    
    bot.send_message(message.chat.id, welcome_text)

# Показываем баланс
@bot.message_handler(commands=['mybalance'])
def show_balance(message):
    user_id = message.from_user.id
    
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        balance = result[0]
        bot.send_message(message.chat.id, f"💰 Ваш баланс: {balance} Stars")
    else:
        bot.send_message(message.chat.id, "❌ Вы не зарегистрированы. Напишите /start")

# Показываем каталог
@bot.message_handler(commands=['buy'])
def show_catalog(message):
    catalog_text = "✨ Выберите звезду для покупки:\n\n"
    
    for key, star in stars_catalog.items():
        catalog_text += f"/{key} - {star['name']} - {star['price']} Stars\n{star['desc']}\n\n"
    
    bot.send_message(message.chat.id, catalog_text)

# Команды для покупки конкретных звезд
@bot.message_handler(commands=['1', '2', '3'])
def buy_star(message):
    user_id = message.from_user.id
    star_id = message.text[1:]  # Убираем слеш
    
    if star_id in stars_catalog:
        star = stars_catalog[star_id]
        price = star['price']
        
        # Проверяем баланс
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if result and result[0] >= price:
            # Списываем Stars и создаем заказ
            new_balance = result[0] - price
            cursor.execute("UPDATE users SET balance = ?, total_stars = total_stars + ? WHERE user_id = ?", 
                          (new_balance, 1, user_id))
            
            # Добавляем заказ
            order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO orders (user_id, star_name, stars_count, order_date) VALUES (?, ?, ?, ?)",
                          (user_id, star['name'], price, order_date))
            conn.commit()
            
            bot.send_message(message.chat.id, f"✅ Поздравляем! Вы купили {star['name']} за {price} Stars!")
        else:
            bot.send_message(message.chat.id, f"❌ Недостаточно Stars. Нужно {price} Stars")
    else:
        bot.send_message(message.chat.id, "❌ Такой звезды нет в каталоге")

# Показать мои покупки
@bot.message_handler(commands=['mystars'])
def show_my_stars(message):
    user_id = message.from_user.id
    
    cursor.execute("SELECT star_name, stars_count, order_date FROM orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()
    
    if orders:
        response = "📦 Ваши покупки:\n\n"
        for order in orders:
            response += f"✨ {order[0]}\n💎 {order[1]} Stars\n📅 {order[2]}\n\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "📭 У вас еще нет покупок")

# Добавить Stars на баланс (для тестирования)
@bot.message_handler(commands=['addstars'])
def add_stars(message):
    # Это для теста, в реальном боте Stars добавляются через Telegram
    user_id = message.from_user.id
    
    try:
        # Пытаемся получить количество из команды /addstars 100
        amount = int(message.text.split()[1])
        
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        
        bot.send_message(message.chat.id, f"✅ На баланс добавлено {amount} Stars")
    except:
        bot.send_message(message.chat.id, "❌ Используйте: /addstars [количество]")

# Помощь
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """🆘 Помощь по командам:

/start - Начать работу
/buy - Показать каталог
/mybalance - Мой баланс Stars
/mystars - Мои покупки

💎 Как получить Stars?
1. Откройте @wallet в Telegram
2. Пополните баланс
3. Используйте Stars в ботах и мини-приложениях

🌟 Внимание!
Это демо-бот для обучения.
Telegram Stars - реальная валюта Telegram."""
    
    bot.send_message(message.chat.id, help_text)

# Обработка обычных сообщений важная заметка (не трогать)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "❌ Неизвестная команда. Напишите /help")
    else:
        bot.send_message(message.chat.id, "✨ Я бот для покупки звезд. Используйте команды:\n/start - начать\n/help - помощь")

# Запускаем бота (не трогать)
print("🤖 Бот запущен...")
bot.polling(none_stop=True)