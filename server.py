import os

import requests

import telebot
from telebot import types

import db
from keyboards import (
    get_send_location_button,
    get_inline_location_button,
    get_inline_show_more_button,
    get_inline_delete_button,
)

from model import (
    get_location_info,
    get_coords_by_id,
    get_more_location_info,
)
import model
from datatypes import PlaceInfo, Suggestion, Coordinates
from environment import ENV


API_TOKEN = os.getenv("TELEGRAM_BOT_API_TOKEN")
if not API_TOKEN:
    print("Add telegram bot api token as environment variable")
    exit()

bot = telebot.TeleBot(API_TOKEN)

try:
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS").split(',')]
except:
    ADMIN_IDS = []


def set_commands() -> None:
    bot_command_list = [
        types.BotCommand("start", "Начать"),
        types.BotCommand("suggest", "Предложить место"),
    ]
    bot.set_my_commands(bot_command_list)


@bot.message_handler(commands=["start", "help"])
def send_welcome(message: types.Message):
    bot.send_message(
        message.chat.id,
        "Я нахожу dog-friendly места по близости.\n"
        "Просто отправь свое местоположение.\n",
        reply_markup=get_send_location_button(),
    )


@bot.message_handler(content_types=["location"])
def send_results(message: types.Message):
    loc = message.location
    results = get_location_info(loc.latitude, loc.longitude, message.chat.id)

    for res in results:
        bot.send_photo(
            message.chat.id,
            res.photo,
            f"{res.name}\n\n"
            f"{res.address}\n\n"
            f"В {res.dist}км от вас.",
            reply_markup=get_inline_location_button(res.id),
        )

    bot.send_message(
        message.chat.id,
        "Не нашли подходящее место?",
        reply_markup=get_inline_show_more_button(message.chat.id)
    )


@bot.callback_query_handler(func=lambda call: call.data.split(':')[0] == 'loc')
def show_location_callback(call: types.CallbackQuery):
    loc = get_coords_by_id(int(call.data.split(':')[1]))
    if loc is not None:
        bot.send_location(call.message.chat.id, loc.lat, loc.lon)
    else:
        bot.send_message(call.message.chat.id, "Not found :(")


@bot.callback_query_handler(func=lambda call: call.data.split(':')[0] == 'chat')
def show_more_locations_callback(call: types.CallbackQuery):
    chat_id = int(call.data.split(':')[1])
    results = get_more_location_info(chat_id)
    if results is not None:
        for res in results:
            bot.send_photo(
                call.message.chat.id,
                res.photo,
                f"{res.name}\n\n"
                f"{res.address}\n\n"
                f"В {res.dist}км от вас.",
                reply_markup=get_inline_location_button(res.id),
            )
        ENV.pop(chat_id)
        bot.delete_message(call.message.chat.id, call.message.id)
    else:
        bot.send_message(call.message.chat.id, "Not found :(")


@bot.message_handler(commands=["suggest"])
def get_suggestion(message: types.Message):
    sent = bot.send_message(message.chat.id, "Название:")
    answer = Suggestion(None, None, None, None)
    bot.register_next_step_handler(sent, get_name, answer)


def get_name(message: types.Message, answer: Suggestion):
    if isinstance(message.text, str):
        answer.name = message.text
        sent = bot.send_message(message.chat.id, "Адрес:");
        bot.register_next_step_handler(sent, get_address, answer)
    else:
        bot.send_message(message.chat.id, "Ошибка");


def get_address(message: types.Message, answer: Suggestion):
    if isinstance(message.text, str):
        answer.address = message.text
        sent = bot.send_message(message.chat.id, "Описание:");
        bot.register_next_step_handler(sent, get_description, answer)
    else:
        bot.send_message(message.chat.id, "Ошибка");


def get_description(message: types.Message, answer: Suggestion):
    if isinstance(message.text, str):
        answer.description = message.text
        sent = bot.send_message(message.chat.id, "Фото:");
        bot.register_next_step_handler(sent, get_photo, answer)
    else:
        bot.send_message(message.chat.id, "Ошибка");


def get_photo(message: types.Message, answer: Suggestion):
    if message.photo is None:
        answer.photo = None
    elif len(message.photo) > 0:
        ordered = sorted(message.photo, key=lambda val: val.file_size)
        f_info = bot.get_file(ordered[-1].file_id)
        url = f'https://api.telegram.org/file/bot{API_TOKEN}/{f_info.file_path}'
        file = requests.get(url)
        if file.status_code == 200:
            answer.photo = file.content
        else:
            answer.photo = None
    db.insert_suggestion(answer)
    bot.send_message(message.chat.id, "Предложение отправлено.");


@bot.message_handler(content_types=['text'])
def send_suggestion_to_admin(message: types.Message):
    if (message.from_user.id in ADMIN_IDS):
        if message.text.lower() == 'предложения':
            suggestions = db.fetch_suggestions()
            for sug in suggestions:
                if sug[4] is None:
                    bot.send_message(
                        message.chat.id,
                        f"Название: {sug[1]}\n"
                        f"Адрес: {sug[2]}\n"
                        f"Описание: {sug[3]}\n",
                        reply_markup=get_inline_delete_button(sug[0])
                    )
                else:
                    bot.send_photo(
                        message.chat.id,
                        photo=sug[4],
                        caption= f"Название: {sug[1]}\n"
                                 f"Адрес: {sug[2]}\n"
                                 f"Описание: {sug[3]}\n",
                        reply_markup=get_inline_delete_button(sug[0])
                    )
        if message.text.lower() == 'добавить':
            answer = PlaceInfo(None, None, None, None, None, None)
            sent = bot.send_message(message.chat.id, "Название: ");
            bot.register_next_step_handler(sent, get_name_add, answer)


@bot.callback_query_handler(func=lambda call: call.data.split(':')[0] == 'sug')
def show_location_callback(call: types.CallbackQuery):
    sug_id = int(call.data.split(':')[1])
    db.delete_suggestion(sug_id)
    bot.send_message(call.message.chat.id, "Удалено")


def get_name_add(message: types.Message, answer: PlaceInfo):
    if isinstance(message.text, str):
        answer.name = message.text
        sent = bot.send_message(message.chat.id, "Адрес:");
        bot.register_next_step_handler(sent, get_address_add, answer)
    else:
        bot.send_message(message.chat.id, "Ошибка");


def get_address_add(message: types.Message, answer: PlaceInfo):
    if isinstance(message.text, str):
        answer.address = message.text
        sent = bot.send_message(message.chat.id, "Местоположение:");
        bot.register_next_step_handler(sent, get_location_add, answer)
    else:
        bot.send_message(message.chat.id, "Ошибка");


def get_location_add(message: types.Message, answer: PlaceInfo):
    loc = message.location
    if loc is not None:
        answer.loc = Coordinates(loc.latitude, loc.longitude)
        sent = bot.send_message(message.chat.id, "Фото:");
        bot.register_next_step_handler(sent, get_description, answer)
    else:
        bot.send_message(message.chat.id, "Ошибка");


def get_photo_add(message: types.Message, answer: PlaceInfo):
    photo = message.photo
    if photo is not None and len(photo) > 0:
        ordered = sorted(photo, key=lambda val: val.file_size)
        f_info = bot.get_file(ordered[-1].file_id)
        url = f'https://api.telegram.org/file/bot{API_TOKEN}/{f_info.file_path}'
        file = requests.get(url)
        if file.status_code == 200:
            answer.photo = file.content
        else:
            answer.photo = None
        ordered = sorted(model.data, key=lambda val: val.id)
        answer.id = ordered[-1].id
        data.append(answer)
    else:
        bot.send_message(message.chat.id, "Ошибка");


if __name__ == "__main__":
    set_commands()
    bot.infinity_polling()
