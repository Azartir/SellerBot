import logging
import telebot
import os
import json

# Включение логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Укажите ваш токен и ID администратора здесь
TELEGRAM_BOT_TOKEN = "7469802414:AAGeN86RbNCEChX4eZ5mOkLa2wn2kew73L0"
ADMIN_ID = "YOUR_ADMIN_ID"

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Путь к файлу для хранения данных
data_file = 'user_balances.json'

# Загрузка данных из файла
def load_data():
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    else:
        return {}

# Сохранение данных в файл
def save_data(data):
    with open(data_file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Инициализация базы данных из JSON
user_data = load_data()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    if user_id not in user_data:
        user_data[user_id] = {'username': username, 'balance': 0}
        save_data(user_data)
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("Купить UC", callback_data='buy_uc'))
    keyboard.add(telebot.types.InlineKeyboardButton("Баланс", callback_data='balance'))
    bot.send_message(message.chat.id, 'Привет! Выберите опцию:', reply_markup=keyboard)

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    try:
        user_id = str(call.from_user.id)
        if call.data == 'buy_uc':
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(telebot.types.InlineKeyboardButton("60UC - 85 р", callback_data='60UC_85'))
            keyboard.row(telebot.types.InlineKeyboardButton("325UC - 415р", callback_data='325UC_415'))
            keyboard.row(telebot.types.InlineKeyboardButton("355UC - 450р", callback_data='355UC_450'))
            keyboard.row(telebot.types.InlineKeyboardButton("660UC - 810р", callback_data='660UC_810'))
            keyboard.row(telebot.types.InlineKeyboardButton("720UC - 855р", callback_data='720UC_855'))
            keyboard.row(telebot.types.InlineKeyboardButton("1075UC - 1300р", callback_data='1075UC_1300'))
            keyboard.row(telebot.types.InlineKeyboardButton("1800UC - 2050р", callback_data='1800UC_2050'))
            keyboard.row(telebot.types.InlineKeyboardButton("1950UC - 2200р", callback_data='1950UC_2200'))
            keyboard.row(telebot.types.InlineKeyboardButton("3850UC - 4050р", callback_data='3850UC_4050'))
            keyboard.row(telebot.types.InlineKeyboardButton("4000UC - 4300р", callback_data='4000UC_4300'))
            keyboard.row(telebot.types.InlineKeyboardButton("8100UC - 8200р", callback_data='8100UC_8200'))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="Выберите количество UC:", reply_markup=keyboard)
        
        elif call.data.endswith('UC'):
            uc_amount, price = call.data.split('_')
            price = int(price)
            balance = user_data[user_id]['balance']

            if balance >= price:
                bot.send_message(call.message.chat.id, f"Вы выбрали {uc_amount}. Отправьте ваш ID в PUBG.")
                bot.register_next_step_handler(call.message, process_uc_purchase, uc_amount, price)
            else:
                bot.send_message(call.message.chat.id, "У вас недостаточно средств для этой покупки.")

        elif call.data == 'balance':
            balance = user_data[user_id]['balance']
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(telebot.types.InlineKeyboardButton("Пополнить", callback_data='top_up'))
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f"Ваш баланс: {balance} UC", reply_markup=keyboard)

        elif call.data == 'top_up':
            bot.send_message(call.message.chat.id, "Совершите перевод на указанную вами сумму Карта: 2200700495101577 В ОТВЕТНОМ СООБЩЕНИИ ПРИШЛИТЕ ЧЕК ТРАНЗАКЦИИ:")

    except Exception as e:
        logger.error(f"Ошибка при обработке нажатия кнопки: {str(e)}")

# Обработчик текстовых сообщений (комментариев или запросов)
def process_uc_purchase(message, uc_amount, price):
    try:
        user_id = str(message.from_user.id)
        bot.send_message(ADMIN_ID, f"Пользователь {user_data[user_id]['username']} хочет пополнить на {price} руб. ({uc_amount}). Сообщение: {message.text}")
        bot.send_message(message.chat.id, f"Ваш запрос на {uc_amount} отправлен администратору.")
        
        # Обновление баланса
        user_data[user_id]['balance'] -= price
        save_data(user_data)

    except Exception as e:
        logger.error(f"Ошибка при обработке покупки UC: {str(e)}")

# Главная функция для запуска бота
def main():
    try:
        bot.polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")

if __name__ == '__main__':
    main()
