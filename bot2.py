import bot2texts as t
import botSql
import telebot
import urllib.request
import time
from telebot import *
import logging
import re

# TODO #1:  block move save
# TODO #2:  feedback save
#----------------------------------------------------------------------
token = t.token # this
admin_password = 'AAGdxK5ZyTLi6x'
#----------------------------------------------------------------------

logging.basicConfig(level=logging.DEBUG)
bot = telebot.TeleBot(token)
db = botSql.bot_sql()

def user_banned_define(user_id,chat_id):
    if db.is_user_banned(user_id):
        bot.send_message(chat_id, "Вы заблокированы администротором!")
        return True

def display_texts_content(off,id):
    print("Value Off: ", off)
    if off > len(t.texts) - 1:
        return
    str1 = ""
    if isinstance(t.texts[off][0][0], tuple):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text=t.texts[off][1][0],
                                              callback_data=str(off+1)))
        bot.send_photo(id, photo=open(t.texts[off][0][0][0], 'rb'),reply_markup=markup)
        return
    for i in range(len(t.texts[off][0]) -1):
        str1 += t.texts[off][0][i] + "\n\n"
    if len(t.texts[off][0]) > 1:
        bot.send_message(id, str1)
    dispay_text_buttons(off,id)

def dispay_text_buttons(off,id):
    markup = types.InlineKeyboardMarkup()
    if len(t.texts[off][1]) > 0:
        for i in t.texts[off][1]:
            if isinstance(i, tuple):
                markup.add(types.InlineKeyboardButton(text=i[0],
                                                      callback_data=str(i[1])))
            else:
                markup.add(types.InlineKeyboardButton(text=i,
                                                      callback_data=str(off + 1)))

        bot.send_message(id, t.texts[off][0][-1], reply_markup=markup, parse_mode='Markdown', disable_web_page_preview=True)
    else:
       m = bot.send_message(id, t.texts[off][0][-1])
       bot.register_next_step_handler(m, lambda m : feedback_at_end_of_block(m,str(off+1)))

@bot.message_handler(commands=['start'])
def start_message(message):
    if user_banned_define(message.from_user.id,message.chat.id):
        return
    register_user(message)
    m = bot.send_message(message.chat.id, "Для доступа введите пароль:")
    bot.register_next_step_handler(m, acsess_handler)

#    display_bottom_keyboard(message.chat.id)
#    display_texts_content(0, message.chat.id)

@bot.message_handler(commands=['admin'])
def admin_message(message):
    if not db.is_user_already_in_table(message.from_user.id):
        register_user(message)
    if user_banned_define(message.from_user.id,message.chat.id):
        return
    m = bot.send_message(message.chat.id, "Введите пароль администратора:")
    bot.register_next_step_handler(m, admin_password_handler)

@bot.callback_query_handler(func=lambda call: True)
def inline_button_pressed_handler(message):
    if user_banned_define(message.from_user.id,message.from_user.id):
        return
    chat_id = message.from_user.id
    print(message.data)
    if message.data == "-1":
        display_texts_content(0, chat_id)
        return
    if message.data == "-2":
        m = bot.send_message(chat_id, "Введите ID:")
        bot.register_next_step_handler(m, user_ban_handler)
        return
    if not db.is_user_already_in_table(message.from_user.id):
            register_user(message)
    if int(message.data) in t.keyboard_jump:                      # todo 1
         iw = t.keyboard_jump.index(int(message.data))
         if db.get_user(message.from_user.id)[4] < iw:
               db.update_user_blocks(message.from_user.id, iw)
    display_texts_content(int(message.data), chat_id)


@bot.message_handler(content_types=['photo'])
def feedback_photo(message):
    if user_banned_define(message.from_user.id,message.chat.id):
        return
    print( 'message.photo =', message.photo)
    fileID = message.photo[-1].file_id
    print('fileID =', fileID)
    file = bot.get_file(fileID)
    print ('file.file_path =', file.file_path)
    downloaded_file = bot.download_file(file.file_path)
    with open("photos"/fileID +".jpg", 'wb') as new_file:
        new_file.write(downloaded_file)

@bot.message_handler(content_types=["text"])
def jump_bottom_keyboard_block(message):
    if user_banned_define(message.from_user.id,message.chat.id):
        return
    text = message.text
    if text in t.keyboard:
        index = t.keyboard.index(text)
        if not db.is_user_already_in_table(message.from_user.id):
            register_user(message)
        completed = db.get_user(message.from_user.id)[4]
        print(completed,index)
        if completed >= index:
            display_texts_content(t.keyboard_jump[index], message.chat.id)
        else:
            bot.send_message(message.chat.id, "Вы пока не имеете доступ к данному блоку!")

def display_bottom_keyboard(id):
    user_markup = types.ReplyKeyboardMarkup(row_width=5, resize_keyboard=True, one_time_keyboard=False)
    user_markup.add(*[types.KeyboardButton(name) for name in t.keyboard])
    m = bot.send_message(id, "❤️❤️❤️", reply_markup=user_markup)

def feedback_at_end_of_block(message,off):
    chat_id = message.chat.id
    answer = message.text
    _id = message.from_user.id
    _f_name = message.from_user.first_name
    _l_name = message.from_user.last_name
    _username = message.from_user.username
    if _f_name is None:
        _f_name = ""
    if _l_name is None:
        _l_name = ""
    if _username is None:
       _username = ""
    try:


        print(str( ("Отзыв от пльзователя " + _f_name + "  " + _l_name + "Ник: @" + _username).encode('utf-8') ))
        email_test_send.smtp_send_email( str( ("Отзыв от пльзователя " + _f_name + "  " + _l_name + "Ник: @" + _username).encode('utf-8') ), answer)

    except Exception as e:
        print('smtp',e)
    display_texts_content(int(off), chat_id)

def admin_password_handler(message):
    chat_id = message.chat.id
    answer = message.text
    markup = types.InlineKeyboardMarkup()
    #markup.add(types.InlineKeyboardButton(text="Закрыть",
    #                                      callback_data="-1"))
    if answer == admin_password:
        display_user_list(chat_id,markup)
    else:
        bot.send_message(chat_id, "Пароль не верный", reply_markup=markup)

def str_default(s):
    if s is None:
        return ""
    else:
        return s


def display_user_list(chat_id,markup):
    a = "Список пользователей:\n"
    users = db.get_all_users()
    counter = 1
    for user in users:
        a += str(counter) + ".  *ID* = " + str(user[0]) + " , *Имя:* " + str_default(user[1]) + " *Фамилия:* " + str_default(user[
            2]) + " *Имя пользователя:* " + str_default(user[3]) \
             + " *Блоков пройдено:* " + str(user[4]) + " *Заблокирован:* " + ("Нет" if user[5] == 0 else "Да" )+ "\n\n"
        counter = counter + 1
    markup.add(types.InlineKeyboardButton(text="Заблокировать/разблокировать пользователя",
                                          callback_data="-2"))
    bot.send_message(chat_id, a, reply_markup=markup, parse_mode='Markdown')


def register_user(message):
    _id = message.from_user.id
    _f_name = message.from_user.first_name
    _l_name = message.from_user.last_name
    _username = message.from_user.username
    if _f_name is None:
        _f_name = ""
    if _l_name is None:
        _l_name = ""
    if _username is None:
       _username = ""
    db.add_new_user(_id,_f_name , _l_name, '@' + _username, 0)


def user_ban_handler(message):
    chat_id = message.chat.id
    answer = 0
    markup = types.InlineKeyboardMarkup()
    #markup.add(types.InlineKeyboardButton(text="Закрыть",
    #                                      callback_data="-1"))
    try:
        answer = int(message.text)
    except:
        bot.send_message(chat_id, "ID не найден")
        display_user_list(chat_id, markup)
        return
    if db.is_user_already_in_table(answer):
        status = db.get_user(answer)[5]
        if status:
            db.ban_user(answer,True)
            bot.send_message(chat_id, "Пользователь разблокирован")
        else:
            db.ban_user(answer,False)
            bot.send_message(chat_id, "Пользователь заблокирован")
    else:
        bot.send_message(chat_id, "ID не найден")
    display_user_list(chat_id, markup)

def acsess_handler(message):
    chat_id = message.chat.id
    answer = message.text
    if db.password_proc(answer):
        display_bottom_keyboard(message.chat.id)
        display_texts_content(0, message.chat.id)
    else:
        bot.send_message(chat_id, "Пароль не найден либо уже активирован!")





bot.polling(none_stop=True)






if not "HEROKU" in list(os.environ.keys()):

    pass
else:

    pass
