from telebot import types
import logging

logger = logging.getLogger('AnimalRaces')

markups = list()

# step 0
markups.append(types.ReplyKeyboardMarkup(resize_keyboard=True))
markups[0].row(
    types.KeyboardButton('📊Статистика'),
    types.KeyboardButton('📜Статус'),
    types.KeyboardButton('💰Ставка')
)

# step 1 - Статистика
markups.append(types.ReplyKeyboardMarkup(resize_keyboard=True))
markups[1].row(
    types.KeyboardButton('👤Личная'),
    types.KeyboardButton('👥Игроки'),
    types.KeyboardButton('🐎Животные')
)
markups[1].row(
    types.KeyboardButton('⬅️Назад'),
    types.KeyboardButton('⬆️Наверх'),
)

# step 2 - Ставка
markups.append(types.ReplyKeyboardMarkup(resize_keyboard=True))
markups[2].row(
    types.KeyboardButton('➕'),
    types.KeyboardButton('➕➕'),
    types.KeyboardButton('Макс.')
)
markups[2].row(
    types.KeyboardButton('➖'),
    types.KeyboardButton('➖➖'),
    types.KeyboardButton('Мин.')
)
markups[2].row(
    types.KeyboardButton('⬅️Назад'),
    types.KeyboardButton('⬆️Наверх'),
)


def check_btn(race_user, text):
    if 'Наверх' in text:
        race_user.put_msg(race_user.status_msg, menu=0)

    # step 0
    elif race_user.menu == 0:
        if 'Статистика' in text:
            race_user.put_msg('🚧В разработке🚧'.format(race_user.bet), menu=1)
        elif 'Статус' in text:
            race_user.put_msg(race_user.status_msg)
        elif 'Ставка' in text:
            race_user.put_msg('Размер ставки установлен {}💰'.format(race_user.bet), menu=2)
    # step 1 - Статистика
    elif race_user.menu == 1:
        if 'Личная' in text:
            race_user.put_msg('🚧В разработке🚧'.format(race_user.bet))
        elif 'Игроки' in text:
            race_user.put_msg('🚧В разработке🚧'.format(race_user.bet))
        elif 'Животные' in text:
            race_user.put_msg('🚧В разработке🚧'.format(race_user.bet))
        elif 'Назад' in text:
            race_user.put_msg(race_user.status_msg, menu=0)
    # step 2 - Ставка
    elif race_user.menu == 2:
        if '➕' == text:
            race_user.set_bet(race_user.bet + int(race_user.money * 0.02))
        elif '➕➕' == text:
            race_user.set_bet(race_user.bet + int(race_user.money * 0.1))
        elif '➖' == text:
            race_user.set_bet(race_user.bet - int(race_user.money * 0.02))
        elif '➖➖' == text:
            race_user.set_bet(race_user.bet - int(race_user.money * 0.1))
        elif 'Мин' in text:
            race_user.set_bet(10)
        elif 'Макс' in text:
            race_user.set_bet(race_user.max_bet)
        elif 'Назад' in text:
            race_user.put_msg(race_user.status_msg, menu=0)
        else:
            try:
                bet = int(text)
                race_user.set_bet(bet)
            except:
                logger.warning('Пользователь {} в качестве ставки ввел: {}'.format(race_user.user_id, text))
    return race_user
