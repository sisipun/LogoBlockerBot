import telebot
from telebot import types
import os

import configparser
from PIL import Image
from detection.logo_detector import detect_logo
from image.image_processor import process_image, ProcessMode
from image.rgb_hex_converter import is_rgb_hex, hex_to_rgb

config = configparser.ConfigParser()
config.read('resources/application.conf')
model_path = config['Config']['model_path']
telegram_token = config['Config']['telegram_token']
bot = telebot.TeleBot(telegram_token)

user_dict = {}
color_codes = {
    'Красный': (255, 0, 0),
    'Оранжевый': (255, 165, 0),
    'Желтый': (255, 255, 0),
    'Зеленый': (0, 255, 0),
    'Сининй': (0, 0, 255),
    'Фиолетовый': (128, 0, 128)
}
process_modes = {
    'Размытие': ProcessMode.BLUR,
    'Заполнение': ProcessMode.FILL,
    'Рамка': ProcessMode.BOUNDING_BOX
}
blur_force = {
    'Слабый': 5,
    'Средний': 20,
    'Сильный': 50
}
filter_force = {
    'Низкая': 0.3,
    'Средняя': 0.5,
    'Высокая': 0.7
}


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message,
                 'Привет, вы можете загрузить изображение и бот заблокирует логотипы на нем.')


@bot.message_handler(content_types=['photo'])
def image_message(message):
    file_id = message.photo[-1].file_id
    user_dict[message.chat.id] = {'file_id': file_id}
    message_with_markup(message,
                        'Выберите силу фильтрации из представленных или значение от 0 до 100% '
                        '(чем ниже тем сила фильтрации тем больше объектов будут заблокированны).',
                        ['Низкая', 'Средняя', 'Высокая'], get_filter_force)


def get_filter_force(message):
    if not user_dict[message.chat.id]:
        return

    force_answer = message.text
    filter_force_value = filter_force.get(force_answer)
    if not filter_force_value:
        if force_answer.isdigit() and 0 <= int(force_answer) <= 100:
            filter_force_value = int(force_answer) / 100
        else:
            message_with_markup(message, 'Значение должно быть от 0 до 100%.', ['Низкая', 'Средняя', 'Высокая'],
                                get_blur_force)
            return

    user_dict[message.chat.id]['filter_force'] = filter_force_value
    message_with_markup(message, 'Выберите режим работы блокировщика:', ['Размытие', 'Заполнение', 'Рамка'], get_mode)


def get_mode(message):
    if not user_dict[message.chat.id]:
        return

    mode_answer = message.text
    mode = process_modes.get(mode_answer)
    if not mode:
        message_with_markup(message, 'Можно выбрать только из существующих режимов:',
                            ['Размытие', 'Заполнение', 'Рамка'],
                            get_mode)
        return

    user_dict[message.chat.id]['mode'] = mode
    if mode == ProcessMode.BLUR:
        message_with_markup(message, 'Выберите силу размытия или введите значение от 1 до 100:',
                            ['Слабый', 'Средний', 'Сильный'],
                            get_blur_force)
    else:
        message_with_markup(message,
                            'Выберите один из существующих цветов или RGB hex (#****** или #***):',
                            ['Красный', 'Оранжевый', 'Желтый', 'Зеленый', 'Сининй', 'Фиолетовый'],
                            get_color)


def get_color(message):
    color_answer = message.text
    color_code = color_codes.get(color_answer)
    if not color_code:
        if is_rgb_hex(color_answer):
            color_code = hex_to_rgb(color_answer)
        else:
            message_with_markup(message,
                                'Значением может быть один из существующих цветов или RGB hex (#****** или #***)',
                                ['Красный', 'Оранжевый', 'Желтый', 'Зеленый', 'Сининй', 'Фиолетовый'],
                                get_color)
            return

    process_photo(message, user_dict[message.chat.id]['file_id'], user_dict[message.chat.id]['mode'], color=color_code,
                  filter_force=user_dict[message.chat.id]['filter_force'])


def get_blur_force(message):
    force_answer = message.text
    blur_force_value = blur_force.get(force_answer)
    if not blur_force_value:
        if force_answer.isdigit() and 0 < int(force_answer) <= 100:
            blur_force_value = int(force_answer)
        else:
            message_with_markup(message, 'Значение должно быть от 1 до 100.', ['Слабый', 'Средний', 'Сильный'],
                                get_blur_force)
            return

    process_photo(message, user_dict[message.chat.id]['file_id'], user_dict[message.chat.id]['mode'],
                  blur_force=blur_force_value, filter_force=user_dict[message.chat.id]['filter_force'])


def process_photo(message, file_id, mode, color=(255, 0, 0), blur_force=20, filter_force=0.5):
    bot.reply_to(message, 'Идет обработка изображения. Подождите...')
    bot_file = bot.get_file(file_id)
    downloaded_file = bot.download_file(bot_file.file_path)
    with open(bot_file.file_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    image = Image.open(bot_file.file_path).convert('RGB')
    detected_boxes = detect_logo(model_path, image, filter_force)
    processed_image = process_image(image, detected_boxes, mode, color, blur_force)
    processed_image.save(bot_file.file_path, 'PNG')
    with open(bot_file.file_path, 'rb') as sendPhoto:
        bot.send_photo(message.chat.id, sendPhoto)
    if os.path.exists(bot_file.file_path):
        os.remove(bot_file.file_path)
    user_dict[message.chat.id] = None


def message_with_markup(message, text, markup_variants, next_step=None):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*markup_variants)
    msg = bot.reply_to(message, text, reply_markup=markup)
    if next_step:
        bot.register_next_step_handler(msg, next_step)

bot.polling()
