import telebot
from telebot import types
import os
import re
import configparser
from PIL import Image
from detection.logo_detector import detect_logo
from image.image_processor import process_image, ProcessMode

rgb_pattern = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')

config = configparser.ConfigParser()
config.read('resources/application.conf')
model_path = config['Config']['model_path']
telegram_token = config['Config']['telegram_token']
bot = telebot.TeleBot(telegram_token)

user_dict = {}


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message,
                 'Привет, вы можете загрузить изображение и бот заблокирует логотипы на нем.')


@bot.message_handler(content_types=['photo'])
def image_message(message):
    file_id = message.photo[-1].file_id
    user_dict[message.chat.id] = {'file_id': file_id}
    reply_with_markup(message, 'Выберите режим работы блокировщика:', ['Размытие', 'Заполнение', 'Рамка'], get_mode)


def get_mode(message):
    if not user_dict[message.chat.id]:
        return

    mode_answer = message.text
    if mode_answer == 'Размытие':
        mode = ProcessMode.BLUR
    elif mode_answer == 'Заполнение':
        mode = ProcessMode.FILL
    elif mode_answer == 'Рамка':
        mode = ProcessMode.BOUNDING_BOX
    else:
        reply_with_markup(message, 'Можно выбрать только из существующих режимов:', ['Размытие', 'Заполнение', 'Рамка'],
                          get_mode)
        return

    user_dict[message.chat.id]['mode'] = mode
    if mode == ProcessMode.BLUR:
        reply_with_markup(message, 'Выберите силу размытия или введите значение от 1 до 100:',
                          ['Слабый', 'Средний', 'Сильный'],
                          get_blur_force)
    else:
        reply_with_markup(message,
                          'Выберите один из существующих цветов или RGB hex (#****** или #***):',
                          ['Красный', 'Оранжевый', 'Желтый', 'Зеленый', 'Сининй', 'Фиолетовый'],
                          get_color)


def get_color(message):
    color_answer = message.text
    if color_answer == 'Красный':
        color = (255, 0, 0)
    elif color_answer == 'Оранжевый':
        color = (255, 165, 0)
    elif color_answer == 'Желтый':
        color = (255, 255, 0)
    elif color_answer == 'Зеленый':
        color = (0, 255, 0)
    elif color_answer == 'Сининй':
        color = (0, 0, 255)
    elif color_answer == 'Фиолетовый':
        color = (128, 0, 128)
    else:
        if is_rgb_hex(color_answer):
            color = hex_to_rgb(color_answer)
        else:
            reply_with_markup(message,
                              'Значением может быть один из существующих цветов или RGB hex (#****** или #***)',
                              ['Красный', 'Оранжевый', 'Желтый', 'Зеленый', 'Сининй', 'Фиолетовый'],
                              get_color)
            return

    process_photo(message, user_dict[message.chat.id]['file_id'], user_dict[message.chat.id]['mode'], color=color)


def get_blur_force(message):
    color_answer = message.text
    if color_answer == 'Слабый':
        blur_force = 5
    elif color_answer == 'Средний':
        blur_force = 20
    elif color_answer == 'Сильный':
        blur_force = 50
    else:
        if color_answer.isdigit() and 0 < int(color_answer) <= 100:
            blur_force = int(color_answer)
        else:
            reply_with_markup(message, 'Значение должно быть от 1 до 100.', ['Слабый', 'Средний', 'Сильный'],
                              get_blur_force)
            return

    process_photo(message, user_dict[message.chat.id]['file_id'], user_dict[message.chat.id]['mode'],
                  blur_force=blur_force)


def process_photo(message, file_id, mode, color=(255, 0, 0), blur_force=20):
    bot.reply_to(message, 'Идет обработка изображения. Подождите...')
    bot_file = bot.get_file(file_id)
    downloaded_file = bot.download_file(bot_file.file_path)
    with open(bot_file.file_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    image = Image.open(bot_file.file_path).convert('RGB')
    detected_boxes = detect_logo(model_path, image, 0.5)
    processed_image = process_image(image, detected_boxes, mode, color, blur_force)
    processed_image.save(bot_file.file_path, 'PNG')
    with open(bot_file.file_path, 'rb') as sendPhoto:
        bot.send_photo(message.chat.id, sendPhoto)
    if os.path.exists(bot_file.file_path):
        os.remove(bot_file.file_path)
    user_dict[message.chat.id] = None


def reply_with_markup(message, text, markup_variants, next_step=None):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*markup_variants)
    msg = bot.reply_to(message, text, reply_markup=markup)
    if next_step:
        bot.register_next_step_handler(msg, next_step)


def is_rgb_hex(value):
    return bool(rgb_pattern.match(value))


def hex_to_rgb(hex):
    hex = hex.lstrip('#')
    hlen = len(hex)
    return tuple(int(hex[i:i + int(hlen / 3)], 16) for i in range(0, hlen, int(hlen / 3)))


bot.polling()
