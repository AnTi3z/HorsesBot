#!/usr/local/bin/python

import time
import telebot
from telebot import types
import logging
import requests
import threading
from db_wrap import update_user
from race import Race
from config import *


logger = logging.getLogger('AnimalRaces')


class BotHandler(logging.Handler):
    def __init__(self, bot):
        logging.Handler.__init__(self)
        self.bot_obj = bot

    def emit(self, record):
        msg = self.format(record)
        bot.send_message(OWNER_ID, msg)  # , parse_mode='Markdown')


bot = telebot.TeleBot(TOKEN, threaded=False)
# me = bot.get_me()
start_btn_clicked = False
race = None


#@bot.message_handler(func=lambda msg: True, commands=['start'])
#def on_start(msg):
#    show_start_btn()

@bot.message_handler(func=lambda msg: msg.chat.id == CHANNEL_ID, content_types=['new_chat_members'])
def on_user_joins(msg):
    logger.debug('User joined support channel (id:%d)', msg.new_chat_member.id)
    new_user = msg.new_chat_member
    if update_user(new_user.id, new_user.username, new_user.first_name, new_user.last_name):
        logger.info('New user added(join)')


@bot.message_handler(func=lambda msg: True)
def on_any_msg(msg):
    new_user = msg.from_user
    if update_user(new_user.id, new_user.username, new_user.first_name, new_user.last_name):
        logger.info('New user added(msg)')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global start_btn_clicked
    if update_user(call.from_user.id, call.from_user.username, call.from_user.first_name, call.from_user.last_name):
        logger.info('New user added(button)')
    if call.data == 'call_start' and not start_btn_clicked:
        start_btn_clicked = True
        init_race(call.message.message_id)
        logger.debug('Race init by {}'.format(call.from_user.first_name))
        threading.Thread(target=do_race, args=(call.message.message_id,)).start()
    elif 'call_bet_' in call.data:
        race.set_bet(call.from_user.id, int(call.data[9:])+1, 10)
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
    time.sleep(30)
    bot.delete_message(CHANNEL_ID, bets_panel_msg_id)
    run_race(main_msg_id)
    finish_race(main_msg_id)
    show_start_btn()


def init_race(msg_id):
    global race
    race = Race()
    bot.edit_message_text('Новый забег вот-вот начнется!\n\n' + race.formatted_tracks, chat_id=CHANNEL_ID,
                          message_id=msg_id, parse_mode='Markdown')


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
    for row in race.result:
        result_list.append('\n{}{:<10.10}{:>5}💰({:>5}💰)'.format(medal[row['place']], row['first_name'],
                                                                row['won'], row['money']))

    bot.send_message(CHANNEL_ID, ''.join(result_list), parse_mode='Markdown')


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
