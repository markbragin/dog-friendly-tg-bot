from telebot.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup
from telebot.util import quick_markup


def get_send_location_button() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Send location", request_location=True))
    return keyboard


def get_inline_location_button(id: int) -> InlineKeyboardMarkup:
    return quick_markup({'Где это?': {'callback_data': f'loc:{id}'}})


def get_inline_show_more_button(chat_id: int) -> InlineKeyboardMarkup:
    return quick_markup({'Показать еще': {'callback_data': f'chat:{chat_id}'}})


def get_inline_delete_button(sug_id: int) -> InlineKeyboardMarkup:
    return quick_markup({'Удалить': {'callback_data': f'sug:{sug_id}'}})
