import logging

from telebot import types

import db_wrap
from utils import *
# from operator import itemgetter

logger = logging.getLogger('AnimalRaces')

markups = list()

# step 0
markups.append(types.ReplyKeyboardMarkup(resize_keyboard=True))
markups[0].row(types.KeyboardButton('📊Статистика'), types.KeyboardButton('📜Статус'), types.KeyboardButton('💰Ставка'))
markups[0].row(types.KeyboardButton('🔖Пригласить'), types.KeyboardButton('ℹ️Правила'))

# step 1 - Статистика
markups.append(types.ReplyKeyboardMarkup(resize_keyboard=True))
markups[1].row(types.KeyboardButton('👤Личная'), types.KeyboardButton('👥Игроки'), types.KeyboardButton('🐎Животные'))
markups[1].row( types.KeyboardButton('⬅️Назад'), types.KeyboardButton('⬆️Наверх'))

# step 2 - Ставка
markups.append(types.ReplyKeyboardMarkup(resize_keyboard=True))
markups[2].row(types.KeyboardButton('➕'), types.KeyboardButton('➕➕'), types.KeyboardButton('Макс.'))
markups[2].row(types.KeyboardButton('➖'), types.KeyboardButton('➖➖'), types.KeyboardButton('Мин.'))
markups[2].row(types.KeyboardButton('⬅️Назад'), types.KeyboardButton('⬆️Наверх'))

# step 3 - Статистика - Личная
markups.append(types.ReplyKeyboardMarkup(resize_keyboard=True))
markups[3].row(types.KeyboardButton(''), types.KeyboardButton(''), types.KeyboardButton(''))
markups[3].row(types.KeyboardButton('⬅️Назад'), types.KeyboardButton('⬆️Наверх'))

# step 4 - Статистика - Игроки
markups.append(types.ReplyKeyboardMarkup(resize_keyboard=True))
markups[4].row(types.KeyboardButton('💰Золото'), types.KeyboardButton('⚜️Уровень'))
markups[4].row(types.KeyboardButton('💰Ставки'), types.KeyboardButton('🥇🥈🥉Медали'), types.KeyboardButton('🏆Победы'))
markups[4].row(types.KeyboardButton('⬅️Назад'), types.KeyboardButton('⬆️Наверх'))

# step 5 - Статистика - Животные
markups.append(types.ReplyKeyboardMarkup(resize_keyboard=True))
markups[5].row(types.KeyboardButton(''), types.KeyboardButton(''), types.KeyboardButton(''))
markups[5].row(types.KeyboardButton('⬅️Назад'), types.KeyboardButton('⬆️Наверх'))


def check_btn(race_user, text):
    if 'Наверх' in text:
        race_user = menu_0(race_user)

    # step 0
    elif race_user.menu == 0:
        if 'Статистика' in text:
            race_user = menu_0_1(race_user)
        elif 'Статус' in text:
            race_user.put_msg(race_user.status_msg)
        elif 'Ставка' in text:
            race_user.put_msg('Размер ставки установлен {}💰'.format(race_user.bet), menu=2)
    # step 1 - Статистика (0 - 1)
    elif race_user.menu == 1:
        if 'Личная' in text:
            race_user.put_msg('🚧В разработке🚧'.format(race_user.bet))
        elif 'Игроки' in text:
            race_user.put_msg('👥Рейтинги игроков'.format(race_user.bet), menu=4)
        elif 'Животные' in text:
            race_user.put_msg('🚧В разработке🚧'.format(race_user.bet))
        elif 'Назад' in text:
            race_user = menu_0(race_user)
    # step 2 - Ставка (0 - 2)
    elif race_user.menu == 2:
        if '➕' == text:
            race_user.set_bet(race_user.bet + int(round_int(int(race_user.money * 0.1))/5))
        elif '➕➕' == text:
            race_user.set_bet(race_user.bet + round_int(int(race_user.money * 0.1)))
        elif '➖' == text:
            race_user.set_bet(race_user.bet - int(round_int(int(race_user.money * 0.1))/5))
        elif '➖➖' == text:
            race_user.set_bet(race_user.bet - round_int(int(race_user.money * 0.1)))
        elif 'Мин' in text:
            race_user.set_bet(10)
        elif 'Макс' in text:
            race_user.set_bet(race_user.max_bet)
        elif 'Назад' in text:
            race_user = menu_0(race_user)
        else:
            try:
                bet = int(text)
                race_user.set_bet(bet)
            except:
                logger.warning('Пользователь {} в качестве ставки ввел: {}'.format(race_user.user_id, text))
    # step 4 - Статистика - Игроки (0 - 1 - 4)
    elif race_user.menu == 4:
        if 'Золото' in text:
            stat = db_wrap.get_players_stat()
            sorted_stat = sorted(stat, key=lambda x: x['money'], reverse=True)[:10]
            result = ['💰Золото\n\n']
            for row in sorted_stat:
                result.append('`{:<14.14}  {:>5}💰`\n'.format(strip_emoji(row['first_name']),
                                                              str_human_int(row['money'])))
            race_user.put_msg(''.join(result))
        elif 'Уровень' in text:
            race_user.put_msg('🚧В разработке🚧'.format(race_user.bet))
        elif 'Победы' in text:
            stat = db_wrap.get_players_stat()
            sorted_stat = sorted(stat, key=lambda x: x['wins'], reverse=True)[:10]
            result = ['🏆Победы\n\n']
            for row in sorted_stat:
                result.append('`{:<14.14}  {:>4}/{}`\n'.format(strip_emoji(row['first_name']),
                                                               row['wins'], row['bets_cnt']))
            race_user.put_msg(''.join(result))
        elif 'Медали' in text:
            stat = db_wrap.get_players_stat()
            sorted_stat = sorted(stat, key=lambda x: x['prizes'], reverse=True)[:10]
            result = ['🥇🥈🥉Медали\n\n']
            for row in sorted_stat:
                result.append('`{:<14.14}  {:>4}/{}`\n'.format(strip_emoji(row['first_name']),
                                                               row['prizes'], row['bets_cnt']))
            race_user.put_msg(''.join(result))
        elif 'Ставки' in text:
            stat = db_wrap.get_players_stat()
            race_user.put_msg('🚧В разработке🚧'.format(race_user.bet))
        elif 'Назад' in text:
            race_user = menu_0_1(race_user)

    return race_user


def menu_0(race_user):
    race_user.put_msg(race_user.status_msg, menu=0)
    return race_user


def menu_0_1(race_user):
    stat = db_wrap.get_main_stat()
    race_user.put_msg('📊Общая статистика\n\n'
                      '`Всего игроков {:>8}`\n'
                      '`Всего животных {:>7}`\n'
                      '`Всего забегов {:>8}`\n'
                      '`Принято ставок {:>7}`\n'
                      '`Сумма ставок {:>9}💰`'.format(stat['users'], stat['animals'],
                                                      str_human_int(stat['races']),
                                                      str_human_int(stat['bets']),
                                                      str_human_int(stat['moneys'])), menu=1)


def menu_0_2(race_user):
    return race_user


def menu_0_1_4(race_user):
    return race_user
