from telebot import types

from db import PostDatabase

import configparser
import telebot


config = configparser.ConfigParser()
config.read('config.ini')

TOKEN = config['ApiKeys']['tg_token']
bot = telebot.TeleBot(TOKEN)

def send_article(message, photo_link):
    chat_id = config['Settings']['tg_chanel_id']
    # Добавляем форматирование Markdown для выделения текста жирным
    bot.send_photo(chat_id, photo_link, caption=message, parse_mode="Markdown")

def send_test_article(art_id, message, photo_link):
    chat_id = config['Settings']['tg_chat_id']
    
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Отменить пост", callback_data=f'disable/{art_id}')
    markup.add(button)
    # Добавляем форматирование Markdown для выделения текста жирным
    bot.send_photo(chat_id, photo_link, reply_markup=markup, caption=message, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    art_id = call.data.split('/')[1]
    if 'disable' in call.data:
        new_markup = types.InlineKeyboardMarkup()
        new_button = types.InlineKeyboardButton(text="Активировать пост", callback_data=f'activate/{art_id}')
        new_markup.add(new_button)
        db = PostDatabase()
        db.update_active_status(art_id, 0)
        db.close()
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=new_markup)
        bot.answer_callback_query(call.id, 'Отменено')
    
    if 'activate' in call.data:
        new_markup = types.InlineKeyboardMarkup()
        new_button = types.InlineKeyboardButton(text="Отменить пост", callback_data=f'disabled/{art_id}')
        new_markup.add(new_button)
        db = PostDatabase()
        db.update_active_status(art_id, 1)
        db.close()
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=new_markup)
        bot.answer_callback_query(call.id, 'Активировано')