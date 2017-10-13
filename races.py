#!/usr/local/bin/python

import time
import telebot
from telebot import types
import logging
import requests
import threading
from db_wrap import update_user
import racing
import user
from config import *


logger = logging.getLogger('AnimalRaces')


class BotHandler(logging.Handler):
    def __init__(self, bot):
        logging.Handler.__init__(self)
        self.bot_obj = bot

    def emit(self, record):
        msg = self.format(record)
        bot.send_message(LOGS_CHANNEL, msg)  # , parse_mode='Markdown')


bot = telebot.TeleBot(TOKEN, threaded=False)
# me = bot.get_me()
start_btn_clicked = False
race = racing.Racing()
users = {}


@bot.message_handler(func=lambda msg: msg.chat.id == CHANNEL_ID, content_types=['new_chat_members'])
def on_user_joins(msg):
    logger.debug('User joined channel (id:%d)', msg.new_chat_member.id)
    new_user = msg.new_chat_member
    if check_user(new_user):
        logger.info('New user in DB added(join)')


@bot.message_handler(commands=['bet'])
def on_bet_msg(msg):
    _, *args = msg.text.split()
    if check_user(msg.from_user):
        logger.info('New user in DB added(command)')
    try:
        users[msg.from_user.id].set_bet(int(args[0]))
    except ValueError:
        logger.warning('set_bet error from user: %s args[0]: %s', msg.from_user.first_name, str(args[0]))
    except IndexError:
        logger.warning('set_bet empty value from user: %s', msg.from_user.first_name)


@bot.message_handler(func=lambda msg: True)
def on_any_msg(msg):
    new_user = msg.from_user
    if check_user(new_user):
        logger.info('New user in DB added(msg)')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global start_btn_clicked
    if check_user(call.from_user):
        logger.info('New user in DB added(button)')
    if call.data == 'call_start' and not start_btn_clicked:
        start_btn_clicked = True
        race_msg_id = init_race(call)
        logger.debug('Race inited by {}'.format(call.from_user.first_name))
        threading.Thread(target=do_race, args=(race_msg_id,)).start()
    elif 'call_bet_' in call.data:
        users[call.from_user.id].track = int(call.data[9:])+1
        bot.answer_callback_query(call.id, '{}💰 на {} по {}️⃣ дорожке.'.format(
            users[call.from_user.id].bet,
            race.racers[users[call.from_user.id].track-1]['animal'],
            users[call.from_user.id].track
        ))
        logger.debug('{} bets on {}'.format(call.from_user.first_name, int(call.data[9:])+1))


def show_start_btn():
    global start_btn_clicked
    markup = types.InlineKeyboardMarkup(row_width=2)
    start_btn = types.InlineKeyboardButton('СТАРТ!', callback_data='call_start')
    markup.add(start_btn)
    bot.send_message(CHANNEL_ID, 'Начать новый забег?', reply_markup=markup)
    start_btn_clicked = False


def show_bets_panel():
    markup = types.InlineKeyboardMarkup(row_width=4)
    btns = []
    for num in range(race.tracks_cnt):
        btns.append(types.InlineKeyboardButton(str(num+1) + ' - ' + race.racers[num]['animal'],
                                               callback_data='call_bet_'+str(num)))
    markup.row(btns[0], btns[1], btns[2], btns[3])
    markup.row(btns[4], btns[5], btns[6], btns[7])
    msg = bot.send_message(CHANNEL_ID, 'Выбирайте на кого ставить:', reply_markup=markup)
    return msg.message_id


def do_race(main_msg_id):
    bets_panel_msg_id = show_bets_panel()
    time.sleep(45)
    bot.delete_message(CHANNEL_ID, bets_panel_msg_id)
    write_bets()
    run_race(main_msg_id)
    finish_race(main_msg_id)
    show_start_btn()


def init_race(caller):
    race.new_race(caller.from_user.id)
    bot.delete_message(CHANNEL_ID, caller.message.message_id)
    msg = bot.send_message(CHANNEL_ID, 'Новый забег вот-вот начнется!\n\n' + race.formatted_tracks,
                           parse_mode='Markdown')
    return msg.message_id


def write_bets():
    for user_id, user_rec in users.items():
        if user_rec.track:
            if race.set_bet(user_id, user_rec.track, user_rec.bet):
                user_rec.put_msg('Ваша ставка {}💰 на {} бегущего по {}️⃣ дорожке принята.'.format(
                    user_rec.bet, race.racers[user_rec.track-1]['animal'], user_rec.track
                ))
            else:
                user_rec.put_msg('Извините, по технической причине Ваша ставка не была принята.')


def run_race(msg_id):
    while race.run():
        bot.edit_message_text('Идет забег!!!\n\n' + race.formatted_tracks, chat_id=CHANNEL_ID, message_id=msg_id,
                              parse_mode='Markdown')
        time.sleep(1.5)


def finish_race(msg_id):
    bot.edit_message_text('Забег завершен.\n\n' + race.formatted_tracks, chat_id=CHANNEL_ID, message_id=msg_id,
                          parse_mode='Markdown')

    result_list = ['''*Победители забега:*
    `🥇 - {}`
    `🥈 - {}`
    `🥉 - {}`
    '''.format(*race.winners)]

    # Обработка race.result
    medal = {1: '🥇', 2: '🥈', 3: '🥉'}
    for i, row in enumerate(race.result):
        users[row['user_id']].end_race(row)
        if row['place']:
            result_list.append('\n`{}{:<10.10} {:>5}💰`'.format(medal[row['place']], row['first_name'], row['won']))
        elif i < 10:
            result_list.append('\n`   {:<10.10} {:>5}💰`'.format(row['first_name'], row['won']))

    bot.send_message(CHANNEL_ID, ''.join(result_list), parse_mode='Markdown')


def check_user(new_user):
    if new_user.id not in users:
        users[new_user.id] = user.User(new_user.id)
    return update_user(new_user.id, new_user.username, new_user.first_name, new_user.last_name)


def msgs_handler():
    while 1:
        for user_id in dict(users):
            msg = users[user_id].get_msg()
            if msg:
                try:
                    bot.send_message(user_id, msg, parse_mode='Markdown')
                    time.sleep(0.33)
                except telebot.apihelper.ApiException:
                    logger.exception('Error sending msg: %s to user: %d', msg, user_id)


def logger_init():
    # logging.basicConfig(level=logging.DEBUG)

    # Console logging
    console_formatter = logging.Formatter(
        '%(asctime)s (%(filename)s:%(lineno)d %(funcName)s) %(levelname)s - %(name)s: "%(message)s"'
    )
    console_output_handler = logging.StreamHandler()
    console_output_handler.setFormatter(console_formatter)
    console_output_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_output_handler)

    # Logging via telegram
    bot_formatter = logging.Formatter('%(message)s')
    bot_output_handler = BotHandler(bot)
    bot_output_handler.setFormatter(bot_formatter)
    bot_output_handler.setLevel(logging.INFO)
    logger.addHandler(bot_output_handler)

    logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    logger_init()
    logger.info("Animal races bot started")
    threading.Thread(target=msgs_handler).start()
    show_start_btn()
    while 1:
        try:
            logger.info("start polling")
            bot.polling(none_stop=True)
        except requests.exceptions.ReadTimeout as e:
            logger.exception('ReadTimeout')
            print(e)
            time.sleep(10)
        except requests.exceptions.ConnectionError as e:
            logger.exception('ConnectionError')
            print(e)
            time.sleep(10)
        except KeyboardInterrupt as e:
            print('хуй')
            logger.exception('Inetrrupted by user')
            raise SystemExit(0)
        except Exception as e:
            logger.exception('unexpected Exception')
            print(e)
            time.sleep(10)
