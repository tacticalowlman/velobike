# -*- coding: utf-8 -*-
import json
import re
import sqlite3
from datetime import datetime

import smtplib                                      # Импортируем библиотеку по работе с SMTP

# Добавляем необходимые подклассы - MIME-типы
from email.mime.multipart import MIMEMultipart      # Многокомпонентный объект
from email.mime.text import MIMEText                # Текст/HTML
from email.mime.image import MIMEImage              # Изображения
import telebot
from telebot import types
from telebot.types import InputMediaPhoto

import text

bot = telebot.TeleBot(text.token, threaded=False)


class DB:
    conn = sqlite3.connect("velobike.db")  # Создание базы данных
    cursor: sqlite3.Connection = conn.cursor()



def send_mail(txt: str):
    addr_from = "Velobikeru@yandex.ru"                 # Адресат
    addr_to   = "andrey_kotovhe@mail.ru"                   # Получатель
    password  = "7415460Qq"                                  # Пароль

    msg = MIMEMultipart()                               # Создаем сообщение
    msg['From']    = addr_from                          # Адресат
    msg['To']      = addr_to                            # Получатель
    msg['Subject'] = 'Problem'                   # Тема сообщения

    body = txt
    msg.attach(MIMEText(body, 'plain'))                 # Добавляем в сообщение текст
    server = smtplib.SMTP('smtp.yandex.ru')           # Создаем объект SMTP
                       # Включаем режим отладки - если отчет не нужен, строку можно закомментировать
    server.starttls()                                   # Начинаем шифрованный обмен по TLS
    server.login(addr_from, password)                   # Получаем доступ
    server.send_message(msg)                            # Отправляем сообщение
    server.quit()   


def zero(user_id: int):
    DB.cursor.execute('update `users` set `tarifch` = ?, `reportst` = ? where `id` = ?', (0, 0, user_id))
    DB.conn.commit()


def newusercheck(user_id: int) -> bool:
    data = DB.cursor.execute('SELECT * FROM `users` WHERE `id` = ? AND `class` = ?', (user_id, 'user')).fetchone()
    return not bool(data)


def admincheck(admin_id: int) -> bool:
    data = DB.cursor.execute('SELECT * FROM `users` WHERE `id` = ? AND `class` = ?', (admin_id, 'admin')).fetchone()
    return bool(data)


def generate_lang_kb() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text='English', callback_data='eng'))
    buttons.append(types.InlineKeyboardButton(text='Русский', callback_data='rus'))
    keyboard.add(*buttons)
    return keyboard


def get_user_lang(user_id: int) -> str:
    sql = 'SELECT `language` FROM `users` WHERE `id` = ?'
    lang = DB.cursor.execute(sql, (user_id,)).fetchone()[0]
    return lang


def generate_main_menu_kb(user_id: int) -> types.InlineKeyboardMarkup:
    lang = get_user_lang(user_id)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = list()
    for i in range(6):
        buttons.append(types.InlineKeyboardButton(text=text.menu[i][lang], callback_data=f'menu{i}'))
    keyboard.add(*buttons)
    return keyboard


@bot.message_handler(commands=['reset'], func=lambda msg: msg.from_user.id == 396706690)  # Получить id юзера
def get_id(msg: types.Message):
    DB.cursor.execute('update `users` set `tarifch` = ?, `texts` = ?, `photos` = ?,  `photonum` = ?, `reportst` = ?, `reportst2` = ?, `reportnum` = ?, `declinerep` = ?', (0, '', '[]', 0, 0, 0, 0, 0))
    DB.conn.commit()
    bot.send_message(396706690, 'База данных обнулена')

@bot.message_handler(commands=['reset_me'], func=lambda msg: msg.from_user.id == 396706690)  # Получить id юзера
def get_id(msg: types.Message):
    DB.cursor.execute('update `users` set `tarifch` = ?, `texts` = ?, `photos` = ?,  `photonum` = ?, `reportst` = ?, `reportst2` = ?, `reportnum` = ?, `declinerep` = ? where `id` = ?', (0, '', '[]', 0, 0, 0, 0, 0, 396706690))
    DB.conn.commit()
    bot.send_message(396706690, 'База данных обнулена')


@bot.message_handler(commands=['get_id'])  # Получить id юзера
def get_id(msg: types.Message):
    bot.send_message(msg.chat.id, msg.from_user.id)


@bot.message_handler(commands=['get_chat_id'])  # Получить id чата
def get_chat_id(msg: types.Message):
    bot.send_message(msg.chat.id, msg.chat.id)


@bot.message_handler(commands=['start'], func=lambda msg: msg.chat.type == 'private')  # Хендлер пользовательского меню
def usermenu(msg: types.Message):
    if newusercheck(msg.from_user.id) and not (admincheck(msg.from_user.id)):
        DB.cursor.execute('insert into `users` (class, id) values (?, ?)', ('user', msg.from_user.id))
        DB.conn.commit()
        bot.send_message(msg.chat.id, 'Choose your language/Выберите ваш язык:', reply_markup=generate_lang_kb())
    else:
        zero(msg.from_user.id)
        lang = get_user_lang(msg.from_user.id)
        keyboard = generate_main_menu_kb(msg.from_user.id)
        bot.send_message(chat_id=msg.chat.id, text=text.hello[lang], reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'mainmenu')  # Хендлер пользовательского меню
def usermenu(c: types.CallbackQuery):
    if newusercheck(c.from_user.id) and not (admincheck(c.from_user.id)):
        DB.cursor.execute('insert into `users` (class, id) values (?, ?)', ('user', c.from_user.id))
        DB.conn.commit()
        bot.send_message(c.message.chat.id, 'Choose your language/Выберите ваш язык:', reply_markup=generate_lang_kb())
    else:
        zero(c.from_user.id)
        lang = get_user_lang(c.from_user.id)
        keyboard = generate_main_menu_kb(c.from_user.id)
        bot.send_message(chat_id=c.message.chat.id, text=text.hello[lang], reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data in ['eng', 'rus'])
def english(c: types.CallbackQuery):
    langs = ['eng', 'rus']
    DB.cursor.execute('update `users` set `language` = ? where `id` = ?', (langs.index(c.data), c.from_user.id))
    DB.conn.commit()
    lang = get_user_lang(c.from_user.id)
    keyboard = generate_main_menu_kb(c.from_user.id)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.hello[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'cmenu')
def cmenu(c: types.CallbackQuery):
    lang = get_user_lang(c.from_user.id)
    keyboard = generate_main_menu_kb(c.from_user.id)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.hello[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'menu0')
def menu0(c: types.CallbackQuery):
    lang = DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone()[0]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.howtouse[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'menu1')
def menu1(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = list()
    for i in range(3):
        buttons.append(types.InlineKeyboardButton(text=text.timerate[i][lang], callback_data='time:' + str(i)))
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.rate[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data.startswith('time:'))
def times(c: types.CallbackQuery):
    timetr = int(c.data.split(':')[1]) + 1
    DB.cursor.execute('update `users` set `tarifch` = ? where `id` = ?', (timetr, c.from_user.id))
    DB.conn.commit()
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = list()
    for i in range(2):
        buttons.append(types.InlineKeyboardButton(text=text.belaycbck[i][lang], callback_data='belay:' + str(i)))
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.belayt[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data.startswith('belay:'))
def belays(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    timetr = (DB.cursor.execute('select `tarifch` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    belaytr = int(c.data.split(':')[1]) + 1
    key = int(str(timetr) + str(belaytr))
    tarifcost = text.tarifs.get(key)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=tarifcost[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'menu2')
def menu2(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    texts = (DB.cursor.execute('select `texts` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = list()
    if texts == '':
        for i in range(4):
            buttons.append(types.InlineKeyboardButton(text=text.problems[i][lang], callback_data='problem' + str(i)))
        buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
        keyboard.add(*buttons)
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.manyproblems[lang],
                              reply_markup=keyboard)
    else:
        buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
        keyboard.add(*buttons)
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.cantreport[lang],
                              reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'problem0')
def reportstt(c: types.CallbackQuery):
    DB.cursor.execute('update `users` set `problemnum` = ? where `id` = ?', (0, c.from_user.id))
    DB.conn.commit()
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.sendrep[lang], callback_data='startread'))
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.sendproblema[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'startread')
def reportstt(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    problemnum = (DB.cursor.execute('select `problemnum` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    DB.cursor.execute('update `users` set `reportst` = ? where `id` = ?', (1, c.from_user.id))
    DB.conn.commit()
    if problemnum == 0:
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.describenumber[lang])
    elif problemnum == 1:
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.describenumberv[lang])
    elif problemnum == 2:
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.describelogin[lang])
    elif problemnum == 3:
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.describenumberv[lang])
    elif problemnum ==4:
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.describeproposal[lang])


@bot.message_handler(content_types=['text'], func=lambda msg:
(DB.cursor.execute('select `reportst` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[
    0] == 1 and msg.chat.type == 'private')
def readreport(msg: types.Message):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[0]
    texts = (DB.cursor.execute('select `texts` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[0]
    problemnum = (DB.cursor.execute('select `problemnum` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[0]
    if problemnum == 0:
        if texts == '':
            texts = text.problems[problemnum][lang] + ' ' + msg.text
            DB.cursor.execute('update `users` set `texts` = ? where `id` = ?', (texts, msg.from_user.id))
            DB.conn.commit()
            bot.send_message(chat_id=msg.chat.id, text=text.describeproblem[lang])
            texts = (DB.cursor.execute('select `texts` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[0]
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            buttons = list()
            buttons.append(types.InlineKeyboardButton(text=text.sendrep[lang], callback_data='reportst'))
            keyboard.add(*buttons)
            texts = texts + '\n' + msg.text
            DB.cursor.execute('update `users` set `texts` = ? where `id` = ?', (texts, msg.from_user.id))
            DB.conn.commit()
            bot.send_message(chat_id=msg.chat.id, text=text.sendphoto[lang],
                            reply_markup=keyboard)
    elif problemnum == 1:
        if texts == '':
            texts = text.problems[problemnum][lang] + ' ' + msg.text
            DB.cursor.execute('update `users` set `texts` = ? where `id` = ?', (texts, msg.from_user.id))
            DB.cursor.execute('update `users` set `spot` = ? where `id` = ?', (1, msg.from_user.id))
            DB.conn.commit()
            bot.send_message(chat_id=msg.chat.id, text=text.describenumber[lang])
            texts = (DB.cursor.execute('select `texts` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[0]
        elif (DB.cursor.execute('select `spot` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[0] == 1:
            texts = texts + '\n' + msg.text
            DB.cursor.execute('update `users` set `texts` = ? where `id` = ?', (texts, msg.from_user.id))
            DB.cursor.execute('update `users` set `spot` = ? where `id` = ?', (0, msg.from_user.id))
            DB.conn.commit()
            bot.send_message(chat_id=msg.chat.id, text=text.describeproblem[lang])
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            buttons = list()
            buttons.append(types.InlineKeyboardButton(text=text.sendrep[lang], callback_data='reportst'))
            keyboard.add(*buttons)
            texts = texts + '\n' + msg.text
            DB.cursor.execute('update `users` set `texts` = ? where `id` = ?', (texts, msg.from_user.id))
            DB.conn.commit()
            bot.send_message(chat_id=msg.chat.id, text=text.sendphoto[lang],
                            reply_markup=keyboard)
    elif problemnum == 2:
        texts = text.problems[problemnum][lang] + ' ' + msg.text
        DB.cursor.execute('update `users` set `texts` = ? where `id` = ?', (texts, msg.from_user.id))
        DB.conn.commit()
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        buttons = list()
        buttons.append(types.InlineKeyboardButton(text=text.sendrep[lang], callback_data='reportst'))
        keyboard.add(*buttons)
        bot.send_message(chat_id=msg.chat.id, text=text.describeproblem[lang], reply_markup=keyboard)
    elif problemnum == 3:
        if texts == '':
            texts = text.problems[problemnum][lang] + ' ' + msg.text
            DB.cursor.execute('update `users` set `texts` = ? where `id` = ?', (texts, msg.from_user.id))
            DB.cursor.execute('update `users` set `spot` = ? where `id` = ?', (1, msg.from_user.id))
            DB.conn.commit()
            bot.send_message(chat_id=msg.chat.id, text=text.describenumber[lang])
            texts = (DB.cursor.execute('select `texts` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[0]
        elif (DB.cursor.execute('select `spot` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[0] == 1:
            texts = texts + '\n' + msg.text
            DB.cursor.execute('update `users` set `texts` = ? where `id` = ?', (texts, msg.from_user.id))
            DB.cursor.execute('update `users` set `spot` = ? where `id` = ?', (0, msg.from_user.id))
            DB.conn.commit()
            bot.send_message(chat_id=msg.chat.id, text=text.describeproblem[lang])
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            buttons = list()
            buttons.append(types.InlineKeyboardButton(text=text.sendrep[lang], callback_data='reportst'))
            keyboard.add(*buttons)
            texts = texts + '\n' + msg.text
            DB.cursor.execute('update `users` set `texts` = ? where `id` = ?', (texts, msg.from_user.id))
            DB.conn.commit()
            bot.send_message(chat_id=msg.chat.id, text=text.sendphoto[lang],
                            reply_markup=keyboard)
    elif problemnum == 4:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        buttons = list()
        buttons.append(types.InlineKeyboardButton(text=text.sendrep[lang], callback_data='reportst'))
        keyboard.add(*buttons)
        texts = texts + '\n' + msg.text
        DB.cursor.execute('update `users` set `texts` = ? where `id` = ?', (texts, msg.from_user.id))
        DB.conn.commit()
        bot.send_message(chat_id=msg.chat.id, text=text.sendphoto[lang],
                        reply_markup=keyboard)



@bot.message_handler(content_types=['photo'], func=lambda msg:
(DB.cursor.execute('select `reportst` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[
    0] == 1 and msg.chat.type == 'private')
def readreportpt(msg: types.Message):
    photonum = \
        (DB.cursor.execute('select `photonum` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[0]
    photonum = photonum + 1
    DB.cursor.execute('update `users` set `photonum` = ? where `id` = ?', (photonum, msg.from_user.id))
    if photonum <= 3:
        photos = \
            (DB.cursor.execute('select `photos` from `users` where `id` = ?', (msg.from_user.id,)).fetchone())[0]
        photos = json.loads(photos)
        photos.append(msg.photo[0].file_id)
        photos = json.dumps(photos)
        DB.cursor.execute('update `users` set `photos` = ? where `id` = ?', (photos, msg.from_user.id))
    DB.conn.commit()


@bot.callback_query_handler(func=lambda c: c.data == 'reportst')
def sendrep(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    texts = (DB.cursor.execute('select `texts` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    if texts != '':
        requests = (DB.cursor.execute('select `requests` from `mains`').fetchone())[0]
        requests = requests + 1
        DB.cursor.execute('update `users` set `reportnum` = ?, `reportst` = ? where `id` = ?',
                          (requests, 0, c.from_user.id))
        moderchat = (DB.cursor.execute('select `moderchat` from `mains`').fetchone())[0]
        photonum = \
            (DB.cursor.execute('select `photonum` from `users` where id = ?', (c.from_user.id,)).fetchone())[0]
        reptime = datetime.now().strftime("%d-%m-%Y %H:%M")
        textr = texts
        texts = '{} Заявка #{}\n{}\n'.format(reptime, requests, textr)
        keyboardm = types.InlineKeyboardMarkup(row_width=2)
        buttonsm = list()
        for i in range(3):
            buttonsm.append(
                types.InlineKeyboardButton(text=text.accept[i], callback_data='manswer' + str(i) + ':' + str(requests)))
        keyboardm.add(*buttonsm)
        bot.send_message(moderchat, texts, reply_markup=keyboardm)
        DB.cursor.execute('update `mains` set `requests` = ?', (requests,))
        DB.conn.commit()
        if photonum != 0:
            sql = 'select `photos` from `users` where `id` = ?'
            photos = (DB.cursor.execute(sql, (c.from_user.id,)).fetchone())[0]
            photos = json.loads(photos)
            inphotos = [InputMediaPhoto(i) for i in photos]
            bot.send_media_group(moderchat, inphotos)
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        buttons = list()
        buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='mainmenu'))
        keyboard.add(*buttons)
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text=text.reportsended[lang].format(requests), reply_markup=keyboard)
    else:
        DB.cursor.execute('update `users` set `reportst` = ? where `id` = ?', (0, c.from_user.id))
        DB.conn.commit()
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        buttons = list()
        buttons.append(types.InlineKeyboardButton(text=text.reportback[lang], callback_data='problem0'))
        buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
        keyboard.add(*buttons)
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                              text=text.reportnotsended[lang], reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data.startswith('manswer0:'))
def answer0(c: types.CallbackQuery):
    requests = int(c.data.split(":")[1])
    userid = (DB.cursor.execute('select `id` from `users` where `reportnum` = ?', (requests,)).fetchone())[0]
    texts = (DB.cursor.execute('select `texts` from `users` where `id` = ?', (userid,)).fetchone())[0]
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (userid,)).fetchone())[0]
    DB.cursor.execute('update `users` set `texts` = ?, `photos` = ?, `photonum` = ? where `id` = ?',
                      ('', '[]', 0, userid))
    DB.conn.commit()
    bot.send_message(userid, text.succeed[lang].format(requests))
    m = [f'Сообщение об ошибке номер #{requests} было отправлено команде поддержки.']
    reptime = datetime.now().strftime("%d-%m-%Y %H:%M")
    textr = texts
    texts = '{} Заявка #{}\n{}\n'.format(reptime, requests, textr)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=texts + '\n' + '\n'.join(m))


@bot.callback_query_handler(func=lambda c: c.data.startswith('manswer1'))
def answer1(c: types.CallbackQuery):
    requests = int(c.data.split(":")[1])
    DB.cursor.execute('update `users` set `declinerep` = ? where `reportnum` = ?', (1, requests))
    DB.conn.commit()
    m = [
        f'В ответ на это сообщение напишите причину, по которой сообщение об ошибке номер #{requests} было отклонено.'
    ]
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text='\n'.join(m))


@bot.callback_query_handler(func=lambda c: c.data.startswith('manswer2'))
def answer2(c: types.CallbackQuery):
    requests = int(c.data.split(":")[1])
    m = [
        'В ответ на это сообщение напишите причину, '
        f'по которой сообщение об ошибке номер #{requests} требует дополнительной информации.'
    ]
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text='\n'.join(m))


@bot.message_handler(content_types=['text'], func=lambda msg: msg.reply_to_message and not msg.chat.type == 'private')
def readreport(msg: types.Message):
    request = int(re.findall(r'^\D*(\d+)', msg.reply_to_message.text)[0])
    userid = (DB.cursor.execute('select `id` from `users` where `reportnum` = ?', (request,)).fetchone())[0]
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (userid,)).fetchone())[0]
    texts = (DB.cursor.execute('select `texts` from `users` where `id` = ?', (userid,)).fetchone())[0]
    decline = (DB.cursor.execute('select `declinerep` from `users` where `id` = ?', (userid,)).fetchone())[0]
    if decline == 1:
        bot.send_message(userid, text.declined[lang].format(request, msg.text))
        m = [f'Сообщение об ошибке номер #{request} было отклонено.']
        reptime = datetime.now().strftime("%d-%m-%Y %H:%M")
        textr = texts
        texts = '{} Заявка #{}\n{}\n'.format(reptime, request, textr)
        bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.reply_to_message.message_id, text=texts + '\n' + '\n'.join(m))
        sql = 'update `users` set `texts` = ?, `photos` = ?, `photonum` = ?, `declinerep` = ? where `id` = ?'
        DB.cursor.execute(sql, ('', '[]', 0, 0, userid))
        DB.conn.commit()
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = list()
        buttons.append(types.InlineKeyboardButton(text=text.solved[lang], callback_data='solved'))
        buttons.append(types.InlineKeyboardButton(text=text.notsolved[lang], callback_data='notsolved'))
        keyboard.add(*buttons)
        bot.send_message(userid, text.delayed[lang].format(request, msg.text), reply_markup=keyboard)
        m = [f'Дополнительная информация по сообщению об ошибке номер #{request} была доставлена отправителю.']
        reptime = datetime.now().strftime("%d-%m-%Y %H:%M")
        textr = texts
        texts = '{} Заявка #{}\n{}\n'.format(reptime, request, textr)
        bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.reply_to_message.message_id,
                              text=texts + '\n' + '\n'.join(m))


@bot.callback_query_handler(func=lambda c: c.data == 'solved')
def solved(c: types.CallbackQuery):
    request = int(re.findall(r'^\D*(\d+)', c.message.text)[0])
    userid = (DB.cursor.execute('select `id` from `users` where `reportnum` = ?', (request,)).fetchone())[0]
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id,
                          text=text.problemclear[lang].format(request))
    DB.cursor.execute('update `users` set `texts` = ?, `photos` = ?, `photonum` = ? where `id` = ?',
                      ('', '[]', 0, userid))
    DB.conn.commit()


@bot.callback_query_handler(func=lambda c: c.data == 'notsolved')
def notsolved(c: types.CallbackQuery):
    request = int(re.findall(r'^\D*(\d+)', c.message.text)[0])
    DB.cursor.execute('update `users` set `reportst2` = ? where `id` = ?', (1, c.from_user.id))
    DB.conn.commit()
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    bot.delete_message(chat_id=c.message.chat.id, message_id=c.message.message_id)
    bot.send_message(chat_id=c.message.chat.id, text=text.respondtext[lang].format(request)
                                                , reply_markup=types.ForceReply())


@bot.message_handler(content_types=['text'], func=lambda msg: msg.reply_to_message and msg.chat.type == 'private')
def sendreport2(msg: types.Message):
    DB.cursor.execute('update `users` set `reportst2` = ? where `id` = ?', (0, msg.from_user.id))
    moderchat = (DB.cursor.execute('select `moderchat` from `mains`').fetchone())[0]
    DB.conn.commit()
    request = int(re.findall(r'^\D*(\d+)', msg.reply_to_message.text)[0])
    userid = (DB.cursor.execute('select `id` from `users` where `reportnum` = ?', (request,)).fetchone())[0]
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (userid,)).fetchone())[0]
    texts = (DB.cursor.execute('select `texts` from `users` where `id` = ?', (userid,)).fetchone())[0]
    reptime = datetime.now().strftime("%d-%m-%Y %H:%M")
    texts = texts + ' ' + msg.text
    textr = texts
    texts = '{} Заявка #{}\n{}\n'.format(reptime, request, textr)
    keyboardm = types.InlineKeyboardMarkup(row_width=3)
    buttonsm = list()
    for i in range(3):
        buttonsm.append(
            types.InlineKeyboardButton(text=text.accept[i], callback_data='manswer' + str(i) + ':' + str(request)))
    keyboardm.add(*buttonsm)
    bot.send_message(moderchat, texts, reply_markup=keyboardm)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='mainmenu'))
    keyboard.add(*buttons)
    bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
    bot.send_message(chat_id=msg.chat.id, text=text.reportsended[lang].format(request)
                                                , reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'problem1')
def reportstt(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    DB.cursor.execute('update `users` set `reportst` = ? where `id` = ?', (1, c.from_user.id))
    DB.cursor.execute('update `users` set `problemnum` = ? where `id` = ?', (1, c.from_user.id))
    DB.conn.commit()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.sendrep[lang], callback_data='startread'))
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.sendproblema[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'problem2')
def reportstt(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    DB.cursor.execute('update `users` set `problemnum` = ? where `id` = ?', (2, c.from_user.id))
    DB.conn.commit()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.payednm[lang], callback_data='payedm'))
    buttons.append(types.InlineKeyboardButton(text=text.backmm[lang], callback_data='backm'))
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.sendproblema[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'payedm')
def reportstt(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    DB.cursor.execute('update `users` set `reportst` = ? where `id` = ?', (1, c.from_user.id))
    DB.conn.commit()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.sendrep[lang], callback_data='startread'))
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.describest3[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'backm')
def menu5(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.backmoney[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'problem3')
def reportstt(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    DB.cursor.execute('update `users` set `problemnum` = ? where `id` = ?', (3, c.from_user.id))
    DB.conn.commit()
    DB.cursor.execute('update `users` set `reportst` = ? where `id` = ?', (1, c.from_user.id))
    DB.conn.commit()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.sendrep[lang], callback_data='startread'))
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.sendproblema[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'menu3')
def menu3(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.contacts[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'menu4')
def menu4(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.que[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'menu5')
def menu2(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    texts = (DB.cursor.execute('select `texts` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = list()
    if texts == '':
        for i in range(4):
            buttons.append(types.InlineKeyboardButton(text=text.proposals[i][lang], callback_data='proposal'))
        buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
        keyboard.add(*buttons)
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.whatsay[lang],
                              reply_markup=keyboard)
    else:
        buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
        keyboard.add(*buttons)
        bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.cantreport[lang],
                              reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'proposal')
def reportstt(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    DB.cursor.execute('update `users` set `reportst` = ? where `id` = ?', (1, c.from_user.id))
    DB.cursor.execute('update `users` set `problemnum` = ? where `id` = ?', (4, c.from_user.id))
    DB.conn.commit()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.sendprop[lang], callback_data='startread'))
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.describest4[lang],
                          reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == 'menu6')
def menu6(c: types.CallbackQuery):
    lang = (DB.cursor.execute('select `language` from `users` where `id` = ?', (c.from_user.id,)).fetchone())[0]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buttons = list()
    buttons.append(types.InlineKeyboardButton(text=text.back[lang], callback_data='cmenu'))
    keyboard.add(*buttons)
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=text.not_ready[lang],
                          reply_markup=keyboard)


while True:
    try:
        bot.polling(timeout=1, interval=1)
    except KeyboardInterrupt:
        print(1)
        break
    except Exception as e:
        bot.send_message(396706690, e)
        # time.sleep(5)
