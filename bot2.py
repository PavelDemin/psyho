import botSql
import telebot
from telebot import types
import logging
from gsheets import gsheets
import requests
import re
import config
import time
import random

# ----------------------------------------------------------------------
token = config.token  # this
admin_password = 'QAZwsx123321'
# ----------------------------------------------------------------------

logging.basicConfig(level=logging.DEBUG)
bot = telebot.TeleBot(token)
db = botSql.bot_sql()
gs = gsheets()


def get_keyboard() -> list:
    keyboard = []
    for i in gs.get_list_worksheets():
        keyboard.append(i.title)
    return keyboard


def user_banned_define(user_id, chat_id):
    if db.is_user_banned(user_id):
        bot.send_message(chat_id, "Вы заблокированы администротором!")
        return True


def display_texts_content(id, off, block=None):
    logging.debug('handler display_text_content, var off={}, block={}'.format(off, block))
    if block is None:
        text_list = gs.get_all_values_from_worksheet(db.get_user(id)[4])
    else:
        text_list = gs.get_all_values_from_worksheet(int(block))
    logging.debug('len(text_list) = {}'.format(len(text_list)))
    if off < len(text_list) - 1:
        if text_list[off][1] != "":  # button exists
            logging.debug('Button exists!')
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(text=text_list[off][1], callback_data=str(block) + ',' + str(off + 1)))
            regex = r"(jpg|png|gif|bmp|jpeg)"
            if re.search(regex, text_list[off][0]) is None:
                s = text_list[off][0]
                if len(s) > 4096:
                    while s:
                        tmp = s[:s.rfind('.', 0, 4096) + 1]
                        bot.send_message(id, tmp, parse_mode='Markdown',
                                         disable_web_page_preview=True)
                        s = s[s.rfind('.', 0, 4096) + 1:]
                        if len(s) < 4096:
                            bot.send_message(id, s, reply_markup=markup, parse_mode='Markdown',
                                             disable_web_page_preview=True)
                            break
                else:
                    bot.send_message(id, text_list[off][0], reply_markup=markup, parse_mode='Markdown',
                                     disable_web_page_preview=True)
            else:
                with requests.session() as s:
                    request = s.get(text_list[off][0])
                    if request.status_code == 200:
                        file = s.get(text_list[off][0]).content
                        bot.send_photo(id, photo=file, reply_markup=markup)
                    else:
                        bot.send_message(id, 'Невозможно загрузить фото')
        else:
            m = bot.send_message(id, text_list[off][0], parse_mode='Markdown')
            bot.register_next_step_handler(m, lambda m: answer_for_question(m, str(off + 1), str(block),
                                                                            text_list[off][0]))
    elif off == len(text_list) - 1:
        m = bot.send_message(id, text_list[off][0], parse_mode='Markdown')
        bot.register_next_step_handler(m, lambda m: feedback_at_end_of_block(m, block))


@bot.message_handler(commands=['start'])
def start_message(message):
    if user_banned_define(message.from_user.id, message.chat.id):
        return
    register_user(message)
    m = bot.send_message(message.chat.id, "Для доступа введите пароль:")
    bot.register_next_step_handler(m, access_handler)


@bot.message_handler(commands=['admin'])
def admin_message(message):
    if not db.is_user_already_in_table(message.from_user.id):
        register_user(message)
    if user_banned_define(message.from_user.id, message.chat.id):
        return
    m = bot.send_message(message.chat.id, "Введите пароль администратора:")
    bot.register_next_step_handler(m, admin_password_handler)


@bot.callback_query_handler(func=lambda call: True)
def inline_button_pressed_handler(message):
    if user_banned_define(message.from_user.id, message.from_user.id):
        return
    chat_id = message.from_user.id
    if message.data == "-1":
        display_texts_content(chat_id, 0)
        return
    if message.data == "-2":
        m = bot.send_message(chat_id, "Введите ID:")
        bot.register_next_step_handler(m, user_ban_handler)
        return
    if message.data == "-3":
        m = bot.send_message(chat_id, "Введите текст рассылки:")
        bot.register_next_step_handler(m, send_message_all_users)
        return
    if message.data == "-4":
        i = 0
        pasw = []
        while i < 50:
            pasw.append(db.randomString())
            db.add_password(pasw[i])
            i += 1
        str = ''
        for p in pasw:
            str += p + '\n'
        with open('pasw.txt', 'w') as file:
            file.write(str)
        bot.send_document(config.admin, open('pasw.txt', 'rb'))
        return
    if not db.is_user_already_in_table(message.from_user.id):
        register_user(message)
    bot.send_chat_action(chat_id, 'typing')
    display_texts_content(chat_id, int(message.data.split(',')[1]), int(message.data.split(',')[0]))


@bot.message_handler(content_types=['photo'])
def feedback_photo(message):
    if user_banned_define(message.from_user.id, message.chat.id):
        return
    file_id = message.photo[-1].file_id
    bot.send_photo(config.admin, file_id)


@bot.message_handler(content_types=["text"])
def jump_bottom_keyboard_block(message):
    if user_banned_define(message.from_user.id, message.chat.id):
        return
    text = message.text
    if text in get_keyboard():
        index = get_keyboard().index(text)
        if not db.is_user_already_in_table(message.from_user.id):
            register_user(message)
        completed = db.get_user(message.from_user.id)[4]
        logging.debug("Run jump_bottom_keyboard_block")
        if completed >= index:
            display_texts_content(message.chat.id, 0, index)
        else:
            bot.send_message(message.chat.id, "Вы пока не имеете доступ к данному блоку!")


def display_bottom_keyboard(id):
    user_markup = types.ReplyKeyboardMarkup(row_width=5, resize_keyboard=True, one_time_keyboard=False)
    user_markup.add(*[types.KeyboardButton(name) for name in get_keyboard()])
    bot.send_message(id, "❤️❤️❤️", reply_markup=user_markup)


def feedback_at_end_of_block(message, block):
    logging.debug('Feedback end of LAST block, len(gs.get_list_worksheets()={} End block: {}'.format(
        len(gs.get_list_worksheets()), db.get_user(message.chat.id)[4]))

    if block + 1 < len(gs.get_list_worksheets()):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='Перейти к следующему блоку',
                                              callback_data=str(block + 1) + ',' + str(0)))
        bot.send_message(message.chat.id, 'Спасибо за отзыв!', reply_markup=markup)
        send_message_to_admin(message, f'Ответ на отзыв Блока № {block + 1}')
    elif block + 1 == len(gs.get_list_worksheets()):
        bot.send_message(message.chat.id, 'Спасибо за отзыв! Это был последний блок!')
        send_message_to_admin(message, 'Ответ на отзыв Заключительного Блока')

    if db.get_user(message.chat.id)[4] == block and db.get_user(message.chat.id)[4] < len(gs.get_list_worksheets()):
        db.update_user_blocks(message.chat.id, db.get_user(message.chat.id)[4] + 1)


def answer_for_question(message, off, block, text):
    if message.content_type == 'photo':
        logging.debug('Answer for question is type: photo')
        file_id = message.photo[-1].file_id
        bot.send_photo(config.admin, file_id, caption=f'Фото от @{message.from_user.username}')
    else:
        logging.debug('Answer for question is type: text.')
        send_message_to_admin(message, text)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Следующее задание', callback_data=str(block) + ',' + str(off)))
    bot.send_message(message.chat.id, 'Ответ принят!', reply_markup=markup)


def send_message_to_admin(message, text, admin_id=config.admin):
    msg = f'Сообщение от ID:{message.from_user.id} на вопрос *{text}*:\n\n'
    bot.send_message(admin_id, text=msg + message.text, parse_mode='Markdown')


def send_message_all_users(message):
    users_id_list = (users_id[0] for users_id in db.get_all_users())
    for user_id in users_id_list:
        bot.send_message(user_id, message.text, parse_mode='Markdown')
        time.sleep(random.random())
    bot.send_message(config.admin, 'Рассылка произведена!')


def admin_password_handler(message):
    chat_id = message.chat.id
    answer = message.text
    markup = types.InlineKeyboardMarkup()
    # markup.add(types.InlineKeyboardButton(text="Закрыть",
    #                                      callback_data="-1"))
    if answer == admin_password:
        display_user_list(chat_id, markup)
    else:
        bot.send_message(chat_id, "Пароль не верный", reply_markup=markup)


def str_default(s):
    if s is None:
        return ""
    else:
        return s


def display_user_list(chat_id, markup):
    a = "Список пользователей:\n"
    users = db.get_all_users()
    counter = 1
    for user in users:
        a += str(counter) + ".  <b>ID</b> = " + str(user[0]) \
             + " , <b>Имя:</b> " + str_default(user[1]) \
             + " <b>Фамилия:</b> " + str_default(user[2]) \
             + " <b>Имя пользователя:</b> " + str_default(user[3]) \
             + " <b>Блоков пройдено:</b> " + str(user[4]) \
             + " <b>Заблокирован:</b> " + ("Нет" if user[5] == 0 else "Да") + "\n\n"
        counter = counter + 1
    markup.add(types.InlineKeyboardButton(text="Заблокировать/разблокировать пользователя",
                                          callback_data="-2"))
    markup.add(types.InlineKeyboardButton(text="Сделать рассылку",
                                          callback_data="-3"))
    markup.add(types.InlineKeyboardButton(text="Сгенерировать пароли",
                                          callback_data="-4"))
    bot.send_message(chat_id, a, reply_markup=markup, parse_mode='HTML')


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
    db.add_new_user(_id, _f_name, _l_name, '@' + _username, 0)


def user_ban_handler(message):
    chat_id = message.chat.id
    answer = 0
    markup = types.InlineKeyboardMarkup()
    # markup.add(types.InlineKeyboardButton(text="Закрыть",
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
            db.ban_user(answer, True)
            bot.send_message(chat_id, "Пользователь разблокирован")
        else:
            db.ban_user(answer, False)
            bot.send_message(chat_id, "Пользователь заблокирован")
    else:
        bot.send_message(chat_id, "ID не найден")
    display_user_list(chat_id, markup)


def access_handler(message):
    chat_id = message.chat.id
    answer = message.text
    if db.password_proc(answer):
        display_bottom_keyboard(message.chat.id)
        display_texts_content(message.chat.id, 0, 0)
    else:
        bot.send_message(chat_id, "Пароль не найден либо уже активирован! Попробуйте еще раз /start")


bot.polling(none_stop=True)
