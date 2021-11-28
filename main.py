import re
import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InputMediaPhoto, InputMediaVideo
import asyncio
import sqlite3 as sql
from config import TELEGRAM_TOKEN, ADMIN_CHAT_ID, ADMIN_LIST, DEFAULT_ADDRESS, MODER_CHAT_ID


class Choise(StatesGroup):
    category = State()
    product = State()
    buy_stay = State()
    wait_accept = State()
    profile = State()

    admin_category = State()
    admin_product_name = State()
    admin_product_description = State()
    admin_photo = State()
    admin_product_price = State()
    admin_product_count = State()
    admin_product_house_is_default = State()
    admin_house = State()
    admin_flat = State()
    admin_accept = State()


categories = [
    'Продукты',
    'Электроника',
    'Для дома',
    'Аренда',
    'Разное'
]

houses = [
    1.1,
    1.2,
    1.3,
    2,
    3.1,
    3.2,
    4,
    5.1,
    5.2,
    5.3,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    27,
    28,
    29,
    30
]

cur_settings = {}

admin_settings = {}

answers = {}

times = {}

is_continue = False

msg = ''

con = sql.connect('base.db')
cursor = con.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS base(
	userid INTEGER PRIMARY KEY,
	username STRING,
	buy_sum INTEGER,
	sell_sum INTEGER,
	house INTEGER,
	flat INTEGER
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS products(
	product_id INTEGER PRIMARY KEY,
	category STRING,
	product_count INTEGER,
	product_name STRING,
	product_description STRING,
	product_price INTEGER,
	product_house INTEGER,
	product_flat INTEGER,
	product_photo STRING,
	userid INTEGER
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS requests(
    request_id INTEGER PRIMARY KEY,
	category STRING,
	product_count INTEGER,
	product_name STRING,
	product_description STRING,
	product_price INTEGER,
	product_house INTEGER,
	product_flat INTEGER,
	product_photo STRING,
	userid INTEGER
)""")

cursor.execute(f"""CREATE TABLE IF NOT EXISTS buys(
    buyer_id INTEGER,
    product_id INTEGER,
    buy_name STRING,
    buy_count INTEGER,
    buy_price INTEGER,
    buy_description STRING,
    buy_house INTEGER,
    buy_flat INTEGER,
    buy_status INTEGER,
    buy_datetime INTEGER,
    buy_photo STRING,
    buy_id INTEGER PRIMARY KEY,
    seller_id INTEGER,
    buyer_status STRING,
    seller_status STRING,
    category STRING
)""")

con.commit()

storage = MemoryStorage()
bot = Bot(TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=storage)

back = types.KeyboardButton("Назад")
menu = types.KeyboardButton("Меню")

sht1 = types.KeyboardButton("1 шт")
sht2 = types.KeyboardButton("2 шт")
sht3 = types.KeyboardButton("3 шт")
sht4 = types.KeyboardButton("4 шт")
sht5 = types.KeyboardButton("5 шт")

tobuy = types.KeyboardButton("Купить")
tosell = types.KeyboardButton("Продать")
profile = types.KeyboardButton("Профиль")
helpy = types.KeyboardButton("Поддержка")
info = types.KeyboardButton("Инфо")

accept = types.KeyboardButton("Подтверждаю")

buys = types.KeyboardButton("Покупки")
sells = types.KeyboardButton("Продажи")

keyboard_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_menu.add(menu)

keyboard_profile = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_profile.add(buys, sells)
keyboard_profile.add(menu)

keyboard_accept = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_accept.add(accept)
keyboard_accept.add(menu)

keyboard_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_main.add(tobuy, tosell)
keyboard_main.add(profile)
keyboard_main.add(info, helpy)

keyboard_sht = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_sht.add(back, menu)
keyboard_sht.add(sht1, sht2, sht3, sht4, sht5)


keyboard_admin_accept = types.ReplyKeyboardMarkup(resize_keyboard=True)
accs = types.KeyboardButton("Подтвердить")
edit = types.KeyboardButton("Редактировать")
canc = types.KeyboardButton("Отмена")
keyboard_admin_accept.add(accs)
keyboard_admin_accept.add(edit)
keyboard_admin_accept.add(canc)


def keyboard_last_buys_or_sells(buy_list, tip):
    keyboard = types.InlineKeyboardMarkup()
    i = 1
    timeless = []
    for buy in buy_list:
        aa = datetime.datetime.fromtimestamp(buy[9])
        buy_time = datetime.datetime.strftime(aa, "%H:%M:%S %d.%m.%Y")
        buy_name = buy[2]
        buy_id = buy[11]
        name = f"{buy_name} | {buy_time}"
        timeless.append(types.InlineKeyboardButton(text=name, callback_data=f'{tip}_{buy_id}'))
        if i % 2 == 0:
            keyboard.add(timeless[0], timeless[1])
            timeless = []
        i += 1
    if i % 2 == 0:
        keyboard.add(timeless[0])
    return keyboard


def keyboard_moder(request_id):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Добавить", callback_data=f"request_accept_{request_id}"))
    keyboard.add(types.InlineKeyboardButton("Редактировать", callback_data=f"request_edit_{request_id}"))
    keyboard.add(types.InlineKeyboardButton("Отменить", callback_data=f"request_decline_{request_id}"))
    return keyboard


def keyboard_contact(user_id, tip, buy_id, message):
    cursor = con.cursor()
    cursor.execute(f"SELECT username FROM base WHERE userid == ?", (user_id,))
    username = cursor.fetchone()[0]

    cursor.execute(f"SELECT buy_status, buyer_status, seller_status FROM buys WHERE buy_id == ?", (buy_id,))
    buy_status, buyer_status, seller_status = cursor.fetchone()

    keyboard = types.InlineKeyboardMarkup()
    print(message.from_user.username)
    if 'Ожидание' in buy_status:
        if tip == 'buyer':
            keyboard.add(types.InlineKeyboardButton(f"Связаться с продавцом",
                                                    callback_data=f"tg_{user_id}",
                                                    url=f"t.me/{username}"))
            if buyer_status != 'access':
                keyboard.add(types.InlineKeyboardButton("Завершить", callback_data=f"buyer_access_{buy_id}"))
            keyboard.add(types.InlineKeyboardButton("Отменить", callback_data=f"buyer_decline_{buy_id}"))
        elif tip == 'seller':
            keyboard.add(types.InlineKeyboardButton(f"Связаться с покупателем",
                                                    callback_data=f"tg_{user_id}",
                                                    url=f"t.me/{username}"))
            if seller_status != 'access':
                keyboard.add(types.InlineKeyboardButton("Завершить", callback_data=f"seller_access_{buy_id}"))
            keyboard.add(types.InlineKeyboardButton("Отменить", callback_data=f"seller_decline_{buy_id}"))
    keyboard.add(types.InlineKeyboardButton("Меню", callback_data="menu"))
    return keyboard


def keyboard_categories(categories):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    i = 1
    timeless = []
    keyboard.add(menu)
    for prod in categories:
        timeless.append(types.KeyboardButton(prod))
        if i % 2 == 0:
            keyboard.add(timeless[0], timeless[1])
            timeless = []
        i += 1
    if i % 2 == 0:
        keyboard.add(timeless[0])
    return keyboard


def keyboard_buy(prod_list):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(back, menu)
    for prod in prod_list:
        keyboard.add(types.KeyboardButton(prod))
    return keyboard


def separator(price):
    perv = f"{price:,}"
    return perv.replace(",", ".")


def get_ids(buy_id):
    cursor.execute(f"SELECT buyer_id, seller_id FROM buys WHERE buy_id == ?",
                   (buy_id,))
    buyer_id, seller_id = cursor.fetchone()
    return buyer_id, seller_id


async def access_all(buy_id):
    buyer_id, seller_id = get_ids(buy_id)
    await bot.send_message(buyer_id, f"Сделка <b>№{buy_id}</b> успешно завершена \u2705",
                           parse_mode=types.ParseMode.HTML)
    await bot.send_message(seller_id, f"Сделка <b>№{buy_id}</b> успешно завершена \u2705",
                           parse_mode=types.ParseMode.HTML)


async def access_buyer(buy_id):
    buyer_id, seller_id = get_ids(buy_id)
    await bot.send_message(seller_id,
                           f"Покупатель подтвердил сделку <b>№{buy_id}</b>. Ожидание подтверждения...",
                           reply_markup=keyboard_main,
                           parse_mode=types.ParseMode.HTML)


async def access_seller(buy_id):
    buyer_id, seller_id = get_ids(buy_id)
    await bot.send_message(buyer_id,
                           f"Продавец подтвердил сделку <b>№{buy_id}</b>. Ожидание подтверждения...",
                           reply_markup=keyboard_main,
                           parse_mode=types.ParseMode.HTML)


async def decline_buyer(buy_id):
    buyer_id, seller_id = get_ids(buy_id)
    await bot.send_message(buyer_id, f"Сделка <b>№{buy_id}</b> была отменена покупателем \u274c",
                           parse_mode=types.ParseMode.HTML,
                           reply_markup=keyboard_main)
    await bot.send_message(seller_id, f"Сделка <b>№{buy_id}</b> была отменена покупателем \u274c",
                           parse_mode=types.ParseMode.HTML,
                           reply_markup=keyboard_main)


async def decline_seller(buy_id):
    buyer_id, seller_id = get_ids(buy_id)
    await bot.send_message(buyer_id, f"Сделка <b>№{buy_id}</b> была отменена продавцом \u274c",
                           parse_mode=types.ParseMode.HTML)
    await bot.send_message(seller_id, f"Сделка <b>№{buy_id}</b> была отменена продавцом \u274c",
                           parse_mode=types.ParseMode.HTML)


def edit_statuses(tip, new_status, buy_id):
    cursor = con.cursor()

    cursor.execute(f"SELECT buyer_status, seller_status FROM buys WHERE buy_id == ?",
                   (buy_id,))
    old_buyer_status, old_seller_status = cursor.fetchone()

    cursor.execute(f"SELECT buyer_id, seller_id FROM buys WHERE buy_id == ?",
                   (buy_id,))
    buyer_id, seller_id = cursor.fetchone()

    cursor.execute(f"UPDATE buys SET {tip}_status = ? WHERE buy_id == ?",
                   (new_status, buy_id))
    con.commit()

    cursor.execute(f"SELECT buyer_status, seller_status FROM buys WHERE buy_id == ?",
                   (buy_id,))
    buyer_status, seller_status = cursor.fetchone()


    if not(old_buyer_status == buyer_status and old_seller_status == seller_status):
        if buyer_status == 'decline' or seller_status == 'decline':
            cursor.execute(f"UPDATE buys SET buy_status = ? WHERE buy_id == ?",
                           ('Отменено', buy_id))
            con.commit()

            recover_product(buy_id)
            if buyer_status == 'decline' and seller_status != 'decline':
                cursor.execute(f"UPDATE buys SET buyer_status = ? WHERE buy_id == ?",
                               ('decline', buy_id))
                con.commit()
                return 'decline_buyer'
            elif buyer_status != 'decline' and seller_status == 'decline':
                cursor.execute(f"UPDATE buys SET seller_status = ? WHERE buy_id == ?",
                               ('decline', buy_id))
                con.commit()
                return 'decline_seller'
        elif buyer_status == 'access' and seller_status == 'access':
            cursor.execute(f"UPDATE buys SET buy_status = ? WHERE buy_id == ?",
                           ('Выполнено', buy_id))
            cursor.execute(f"SELECT buy_sum FROM base WHERE userid == ?",
                           (buyer_id,))
            old_buyer_sum = cursor.fetchone()[0]
            cursor.execute(f"SELECT buy_sum FROM base WHERE userid == ?",
                           (seller_id,))
            old_seller_sum = cursor.fetchone()[0]
            cursor.execute(f"SELECT buy_price, buy_count FROM buys WHERE buy_id == ?",
                           (buy_id,))
            buy_price, buy_count = cursor.fetchone()

            new_sum = buy_price * buy_count
            new_buyer_sum = old_buyer_sum + new_sum
            new_seller_sum = old_seller_sum + new_sum

            cursor.execute(f"UPDATE base SET buy_sum = ? WHERE userid == ?",
                           (new_buyer_sum, buyer_id))
            cursor.execute(f"UPDATE base SET sell_sum = ? WHERE userid == ?",
                           (new_seller_sum, seller_id))
            con.commit()

            return 'access_all'
        elif buyer_status == 'access' and seller_status == 'neutral':
            cursor.execute(f"UPDATE buys SET buy_status = ? WHERE buy_id == ?",
                           ('Ожидание продавца', buy_id))
            con.commit()
            return 'access_buyer'
        elif buyer_status == 'neutral' and seller_status == 'access':
            cursor.execute(f"UPDATE buys SET buy_status = ? WHERE buy_id == ?",
                           ('Ожидание покупателя', buy_id))
            con.commit()
            return 'access_seller'


def recover_product(buy_id):
    buy = get_buy_by_id(buy_id)

    settings = {
        'category': buy[15],
        'product': {
            'name': buy[2],
            'price': buy[4],
            'count': buy[3],
            'description': buy[5],
            'house': buy[6],
            'flat': buy[7],
            'photo': buy[10],
            'seller_id': buy[12],
            'buyer_id': buy[0]
        }
    }

    cursor.execute(f"SELECT product_id FROM products")
    last_id = cursor.fetchall()
    if len(last_id) > 0:
        last_id = last_id[-1][0]
    else:
        last_id = 0

    cursor.execute(f"SELECT product_id, product_count FROM products WHERE category == ? AND "
                   f"product_name == ? AND product_price == ? AND userid == ?",
                   (settings['category'], settings['product']['name'],
                    settings['product']['price'], settings['product']['seller_id']))

    res = cursor.fetchone()
    if (res is not None) and (len(res) > 0):
        cursor.execute(f"UPDATE products SET product_count = ? WHERE product_id == ?",
                       (res[1] + settings['product']['count'], res[0]))
    else:
        cursor.execute(f"INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (last_id + 1,
                        settings['category'],
                        settings['product']['count'],
                        settings['product']['name'],
                        settings['product']['description'],
                        settings['product']['price'],
                        settings['product']['house'],
                        settings['product']['flat'],
                        settings['product']['photo'],
                        settings['product']['seller_id']
                        ))
    con.commit()


def if_not_reg(message):
    if message.chat.id == message.from_user.id:
        cursor = con.cursor()
        cursor.execute(f"SELECT userid FROM base WHERE userid == {message.from_user.id}")
        if cursor.fetchone() is None:
            cursor.execute(f"INSERT INTO base VALUES (?, ?, ?, ?, ?, ?)",
                           (message.from_user.id, message.from_user.username, 0, 0, 0, 0))
            con.commit()


def del_request_from_base(req_id):
    cursor = con.cursor()
    cursor.execute(f"DELETE FROM requests WHERE request_id == ?",
                   (req_id,))
    con.commit()


async def next_req_to_moder(message):
    cursor = con.cursor()

    cursor.execute(f"SELECT * FROM requests")
    request = cursor.fetchall()

    if (request is None) or (len(request) == 0):
        await bot.send_message(message.chat.id, 'Больше запросов нет.')
        return

    request = request[0]

    settings = {
        'req_id': request[0],
        'category': request[1],
        'product': {
            'name': request[3],
            'price': request[5],
            'count': request[2],
            'description': request[4],
            'house': request[6],
            'flat': request[7],
            'photo': request[8],
            'seller_id': request[9]
        }
    }

    if settings['product']['photo'] is not None:
        await bot.send_photo(MODER_CHAT_ID, caption="Запрос на добавление:\n"
                                                    f"<b>ID:</b> {settings['req_id']}\n"
                                                    f"Категория: {settings['category']}\n"
                                                    f"Название: {settings['product']['name']}\n"
                                                    f"Цена: {settings['product']['price']}\n"
                                                    f"Количество: {settings['product']['count']}\n"
                                                    f"Итог: {settings['product']['count'] * settings['product']['price']}\n\n"
                                                    f"Дом: {settings['product']['house']}\n"
                                                    f"Комната: {settings['product']['flat']}\n\n"
                                                    f"Описание: {settings['product']['description']}",
                             photo=settings['product']['photo'],
                             reply_markup=keyboard_moder(settings['req_id']),
                             parse_mode=types.ParseMode.HTML)
    else:
        await bot.send_message(MODER_CHAT_ID, "Запрос на добавление:\n"
                                              f"<b>ID:</b> {settings['req_id']}\n"
                                              f"Категория: {settings['category']}\n"
                                              f"Название: {settings['product']['name']}\n"
                                              f"Цена: {settings['product']['price']}\n"
                                              f"Количество: {settings['product']['count']}\n"
                                              f"Итог: {settings['product']['count'] * settings['product']['price']}\n\n"
                                              f"Дом: {settings['product']['house']}\n"
                                              f"Комната: {settings['product']['flat']}\n\n"
                                              f"Описание: {settings['product']['description']}",
                               reply_markup=keyboard_moder(settings['req_id']),
                             parse_mode=types.ParseMode.HTML)


async def decline_request(reason, message):
    reason = reason.lower()
    try:
        wow = reason.split()
        req_id = wow[1]
        reason = ' '.join(wow[2::])
        reason = reason[0].upper() + reason[1::]

        try:
            cursor = con.cursor()

            cursor.execute(f"SELECT * FROM requests WHERE request_id == ?",
                           (req_id,))
            request = cursor.fetchone()

            if (request is None) or (len(request) == 0):
                return False

            settings = {
                'category': request[1],
                'product': {
                    'name': request[3],
                    'price': request[5],
                    'count': request[2],
                    'description': request[4],
                    'house': request[6],
                    'flat': request[7],
                    'photo': request[8],
                    'seller_id': request[9]
                }
            }

            del_request_from_base(req_id)

            if settings['product']['photo'] is not None:
                await bot.send_photo(settings['product']['seller_id'],
                                     caption="Ваш запрос был отклонен по причине:\n"
                                     f"<b>{reason}</b>\n\n"
                                     f"Категория: {settings['category']}\n"
                                     f"Название: {settings['product']['name']}\n"
                                     f"Цена: {settings['product']['price']}\n"
                                     f"Количество: {settings['product']['count']}\n"
                                     f"Итог: {settings['product']['count'] * settings['product']['price']}\n\n"
                                     f"Дом: {settings['product']['house']}\n"
                                     f"Комната: {settings['product']['flat']}\n\n"
                                     f"Описание: {settings['product']['description']}",
                                     reply_markup=keyboard_main,
                                     photo=settings['product']['photo'],
                                     parse_mode=types.ParseMode.HTML)
            else:
                await bot.send_message(settings['product']['seller_id'],
                                       "Ваш запрос был отклонен по причине:\n"
                                       f"<b>{reason}</b>\n\n"
                                       f"Категория: {settings['category']}\n"
                                       f"Название: {settings['product']['name']}\n"
                                       f"Цена: {settings['product']['price']}\n"
                                       f"Количество: {settings['product']['count']}\n"
                                       f"Итог: {settings['product']['count'] * settings['product']['price']}\n\n"
                                       f"Дом: {settings['product']['house']}\n"
                                       f"Комната: {settings['product']['flat']}\n\n"
                                       f"Описание: {settings['product']['description']}",
                                       reply_markup=keyboard_main,
                                       parse_mode=types.ParseMode.HTML)

            await bot.send_message(message.chat.id, 'Запрос успешно отклонен.')

            return True
        except Exception as ex:
            print('Ошибка удаления запроса  ' + str(ex))
            return False

    except Exception as ex:
        print(str(ex))
        await bot.send_message(message.chat.id, 'Введите корректно отказ.')


def add_tovar_buy_request(req_id):
    try:
        cursor = con.cursor()

        cursor.execute(f"SELECT * FROM requests WHERE request_id == ?",
                       (req_id,))
        request = cursor.fetchone()
        settings = {
            'category': request[1],
            'product': {
                'name': request[3],
                'price': request[5],
                'count': request[2],
                'description': request[4],
                'house': request[6],
                'flat': request[7],
                'photo': request[8],
                'seller_id': request[9]
            }
        }
        cursor.execute(f"SELECT product_id FROM products")
        last_id = cursor.fetchall()
        if len(last_id) > 0:
            last_id = last_id[-1][0]
        else:
            last_id = 0

        cursor.execute(f"SELECT product_id, product_count FROM products WHERE category == ? AND "
                       f"product_name == ? AND product_price == ? AND userid == ?",
                       (settings['category'], settings['product']['name'],
                        settings['product']['price'], settings['product']['seller_id']))

        res = cursor.fetchone()
        if (res is not None) and (len(res) > 0):
            cursor.execute(f"UPDATE products SET product_count = ? WHERE product_id == ?",
                           (res[1] + settings['product']['count'], res[0]))
        else:
            cursor.execute(f"INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (last_id + 1,
                        settings['category'],
                        settings['product']['count'],
                        settings['product']['name'],
                        settings['product']['description'],
                        settings['product']['price'],
                        settings['product']['house'],
                        settings['product']['flat'],
                        settings['product']['photo'],
                        settings['product']['seller_id']
                        ))
        del_request_from_base(req_id)
        con.commit()
        return True
    except Exception as ex:
        print('ошибка добавление товара через запрос  ' + str(ex))
        return False


def add_tovar(settings, seller_id):
    try:
        cursor = con.cursor()

        cursor.execute(f"SELECT product_id FROM products")

        last_id = cursor.fetchall()
        if len(last_id) > 0:
            last_id = last_id[-1][0]
        else:
            last_id = 0

        cursor.execute(f"INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (last_id + 1,
                        settings['category'],
                        settings['product']['count'],
                        settings['product']['name'],
                        settings['product']['description'],
                        settings['product']['price'],
                        settings['product']['house'],
                        settings['product']['flat'],
                        settings['product']['photo'],
                        seller_id
                        ))
        con.commit()

        return True
    except Exception as ex:
        print('ошибка добавление товара админом  ' + str(ex))
        return False


async def request_tovar(settings, seller_id):
    try:
        cursor = con.cursor()

        cursor.execute(f"SELECT request_id FROM requests")

        last_id = cursor.fetchall()
        if len(last_id) > 0:
            last_id = last_id[-1][0]
        else:
            last_id = 0

        request_id = last_id + 1

        cursor.execute(f"INSERT INTO requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (request_id,
                        settings['category'],
                        settings['product']['count'],
                        settings['product']['name'],
                        settings['product']['description'],
                        settings['product']['price'],
                        settings['product']['house'],
                        settings['product']['flat'],
                        settings['product']['photo'],
                        seller_id))
        con.commit()

        if settings['product']['photo'] is not None:
            await bot.send_photo(MODER_CHAT_ID, caption="Запрос на добавление:\n"
                                                  f"<b>ID:</b> {request_id}\n"
                                                  f"Категория: {settings['category']}\n"
                                                  f"Название: {settings['product']['name']}\n"
                                                  f"Цена: {settings['product']['price']}\n"
                                                  f"Количество: {settings['product']['count']}\n"
                                                  f"Итог: {settings['product']['count'] * settings['product']['price']}\n\n"
                                                  f"Дом: {settings['product']['house']}\n"
                                                  f"Комната: {settings['product']['flat']}\n\n"
                                                  f"Описание: {settings['product']['description']}",
                                                  photo=settings['product']['photo'],
                                                  reply_markup=keyboard_moder(request_id),
                             parse_mode=types.ParseMode.HTML)
        else:
            await bot.send_message(MODER_CHAT_ID, "Запрос на добавление:\n"
                                              f"<b>ID:</b> {request_id}\n"
                                              f"Категория: {settings['category']}\n"
                                              f"Название: {settings['product']['name']}\n"
                                              f"Цена: {settings['product']['price']}\n"
                                              f"Количество: {settings['product']['count']}\n"
                                              f"Итог: {settings['product']['count'] * settings['product']['price']}\n\n"
                                              f"Дом: {settings['product']['house']}\n"
                                              f"Комната: {settings['product']['flat']}\n\n"
                                              f"Описание: {settings['product']['description']}",
                                              reply_markup=keyboard_moder(request_id),
                             parse_mode=types.ParseMode.HTML)

        return True
    except Exception as ex:
        print('ошибка добавление товара админом  ' + str(ex))
        return False


def get_tovar_list():
    products = ''
    for category in categories:
        cursor.execute(f"SELECT * FROM products WHERE category == ?", (category,))
        tovari_fetchall = cursor.fetchall()
        if len(tovari_fetchall) > 0:
            products += '<b>' + category + ':</b>\n'
            for product in tovari_fetchall:
                tovar = f"{product[3]} | <b>{separator(product[5])}</b> руб/шт | " \
                        f"Осталось: {separator(product[2])} шт.\n"
                products += tovar
            products += '\n'
    return products


def get_all_categories():
    cursor = con.cursor()
    cursor.execute(f"SELECT category FROM products")
    buy_fetchall = set()
    for s in cursor.fetchall():
        buy_fetchall.add(s[0])
    buy_fetchall = sorted(buy_fetchall)
    return buy_fetchall


def get_product_list_by_category(category):
    products = []
    cursor.execute(f"SELECT * FROM products WHERE category == ?", (category,))
    tovari_fetchall = cursor.fetchall()
    for product in tovari_fetchall:
        tovar = f"{product[3]} | {separator(product[5])} руб/шт | \n" \
                f"Осталось: {separator(product[2])} шт.\n"
        products.append(tovar)
    return products


def find_product_in_category(message):
    prod = message.text
    cur_prod = None
    cursor = con.cursor()
    cursor.execute(f"SELECT * FROM products WHERE category == ?",
                   (cur_settings[message.from_user.id]['category'],))
    prods_fetchall = cursor.fetchall()
    for product in prods_fetchall:
        if str(product[3]) in prod and str(separator(product[5])) in prod:
            cur_prod = product
    return cur_prod


def get_tovar_count(message):
    cursor = con.cursor()
    cursor.execute(f"SELECT product_count FROM products WHERE product_id == ?",
                   (cur_settings[message.from_user.id]['product'][0],))
    all_kol = cursor.fetchone()[0]
    return all_kol


def get_buy_sum(message):
    cursor = con.cursor()
    cursor.execute(f"SELECT buy_sum FROM base WHERE userid == {message.from_user.id}")
    buy_sum = cursor.fetchone()[0]
    return buy_sum


def get_sell_sum(message):
    cursor = con.cursor()
    cursor.execute(f"SELECT sell_sum FROM base WHERE userid == {message.from_user.id}")
    sell_sum = cursor.fetchone()[0]
    return sell_sum


def get_buy_by_id(buy_id):
    cursor = con.cursor()
    cursor.execute(f"SELECT * FROM buys WHERE buy_id == ?",
                   (buy_id,))
    buy = cursor.fetchone()
    return buy


def get_buys(message):
    cursor = con.cursor()
    cursor.execute(f"SELECT * FROM buys WHERE buyer_id == ?",
                   (message.from_user.id,))
    buys = cursor.fetchall()[::-1]
    return buys


def get_sells(message):
    cursor = con.cursor()
    cursor.execute(f"SELECT * FROM buys WHERE seller_id == ?",
                   (message.from_user.id,))
    sells = cursor.fetchall()[::-1]
    return sells


def change_count(message):
    cursor = con.cursor()
    cursor.execute(f"UPDATE products SET product_count = ? WHERE product_id == ?",
                   (cur_settings[message.from_user.id]['product'][2] - cur_settings[message.from_user.id]['kol'],
                    cur_settings[message.from_user.id]['product'][0]))
    con.commit()
    cursor.execute(f"SELECT product_count FROM products WHERE product_id == ?",
                   (cur_settings[message.from_user.id]['product'][0],))
    cnt = cursor.fetchone()[0]
    if cnt == 0:
        cursor.execute(f"DELETE FROM products WHERE product_id == ?",
                       (cur_settings[message.from_user.id]['product'][0],))
        con.commit()


def update_sums(message, new_buy_sum, new_sell_sum):
    cursor = con.cursor()
    cursor.execute(f"UPDATE base SET buy_sum = ? WHERE userid == ?",
                   (new_buy_sum,
                    message.from_user.id))
    cursor.execute(f"UPDATE base SET sell_sum = ? WHERE userid == ?",
                   (new_sell_sum,
                    message.from_user.id))
    con.commit()


async def get_buy_info(tip, buy_id, message):
    buy = get_buy_by_id(buy_id)
    buy_time = ' в '.join(datetime.datetime.strftime(datetime.datetime.fromtimestamp(buy[9]),
                                                     "%d.%m.%Y %H:%M:%S").split())
    buy_info = {
        'buy_category': buy[15],
        'buyer_id': buy[0],
        'seller_id': buy[12],
        'buy_id': buy_id,
        'buy_name': buy[2],
        'buy_description': buy[5],
        'buy_photo': buy[10],
        'buy_price': buy[4],
        'buy_count': buy[3],
        'buy_datetime': buy_time,
        'buy_house': buy[6],
        'buy_flat': buy[7],
        'buy_address': f"дом {buy[6]}, кв. {buy[7]}",
        'buy_status': buy[8]
    }

    if buy[8] == 'Ожидание сделки':
        buy_info['buy_status'] = '\u26a0\ufe0f <u>Ожидание сделки</u>'
    elif buy[8] == 'Ожидание продавца':
        buy_info['buy_status'] = '\u2753 <u>Ожидание продавца</u>'
    elif buy[8] == 'Ожидание покупателя':
        buy_info['buy_status'] = '\u2753 <u>Ожидание покупателя</u>'
    elif buy[8] == 'Отменено':
        buy_info['buy_status'] = '\u274c <u>Отменено</u>'
    elif buy[8] == 'Выполнено':
        buy_info['buy_status'] = '\u2705 <u>Выполнено</u>'

    await bot.delete_message(message.chat.id, message.message_id)
    desc = ""
    if buy_info['buy_description'] != '-':
        desc = f"  <b>Описание:</b> {buy_info['buy_description']}\n\n"

    if tip == 'buy':
        kok = "покупке"
    elif tip == 'sell':
        kok = "продаже"
    result = f"<b>Информация о {kok}:</b>\n"\
               f"  <b>ID:</b> {buy_info['buy_id']}\n"\
               f"  <b>Статус:</b> {buy_info['buy_status']}\n" \
               f"  <b>Категория:</b> {buy_info['buy_category']}\n"\
               f"  <b>Наименование:</b> {buy_info['buy_name']}\n"\
               f"{desc}"\
               f"  <b>Цена за шт:</b> {buy_info['buy_price']} руб.\n"\
               f"  <b>Кол-во:</b> {buy_info['buy_count']} шт.\n"\
               f"  <b>Общая сумма:</b> {buy_info['buy_count'] * buy_info['buy_price']} руб.\n\n"\
               f"  <b>Дата:</b> {buy_info['buy_datetime']}\n"\
               f"  <b>Адрес продавца:</b> {buy_info['buy_address']}\n"

    if tip == 'buy':
        if buy_info['buy_photo'] is not None:
            await bot.send_photo(message.chat.id,
                               photo=buy_info['buy_photo'],
                               caption=result,
                               parse_mode=types.ParseMode.HTML,
                               reply_markup=keyboard_contact(buy_info['seller_id'],
                                                             'buyer', buy_info['buy_id'], message))
        else:
            await bot.send_message(message.chat.id,
                                 text=result,
                                 parse_mode=types.ParseMode.HTML,
                                 reply_markup=keyboard_contact(buy_info['seller_id'],
                                                               'buyer', buy_info['buy_id'], message))
    elif tip == 'sell':
        if buy_info['buy_photo'] is not None:
            await bot.send_photo(message.chat.id,
                           photo=buy_info['buy_photo'],
                           caption=result,
                           parse_mode=types.ParseMode.HTML,
                           reply_markup=keyboard_contact(buy_info['buyer_id'],
                                                         'seller', buy_info['buy_id'], message))
        else:
            await bot.send_message(message.chat.id,
                                 text=result,
                                 parse_mode=types.ParseMode.HTML,
                                 reply_markup=keyboard_contact(buy_info['buyer_id'],
                                                               'seller', buy_info['buy_id'], message))


def update_of_trade(message, cur_time):
    cursor = con.cursor()

    cursor.execute(f"SELECT buy_id FROM buys")

    last_id = cursor.fetchall()
    if len(last_id) > 0:
        last_id = last_id[-1][0]
    else:
        last_id = 0

    cursor.execute(f"INSERT INTO buys VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (message.from_user.id,
                    cur_settings[message.from_user.id]['product'][0],
                    cur_settings[message.from_user.id]['product'][3],
                    cur_settings[message.from_user.id]['kol'],
                    cur_settings[message.from_user.id]['product'][5],
                    cur_settings[message.from_user.id]['product'][4],
                    cur_settings[message.from_user.id]['product'][6],
                    cur_settings[message.from_user.id]['product'][7],
                    'Ожидание сделки',
                    cur_time,
                    cur_settings[message.from_user.id]['product'][8],
                    last_id + 1,
                    cur_settings[message.from_user.id]['product'][9],
                    'neutral',
                    'neutral',
                    cur_settings[message.from_user.id]['category']))

    con.commit()

    return last_id


def if_username_not_updated(message):
    cursor = con.cursor()
    cursor.execute(f"SELECT username FROM base WHERE userid == ?",
                   (message.from_user.id,))
    username = cursor.fetchone()[0]
    if username is None:
        return False
    else:
        return True


def update_username(message):
    cursor = con.cursor()
    cursor.execute(f"UPDATE base SET username = ? WHERE userid == ?",
                   (message.from_user.username, message.from_user.id))


@dp.message_handler(commands=['help', 'start'], state='*')
async def help(message: types.Message, state: FSMContext):
    if message.from_user.id == message.chat.id:
        if_not_reg(message)
        await bot.send_message(message.from_user.id, 'Привет, <b>уважаемый студент</b> или нет. Ты попал в место, '
                                                     'где можно купить или продать что захочешь прямо в ДУ. '
                                                     'Чтобы начать пользование, '
                                                     'воспользуйся <b>меню ниже</b>.',
                               parse_mode=types.ParseMode.HTML, reply_markup=keyboard_main)
        await state.finish()
    else:
        await bot.send_message(message.from_user.id,  'Пожалуйста, используйте бота только в его ЛС.')


@dp.message_handler(state=Choise.wait_accept)
async def wait_accept(message: types.Message, state: FSMContext):
    if message.from_user.id == message.chat.id:
        if message.text == 'Меню':
            cur_settings[message.from_user.id] = {}
            await bot.send_message(message.from_user.id, 'Меню:', reply_markup=keyboard_main)
            await state.finish()
        elif message.text == 'Подтверждаю':
            change_count(message)

            cur_time = int(datetime.datetime.now().timestamp())

            last_id_buy = update_of_trade(message, cur_time)

            buy_id = last_id_buy + 1

            await get_buy_info('buy', buy_id, message)

            times[message.from_user.id]['buy'] = int(datetime.datetime.now().timestamp())

            cur_settings[message.from_user.id] = {}

            await state.finish()
            
    else:
        await bot.send_message(message.from_user.id, 'Пожалуйста, используйте бота в его ЛС.')


@dp.message_handler(state=Choise.buy_stay)
async def choice_product(message: types.Message, state: FSMContext):
    if message.from_user.id == message.chat.id:
        if message.text == 'Меню':
            cur_settings[message.from_user.id] = {}
            await bot.send_message(message.from_user.id, 'Меню:', reply_markup=keyboard_main)
            await state.finish()
        elif message.text == 'Назад':
            category = cur_settings[message.from_user.id]['category']
            products = get_product_list_by_category(category)
            await bot.send_message(message.from_user.id, 'Выберите товар:',
                                   reply_markup=keyboard_buy(products), parse_mode=types.ParseMode.HTML)
            cur_settings[message.from_user.id] = {
                'category': category,
                'product': ''
            }
            await Choise.product.set()
        else:
            kol = re.search(r'(\d) шт', message.text)
            if kol:
                kol = int(kol.group(1))
                all_kol = get_tovar_count(message)
                if kol <= all_kol:
                    await bot.send_message(message.from_user.id,
                                           f'<b>Покупка товара:</b> {cur_settings[message.from_user.id]["product"][3]}\n'
                                           f'<b>Количество товара:</b> {kol} шт.\n'
                                           f'<b>К оплате:</b> '
                                           f'{separator(kol*int(cur_settings[message.from_user.id]["product"][5]))} руб.\n'
                                           f'Подтвердите покупку товара <b>нажав кнопку ниже</b>',
                                           parse_mode=types.ParseMode.HTML,
                                           reply_markup=keyboard_accept)
                    cur_settings[message.from_user.id]['kol'] = kol
                    await Choise.wait_accept.set()
                else:
                    await bot.send_message(message.from_user.id,
                                           '<b>Пожалуйста, выберите корректное количество товара.</b>',
                                           parse_mode=types.ParseMode.HTML)
            else:
                await bot.send_message(message.from_user.id,
                                       'Пожалуйста, выберите количество товара, которое хотите приобрести.')
    else:
        await bot.send_message(message.from_user.id, 'Пожалуйста, используйте бота в его ЛС.')



@dp.message_handler(state=Choise.product)
async def choice_product(message: types.Message, state: FSMContext):
    if message.from_user.id == message.chat.id:
        if message.text == 'Меню':
            cur_settings[message.from_user.id] = {}
            await bot.send_message(message.from_user.id, 'Меню:', reply_markup=keyboard_main)
            await state.finish()
        elif message.text == 'Назад':
            products = get_tovar_list()
            buy_categories = get_all_categories()
            if products != '':
                await bot.send_message(message.from_user.id, products,
                                       parse_mode=types.ParseMode.HTML, reply_markup=keyboard_buy(buy_categories))
                await Choise.category.set()
            else:
                await bot.send_message(message.from_user.id, 'Увы, товаров нет в наличии!',
                                       reply_markup=keyboard_main, parse_mode=types.ParseMode.HTML)
        else:
            cur_prod = find_product_in_category(message)
            if cur_prod is not None:
                if cur_prod[8] is not None:
                    await bot.send_photo(message.from_user.id,
                                           caption=f'<b>Товар:</b> {cur_prod[3]}\n'
                                           f'<b>Описание:</b> {cur_prod[4]}\n'
                                           f'<b>Осталось:</b> {cur_prod[2]} шт.\n'
                                           f'<b>Цена:</b> {separator(cur_prod[5])} руб.\n'
                                           f'<b>Дом:</b> {cur_prod[6]}',
                                           photo=cur_prod[8],
                                           parse_mode=types.ParseMode.HTML,
                                           reply_markup=keyboard_sht)
                else:
                    await bot.send_message(message.from_user.id,
                                         text=f'<b>Товар:</b> {cur_prod[3]}\n'
                                              f'<b>Описание:</b> {cur_prod[4]}\n'
                                              f'<b>Осталось:</b> {cur_prod[2]} шт.\n'
                                              f'<b>Цена:</b> {separator(cur_prod[5])} руб.\n'
                                              f'<b>Дом:</b> {cur_prod[6]}',
                                         parse_mode=types.ParseMode.HTML,
                                         reply_markup=keyboard_sht)
                cur_settings[message.from_user.id]['product'] = cur_prod
                await Choise.buy_stay.set()
            else:
                await bot.send_message(message.from_user.id, '<b>Пожалуйста, выберите товар из списка.</b>',
                                       parse_mode=types.ParseMode.HTML)
    else:
        await bot.send_message(message.from_user.id, 'Пожалуйста, используйте бота в его ЛС.')


@dp.message_handler(state=Choise.category)
async def choice_category(message: types.Message, state: FSMContext):
    if message.from_user.id == message.chat.id:
        buy_categories = get_all_categories()
        if message.text == 'Меню' or message.text == 'Назад':
            cur_settings[message.from_user.id] = {}
            await bot.send_message(message.from_user.id, 'Меню:',
                                   reply_markup=keyboard_main)
            await state.finish()
        elif message.text in buy_categories:
            category = message.text
            products = get_product_list_by_category(category)
            await bot.send_message(message.from_user.id, 'Выберите товар:',
                                   reply_markup=keyboard_buy(products), parse_mode=types.ParseMode.HTML)
            cur_settings[message.from_user.id] = {
                'category': category,
                'product': '',
                'kol': 0
            }
            await Choise.product.set()
        else:
            await bot.send_message(message.from_user.id, 'Пожалуйста, выберите категорию из списка.',
                                   reply_markup=keyboard_buy(buy_categories))
    else:
        await bot.send_message(message.from_user.id, 'Пожалуйста, используйте бота в его ЛС.')


@dp.message_handler(state=Choise.profile)
async def start(message: types.Message, state: FSMContext):
    if message.from_user.id == message.chat.id:
        if message.text == 'Меню':
            if_not_reg(message)
            await bot.send_message(message.from_user.id, 'Меню:',
                                   reply_markup=keyboard_main)
            await state.finish()
        elif message.text == 'Покупки':
            buys = get_buys(message)
            if len(buys) > 0:
                if len(buys) > 10:
                    buys = buys[0:10]
                await bot.send_message(message.from_user.id,
                                       "Ваши последние покупки:",
                                       reply_markup=keyboard_last_buys_or_sells(buys, 'buy'))
            else:
                await bot.send_message(message.from_user.id,
                                       "У вас еще нет покупок.",
                                       reply_markup=keyboard_profile)
        elif message.text == 'Продажи':
            sells = get_sells(message)
            if len(sells) > 0:
                if len(sells) > 10:
                    sells = sells[0:10]
                await bot.send_message(message.from_user.id,
                                       "Ваши последние продажи:",
                                       reply_markup=keyboard_last_buys_or_sells(sells, 'sell'))
            else:
                await bot.send_message(message.from_user.id,
                                       "Вы еще ничего не продавали.",
                                       reply_markup=keyboard_profile)
        elif message.text == 'Мой телефон':
            pass
    else:
        await bot.send_message(message.from_user.id, 'Пожалуйста, используйте бота в его ЛС.')


@dp.message_handler(state=Choise.admin_accept)
async def start(message: types.Message, state: FSMContext):
    if message.chat.id == ADMIN_CHAT_ID and message.from_user.id in ADMIN_LIST:
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            if message.text in ['Да', 'да', 'д', 'Д', 'y', 'yes', 'Подтвердить', 'подтверждаю', 'accept', 'acc']:
                if add_tovar(admin_settings[message.from_user.id], message.from_user.id):
                    await bot.send_message(message.chat.id, 'Товар успешно добавлен!',
                                           reply_markup=types.ReplyKeyboardRemove())
                else:
                    await bot.send_message(message.chat.id, 'Ошибка добавления товара',
                                           reply_markup=types.ReplyKeyboardRemove())
                admin_settings[message.from_user.id] = {}
                await state.finish()
            elif message.text in ['Нет', 'нет', 'no', 'Н', 'н', 'n', 'отмена', 'отм', 'Отмена']:
                await bot.send_message(message.chat.id, 'Добавление товара отменено!',
                                       reply_markup=types.ReplyKeyboardRemove())
                admin_settings[message.from_user.id] = {}
                await state.finish()
    elif message.from_user.id == message.chat.id:
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            if message.text in ['Да', 'да', 'д', 'Д', 'y', 'yes', 'Подтвердить', 'подтверждаю', 'accept', 'acc']:
                if await request_tovar(admin_settings[message.from_user.id], message.from_user.id):
                    await bot.send_message(message.chat.id, 'Запрос на добавление успешно создан. Ожидайте одобрения!',
                                           reply_markup=keyboard_main)
                    times[message.from_user.id]['sell'] = int(datetime.datetime.now().timestamp())
                else:
                    await bot.send_message(message.chat.id, 'Ошибка добавления товара',
                                           reply_markup=keyboard_main)
                admin_settings[message.from_user.id] = {}
            elif message.text in ['Нет', 'нет', 'no', 'Н', 'н', 'n', 'отмена', 'отм', 'Отмена']:
                await bot.send_message(message.chat.id, 'Добавление товара отменено!',
                                       reply_markup=types.ReplyKeyboardRemove())
                admin_settings[message.from_user.id] = {}
            await state.finish()


@dp.message_handler(state=Choise.admin_flat)
async def start(message: types.Message, state: FSMContext):
    if (message.chat.id == ADMIN_CHAT_ID and message.from_user.id in ADMIN_LIST) or message.from_user.id == message.chat.id:
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            admin_settings[message.from_user.id]['product']['flat'] = message.text

            itog = admin_settings[message.from_user.id]['product']['price'] * \
                   admin_settings[message.from_user.id]['product']['count']

            tovar = f"Категория: {admin_settings[message.from_user.id]['category']}\n" \
                    f"Название: {admin_settings[message.from_user.id]['product']['name']}\n" \
                    f"Цена: {admin_settings[message.from_user.id]['product']['price']}\n" \
                    f"Количество: {admin_settings[message.from_user.id]['product']['count']}\n" \
                    f"Итог: {itog}\n\n" \
                    f"Описание: {admin_settings[message.from_user.id]['product']['description']}\n\n" \
                    f"Дом: {admin_settings[message.from_user.id]['product']['house']}\n" \
                    f"Комната: {admin_settings[message.from_user.id]['product']['flat']}"

            if admin_settings[message.from_user.id]['product']['photo'] is not None:
                await bot.send_photo(message.chat.id,
                                     caption=tovar,
                                     photo=admin_settings[message.from_user.id]['product']['photo'])
            else:
                await bot.send_message(message.chat.id, text=tovar)
            await bot.send_message(message.chat.id, 'Подтвердите товар:', reply_markup=keyboard_admin_accept)

            await Choise.admin_accept.set()


@dp.message_handler(state=Choise.admin_house)
async def start(message: types.Message, state: FSMContext):
    if (message.chat.id == ADMIN_CHAT_ID and message.from_user.id in ADMIN_LIST) or message.from_user.id == message.chat.id:
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            try:
                house = float(message.text)
                if house in houses:
                    await bot.send_message(message.chat.id, 'Введите номер комнаты:')
                    admin_settings[message.from_user.id]['product']['house'] = house
                    await Choise.admin_flat.set()
                else:
                    await bot.send_message(message.chat.id, 'Введите корректный номер дома:')
            except:
                await bot.send_message(message.chat.id, 'Введите корректный номер дома:')


@dp.message_handler(state=Choise.admin_product_house_is_default)
async def start(message: types.Message, state: FSMContext):
    if (message.chat.id == ADMIN_CHAT_ID and message.from_user.id in ADMIN_LIST) or message.from_user.id == message.chat.id:
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            if message.text in ['Да', 'да', 'д', 'Д', 'y', 'yes']:
                admin_settings[message.from_user.id]['product']['house'] = DEFAULT_ADDRESS['house']
                admin_settings[message.from_user.id]['product']['flat'] = DEFAULT_ADDRESS['flat']

                itog = admin_settings[message.from_user.id]['product']['price'] *\
                       admin_settings[message.from_user.id]['product']['count']

                tovar = f"Категория: {admin_settings[message.from_user.id]['category']}\n" \
                        f"Название: {admin_settings[message.from_user.id]['product']['name']}\n" \
                        f"Цена: {admin_settings[message.from_user.id]['product']['price']}\n" \
                        f"Количество: {admin_settings[message.from_user.id]['product']['count']}\n" \
                        f"Итог: {itog}\n\n" \
                        f"Описание: {admin_settings[message.from_user.id]['product']['description']}\n\n" \
                        f"Дом: {admin_settings[message.from_user.id]['product']['house']}\n" \
                        f"Комната: {admin_settings[message.from_user.id]['product']['flat']}"

                if admin_settings[message.from_user.id]['product']['photo'] is not None:
                    await bot.send_photo(message.chat.id,
                                         caption=tovar,
                                         photo=admin_settings[message.from_user.id]['product']['photo'])
                else:
                    await bot.send_message(message.chat.id, text=tovar)
                await bot.send_message(message.chat.id, 'Подтвердите товар:', reply_markup=keyboard_admin_accept)
                await Choise.admin_accept.set()
            elif message.text in ['Нет', 'нет', 'no', 'Н', 'н', 'n']:
                await bot.send_message(message.chat.id, 'Введите номер дома:')
                await Choise.admin_house.set()


@dp.message_handler(state=Choise.admin_product_count)
async def start(message: types.Message, state: FSMContext):
    if (message.chat.id == ADMIN_CHAT_ID and message.from_user.id in ADMIN_LIST):
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            try:
                count = int(message.text)
                admin_settings[message.from_user.id]['product']['count'] = count
                await bot.send_message(message.chat.id, 'Оставить адрес дефолтным?')
                await Choise.admin_product_house_is_default.set()
            except:
                await bot.send_message(message.chat.id, 'Введите корректное количество:')
    elif message.from_user.id == message.chat.id:
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            try:
                count = int(message.text)
                admin_settings[message.from_user.id]['product']['count'] = count
                await bot.send_message(message.chat.id, 'Введите номер дома:')
                await Choise.admin_house.set()
            except:
                await bot.send_message(message.chat.id, 'Введите корректное количество:')


@dp.message_handler(state=Choise.admin_product_price)
async def start(message: types.Message, state: FSMContext):
    if (message.chat.id == ADMIN_CHAT_ID and message.from_user.id in ADMIN_LIST) or message.from_user.id == message.chat.id:
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            try:
                price = int(message.text)
                admin_settings[message.from_user.id]['product']['price'] = price
                await bot.send_message(message.chat.id, 'Введите количество товара:')
                await Choise.admin_product_count.set()
            except:
                await bot.send_message(message.chat.id, 'Введите корректную цену:')


@dp.message_handler(state=Choise.admin_photo, content_types=['photo', 'text'])
async def start(message: types.Message, state: FSMContext):
    if (message.chat.id == ADMIN_CHAT_ID and message.from_user.id in ADMIN_LIST) or message.from_user.id == message.chat.id:
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            if message.content_type == 'text':
                await bot.send_message(message.chat.id, 'Пришлите фото товара:', reply_markup=keyboard_menu)
            elif message.content_type == 'photo':
                admin_settings[message.from_user.id]['product']['photo'] = message.photo[0].file_id
                await bot.send_message(message.chat.id, 'Введите цену за шт. товара:', reply_markup=keyboard_menu)
                await Choise.admin_product_price.set()


@dp.message_handler(state=Choise.admin_product_description)
async def start(message: types.Message, state: FSMContext):
    if (message.chat.id == ADMIN_CHAT_ID and message.from_user.id in ADMIN_LIST) or message.from_user.id == message.chat.id:
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            await bot.send_message(message.chat.id, 'Отправьте фото товара:')
            admin_settings[message.from_user.id]['product']['description'] = message.text
            await Choise.admin_photo.set()


@dp.message_handler(state=Choise.admin_product_name)
async def start(message: types.Message, state: FSMContext):
    if (message.chat.id == ADMIN_CHAT_ID and message.from_user.id in ADMIN_LIST) or message.from_user.id == message.chat.id:
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            admin_settings[message.from_user.id] = {}
            await state.finish()
        else:
            await bot.send_message(message.chat.id, 'Введите описание товара '
                                                    '(если описания нет, введите <b>-</b>):',
                                                    reply_markup=keyboard_menu,
                                                    parse_mode=types.ParseMode.HTML)
            admin_settings[message.from_user.id]['product'] = {}
            admin_settings[message.from_user.id]['product']['name'] = message.text
            await Choise.admin_product_description.set()


@dp.message_handler(state=Choise.admin_category)
async def start(message: types.Message, state: FSMContext):
    if (message.chat.id == ADMIN_CHAT_ID and message.from_user.id in ADMIN_LIST) or message.from_user.id == message.chat.id:
        admin_settings[message.from_user.id] = {}
        if message.text == 'Меню' or message.text == 'Назад' or message.text == 'm':
            await bot.send_message(message.chat.id, 'Меню:', reply_markup=keyboard_main)
            await state.finish()
        elif message.text in categories:
            category = message.text
            await bot.send_message(message.chat.id, 'Введите название товара:', reply_markup=keyboard_menu)
            admin_settings[message.from_user.id]['category'] = category
            await Choise.admin_product_name.set()
        else:
            await bot.send_message(message.chat.id, 'Пожалуйста, выберите категорию из списка.',
                                   reply_markup=keyboard_buy(categories))


@dp.message_handler(state='*')
async def start(message: types.Message, state: FSMContext):
    global msg
    global is_continue
    if message.chat.id == ADMIN_CHAT_ID:
        if message.from_user.id in ADMIN_LIST:
            if message.text == '/add':
                await bot.send_message(message.chat.id,
                                       'Выберите категорию товара:',
                                       reply_markup=keyboard_categories(categories))
                await Choise.admin_category.set()
    elif message.chat.id == MODER_CHAT_ID:
        if ('отказ' in message.text.lower()) or ('нет' in message.text.lower()):
            await decline_request(message.text, message)
        elif message.text == '/req':
            await next_req_to_moder(message)
    elif message.from_user.id == message.chat.id:
        if message.text == 'Меню':
            if_not_reg(message)
            await bot.send_message(message.from_user.id, 'Меню:',
                                   reply_markup=keyboard_main)
            await state.finish()
        elif '/spam' in message.text:
            if message.from_user.id in ADMIN_LIST:
                msg = message.text.split()
                if len(msg) == 1:
                    await bot.send_message(message.from_user.id, 'Введите /spam текст')
                elif len(msg) > 1:
                    msg = ' '.join(msg[1::])
                    print(msg)
                    await bot.send_message(message.from_user.id,
                                           'Будет разослано сообщение:\n' + msg + '\nВведите "Да" чтобы подтвердить, '
                                                                                  '"Нет" чтобы отменить.')
                    is_continue = True
        elif message.text == 'Да':
            if message.from_user.id in ADMIN_LIST:
                if is_continue == True:
                    con = sql.connect('base.db')
                    cursor = con.cursor()
                    cursor.execute(f"SELECT userid FROM base")
                    alls = cursor.fetchall()
                    for all in alls:
                        await bot.send_message(all[0], msg, reply_markup=keyboard_main)
                    is_continue = False
                    msg = ''
                    await bot.send_message(message.from_user.id, 'Разослано.')
        elif message.text == 'Нет':
            if message.from_user.id in ADMIN_LIST:
                if is_continue == True:
                    msg = ''
                    is_continue = False
                    await bot.send_message(message.from_user.id, 'Отменено.')
        elif message.text == 'Купить':
            if message.from_user.username is not None:
                if_not_reg(message)
                try:
                    razn = int(datetime.datetime.now().timestamp()) - times[message.from_user.id]['buy']
                    if razn > 60:
                        products = get_tovar_list()
                        buy_categories = get_all_categories()
                        if products != '':
                            await bot.send_message(message.from_user.id, products,
                                                   parse_mode=types.ParseMode.HTML,
                                                   reply_markup=keyboard_buy(buy_categories))
                            await Choise.category.set()
                        else:
                            await bot.send_message(message.from_user.id, 'Увы, товаров нет в наличии!',
                                                   reply_markup=keyboard_main, parse_mode=types.ParseMode.HTML)
                    else:
                        await bot.send_message(message.from_user.id, f"Попробуйте через {60 - razn} сек...")
                except Exception as ex:
                    if str(ex) == str(message.from_user.id) or str(ex) == "'buy'":
                        products = get_tovar_list()
                        buy_categories = get_all_categories()
                        if products != '':
                            await bot.send_message(message.from_user.id, products,
                                                   parse_mode=types.ParseMode.HTML,
                                                   reply_markup=keyboard_buy(buy_categories))
                            await Choise.category.set()
                        else:
                            await bot.send_message(message.from_user.id, 'Увы, товаров нет в наличии!',
                                                   reply_markup=keyboard_main, parse_mode=types.ParseMode.HTML)
                        times[message.from_user.id] = {}
                        times[message.from_user.id]['buy'] = 0
            else:
                await bot.send_message(message.from_user.id, 'Пожалуйста, для дальнейшей работы установите свой '
                                                             '<b>Никнейм</b> в настройках профиля Telegram.',
                                       parse_mode=types.ParseMode.HTML,
                                       reply_markup=keyboard_main)
        elif message.text == 'Продать':
            if message.from_user.username is not None:
                try:
                    razn = int(datetime.datetime.now().timestamp()) - times[message.from_user.id]['sell']
                    if razn > 60:
                        await bot.send_message(message.chat.id,
                                               'Выберите категорию товара:',
                                               reply_markup=keyboard_categories(categories))
                        await Choise.admin_category.set()
                    else:
                        await bot.send_message(message.from_user.id, f"Попробуйте через {60 - razn} сек...")
                except Exception as ex:
                    if str(ex) == str(message.from_user.id) or str(ex) == "'sell'":
                        await bot.send_message(message.chat.id,
                                               'Выберите категорию товара:',
                                               reply_markup=keyboard_categories(categories))
                        times[message.from_user.id] = {}
                        times[message.from_user.id]['sell'] = 0
                        await Choise.admin_category.set()
            else:
                await bot.send_message(message.from_user.id, 'Пожалуйста, для дальнейшей работы установите свой '
                                                             '<b>Никнейм</b> в настройках профиля Telegram.',
                                       parse_mode=types.ParseMode.HTML,
                                       reply_markup=keyboard_main)
        elif message.text == 'Профиль':
            if message.from_user.username is not None:
                if not if_username_not_updated(message):
                    update_username(message)
                if_not_reg(message)
                buy_sum = get_buy_sum(message) 
                sell_sum = get_sell_sum(message)
                await bot.send_message(message.from_user.id,
                                       '➖➖➖➖➖➖➖➖➖➖➖\n'
                                       f'  <b>Информация о вас:</b>\n\n'
                                       f'  <b>Логин:</b> @{message.from_user.username}\n'
                                       f'  <b>ID:</b> {message.from_user.id}\n\n'
                                       f'  <b>Покупок на сумму:</b> {buy_sum}\n'
                                       f'  <b>Продаж на сумму:</b> {sell_sum}\n'
                                       '➖➖➖➖➖➖➖➖➖➖➖',
                                       reply_markup=keyboard_profile,
                                       parse_mode=types.ParseMode.HTML)
                await Choise.profile.set()
            else:
                await bot.send_message(message.from_user.id, 'Пожалуйста, для дальнейшей работы установите свой '
                                                             '<b>Никнейм</b> в настройках профиля Telegram.',
                                       parse_mode=types.ParseMode.HTML,
                                       reply_markup=keyboard_main)
        elif message.text == 'Инфо':
            if_not_reg(message)
            await bot.send_message(message.from_user.id, 'Привет. Этот бот создан для покупки/продажи различных товаров'
                                                         ' на территории Деревни Универсиады.\n\n'
                                                         'Всю подробную информацию о товаре вы можете '
                                                         'посмотреть во вкладке <b>"Купить"</b> или связаться с '
                                                         'продавцом.\n\n'
                                                         'Можете заглянуть в нашего '
                                                         '<a href="t.me/kpfuhelperbot">КФУ Помощника</a> :)\n'
                                                         'Там всегда актуальное расписание (пока только ИВМиИТ) ',
                                   reply_markup=keyboard_main, parse_mode=types.ParseMode.HTML)
        elif message.text == 'Поддержка':
            if_not_reg(message)
            await bot.send_message(message.from_user.id, '<a href="t.me/mosemax">жалобы и пожелания сюда</a>',
                                   reply_markup=keyboard_main,
                                   parse_mode=types.ParseMode.HTML,
                                   disable_web_page_preview=True)
    else:
        await bot.send_message(message.from_user.id, 'Пожалуйста, используйте бота в его ЛС.')


@dp.callback_query_handler(state='*')
async def callback_worker(call: types.CallbackQuery, state: FSMContext):
    data = call.data
    if data == 'menu':
        if_not_reg(call.message)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await bot.send_message(call.message.chat.id, 'Меню:',
                               reply_markup=keyboard_main)
        await state.finish()
    elif 'buy_' in data:
        buy_id = int(data.split('buy_')[1])

        await get_buy_info('buy', buy_id, call.message)
    elif 'sell_' in data:
        sell_id = int(data.split('sell_')[1])

        await get_buy_info('sell', sell_id, call.message)
    elif 'tg_' in data:
        tgid = int(data.split('tg_')[1])
    elif 'buyer_' in data:
        l = data.split('_')
        res = edit_statuses(l[0], l[1], l[2])
        if res == 'access_all':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await access_all(l[2])
        elif res == 'access_buyer':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await access_buyer(l[2])
        elif res == 'access_seller':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await access_seller(l[2])
        elif res == 'decline_buyer':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await decline_buyer(l[2])
        elif res == 'decline_seller':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await decline_seller(l[2])
    elif 'seller_' in data:
        l = data.split('_')
        res = edit_statuses(l[0], l[1], l[2])
        if res == 'access_all':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await access_all(l[2])
            await state.finish()
        elif res == 'access_buyer':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await access_buyer(l[2])
        elif res == 'access_seller':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await access_seller(l[2])
        elif res == 'decline_buyer':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await decline_buyer(l[2])
            await state.finish()
        elif res == 'decline_seller':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await decline_seller(l[2])
            await state.finish()
    elif 'request_' in data:
        req, tip, req_id = data.split('_')
        if tip == 'accept':
            if add_tovar_buy_request(req_id):
                await bot.delete_message(call.message.chat.id, call.message.message_id)
                await bot.send_message(call.message.chat.id, 'Товар успешно добавлен!',
                                       reply_markup=types.ReplyKeyboardRemove())
            else:
                await bot.send_message(call.message.chat.id, 'Ошибка добавления товара',
                                       reply_markup=types.ReplyKeyboardRemove())
        elif tip == 'edit':
            pass
        elif tip == 'decline':
            await bot.send_message(call.message.chat.id,
                                   'Чтобы отменить введите ответ, '
                                   'добавив в начале отказ и ID запроса "Отказ 35".',
                                   reply_markup=types.ReplyKeyboardRemove())


if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # loop.create_task(download())
    executor.start_polling(dp, skip_updates=True)
