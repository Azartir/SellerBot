import logging
import telebot
import os
import json

# Включение логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурационных данных
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Инициализация бота
bot = telebot.TeleBot(config['TELEGRAM_BOT_TOKEN'])
ADMIN_ID = config['ADMIN_ID']

# Путь к файлу для хранения данных
data_file = 'user_balances.json'
# Путь к файлу для логов
log_file = 'bot_logs.txt'

# Инициализация логгера
logger = logging.getLogger('telegram_bot')
logger.setLevel(logging.INFO)

# Обработчик файлового вывода логов
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Загрузка данных из файла
def load_data():
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Ошибка при загрузке данных из JSON файла")
            return {}
    else:
        return {}

# Сохранение данных в файл
def save_data(data):
    try:
        with open(data_file, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в JSON файл: {str(e)}")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        user_id = str(message.from_user.id)
        username = message.from_user.username
        user_data = load_data()

        # Сохраняем лог о запуске бота пользователя
        logger.info(f"Пользователь {username} ({user_id}) запустил бота")

        if user_id not in user_data:
            user_data[user_id] = {'username': username, 'balance': 0}
            save_data(user_data)
        
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.row(telebot.types.KeyboardButton("Купить UC"))
        keyboard.row(telebot.types.KeyboardButton("Баланс"))
        bot.send_message(message.chat.id, 'Привет! Выберите опцию:', reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {str(e)}")

    finally:
        # В любом случае сохраняем текущие логи в файл
        file_handler.flush()

# Функция для генерации клавиатуры с выбором прайса UC
def generate_price_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row(telebot.types.KeyboardButton("60UC - 85 р"))
    keyboard.row(telebot.types.KeyboardButton("325UC - 415р"))
    keyboard.row(telebot.types.KeyboardButton("355UC - 450р"))
    keyboard.row(telebot.types.KeyboardButton("660UC - 810р"))
    keyboard.row(telebot.types.KeyboardButton("720UC - 855р"))
    keyboard.row(telebot.types.KeyboardButton("1075UC - 1300р"))
    keyboard.row(telebot.types.KeyboardButton("1800UC - 2050р"))
    keyboard.row(telebot.types.KeyboardButton("1950UC - 2200р"))
    keyboard.row(telebot.types.KeyboardButton("3850UC - 4050р"))
    keyboard.row(telebot.types.KeyboardButton("4000UC - 4300р"))
    keyboard.row(telebot.types.KeyboardButton("8100UC - 8200р"))
    keyboard.row(telebot.types.KeyboardButton("Назад"))
    return keyboard

# Обработчик нажатий на кнопки
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    try:
        user_id = str(message.from_user.id)
        user_data = load_data()

        # Проверяем сообщение "Назад" в первую очередь
        if message.text == 'Назад':
            handle_start(message)
            logger.info(f"Пользователь {user_data[user_id]['username']} ({user_id}) вернулся на стартовый экран")
            return

        # Далее обрабатываем остальные возможные действия
        if message.text == 'Купить UC':
            keyboard = generate_price_keyboard()
            bot.send_message(message.chat.id, "Выберите количество UC:", reply_markup=keyboard)
            logger.info(f"Пользователь {user_data[user_id]['username']} ({user_id}) выбрал покупку UC")

        elif any(uc in message.text for uc in ['UC']):
            uc_amount, price = message.text.split(' - ')
            uc_amount = uc_amount.replace('UC', '').strip()
            price = int(price.replace('р', '').strip())
            balance = user_data[user_id]['balance']

            if balance >= price:
                bot.send_message(message.chat.id, f"Вы выбрали {uc_amount} UC. Отправьте ваш ID в PUBG.")
                bot.register_next_step_handler(message, process_uc_purchase, uc_amount, price)
                logger.info(f"Пользователь {user_data[user_id]['username']} ({user_id}) выбрал {uc_amount} за {price} р.")
            else:
                bot.send_message(message.chat.id, "У вас недостаточно средств для этой покупки.")
                logger.warning(f"Пользователь {user_data[user_id]['username']} ({user_id}) попытался купить {uc_amount}, но недостаточно средств")

        elif message.text == 'Баланс':
            balance = user_data[user_id]['balance']
            keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            keyboard.row(telebot.types.KeyboardButton("Пополнить"))
            keyboard.row(telebot.types.KeyboardButton("Назад"))
            bot.send_message(message.chat.id, f"Ваш баланс: {balance} UC", reply_markup=keyboard)
            logger.info(f"Пользователь {user_data[user_id]['username']} ({user_id}) запросил баланс")

        elif message.text == 'Пополнить':
            bot.send_message(message.chat.id, "Совершите перевод на указанную вами сумму на карту 2200700495101577 и отправьте фото чека.")
            bot.register_next_step_handler(message, handle_top_up_request)
            logger.info(f"Пользователь {user_data[user_id]['username']} ({user_id}) запросил пополнение")

    except Exception as e:
        logger.error(f"Ошибка при обработке нажатия кнопки: {str(e)}")

# Обработчик запроса на пополнение баланса
def handle_top_up_request(message):
    try:
        user_id = str(message.from_user.id)
        user_data = load_data()
        if message.content_type == 'photo':
            # Обработка фото
            bot.send_message(message.chat.id, "Спасибо! Ваш чек получен и будет проверен администратором.")
            logger.info(f"Пользователь {user_data[user_id]['username']} ({user_id}) отправил чек пополнения баланса")

            # Отправка чека администратору с просьбой подтвердить
            markup = telebot.types.InlineKeyboardMarkup()
            real_check_button = telebot.types.InlineKeyboardButton(text='Реальный чек', callback_data=f'real_check_{user_id}')
            invalid_check_button = telebot.types.InlineKeyboardButton(text='Некорректный чек', callback_data=f'invalid_check_{user_id}')
            markup.add(real_check_button, invalid_check_button)
            
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            bot.send_message(ADMIN_ID, f"Пользователь {user_data[user_id]['username']} прислал чек. Выберите действие:", reply_markup=markup)
            
        else:
            bot.send_message(message.chat.id, "Пожалуйста, отправьте чек пополнения в формате фото.")
            bot.register_next_step_handler(message, handle_top_up_request)
            logger.warning(f"Пользователь {user_data[user_id]['username']} ({user_id}) отправил неподдерживаемый тип данных для чека")
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса на пополнение баланса: {str(e)}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке вашего чека. Попробуйте еще раз позже.")

# Функция для обработки покупки UC после подтверждения администратором
def process_uc_purchase(message, uc_amount, price):
    try:
        user_id = str(message.from_user.id)
        user_data = load_data()
        pubg_id = message.text.strip()
        
        # Производим покупку, если ID в PUBG корректен
        if pubg_id:
            user_data[user_id]['balance'] -= price
            save_data(user_data)
            bot.send_message(message.chat.id, f"Ваш заказ на {uc_amount} UC принят. ID в PUBG: {pubg_id}. Баланс обновлен, ожидайте пополнения.")
            bot.send_message(ADMIN_ID, f"Пользователь {user_data[user_id]['username']} ({user_id}) купил {uc_amount} UC. ID в PUBG:")
            bot.send_message(ADMIN_ID, f"{pubg_id}")
            logger.info(f"Пользователь {user_data[user_id]['username']} ({user_id}) купил {uc_amount} UC. ID в PUBG: {pubg_id}.")
        else:
            bot.send_message(message.chat.id, "Введите корректный ID в PUBG.")
            bot.register_next_step_handler(message, process_uc_purchase, uc_amount, price)
            
    except Exception as e:
        logger.error(f"Ошибка при обработке покупки UC: {str(e)}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке вашего заказа. Попробуйте еще раз позже.")

# Обработчик нажатий на кнопки "реальный чек" и "некорректный чек" у администратора
@bot.callback_query_handler(func=lambda call: True)
def handle_admin_buttons(call):
    try:
        user_id = call.data.split('_')[-1]
        user_data = load_data()
        if call.data.startswith('real_check'):
            # Действие при нажатии "реальный чек"
            bot.send_message(call.message.chat.id, f"Введите сумму для пополнения баланса пользователя {user_data[user_id]['username']}:")
            bot.register_next_step_handler(call.message, lambda message: confirm_top_up(message, user_id))
        
        elif call.data.startswith('invalid_check'):
            # Действие при нажатии "некорректный чек"
            bot.send_message(call.message.chat.id, f"Пользователю отказано.")
            bot.send_message(user_id, "Ваш чек не прошел проверку. Нажмите 'Назад'.")
    except Exception as e:
        logger.error(f"Ошибка при обработке нажатия кнопки администратором: {str(e)}")

# Функция для подтверждения пополнения баланса администратором
def confirm_top_up(message, user_id):
    try:
        admin_message = message.text.strip()
        user_data = load_data()
        if admin_message.isdigit():
            amount = int(admin_message)
            user_data[user_id]['balance'] += amount
            save_data(user_data)
            bot.send_message(ADMIN_ID, f"Баланс пользователя {user_data[user_id]['username']} успешно пополнен на {amount} UC.")
            bot.send_message(user_id, f"Ваш баланс успешно пополнен на {amount} UC.")
            logger.info(f"Пополнение баланса пользователя {user_data[user_id]['username']} ({user_id}) на {amount} UC подтверждено.")
        else:
            bot.send_message(ADMIN_ID, "Введите корректное число.")
            # Регистрация следующего шага для администратора в случае некорректного ввода
            bot.register_next_step_handler_by_chat_id(ADMIN_ID, lambda msg: confirm_top_up(msg, user_id))
    except Exception as e:
        logger.error(f"Ошибка при подтверждении пополнения баланса: {str(e)}")
        bot.send_message(ADMIN_ID, "Произошла ошибка при подтверждении пополнения баланса. Попробуйте еще раз позже.")

# Главная функция для запуска бота
def main():
    try:
        bot.polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")

if __name__ == '__main__':
    main()