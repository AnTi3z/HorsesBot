#!/usr/local/bin/python

import time
import telebot
from telebot import types
import logging
import requests
import random
import threading
from config import *


logger = logging.getLogger('AnimalRaces')


class BotHandler(logging.Handler):
    def __init__(self, bot):
        logging.Handler.__init__(self)
        self.bot_obj = bot

    def emit(self, record):
        msg = self.format(record)
        bot.send_message(OWNER_ID, msg, parse_mode='Markdown')


bot = telebot.TeleBot(TOKEN, threaded=False)
me = bot.get_me()
animals = ('🐆','🐅','🐃','🐂','🐄','🦌','🐪','🐫','🐘','🦏','🦍','🐎','🐖','🐐','🐏','🐑','🐕','🐩','🐈','🐓','🦃','🕊','🐇','🐁','🐀','🐿','🐢','🐜','🐍','🦂','🦀')
racers = []
winners = []
bets = {}
start_btn_clicked = False


@bot.message_handler(func=lambda msg: True, commands=['start'])
def on_start(msg):
    show_start_btn()


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global bets, start_btn_clicked
    logger.debug(call)
    if call.data == 'call_start' and not start_btn_clicked:
        start_btn_clicked = True
        init_race(call.message.message_id)
        logger.debug('Race init by {}'.format(call.from_user.first_name))
        threading.Thread(target=do_race, args=(call.message.message_id,)).start()
    elif 'call_bet_' in call.data:
        bets[call.from_user.first_name] = int(call.data[9:])
        logger.debug('{} bets on {}'.format(call.from_user.first_name, call.data[9:]))


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
    for num in range(TRACKS_NUM):
        btns.append(types.InlineKeyboardButton(str(num+1) + ' - ' + racers[num]['animal'], callback_data='call_bet_'+str(num)))
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
    global winners, bets, racers
    racers = []
    rnd_animals_indx = random.sample(range(len(animals)), TRACKS_NUM)
    for i in range(TRACKS_NUM):
       racer = {'animal' : animals[rnd_animals_indx[i]], 'position' : 0}
       racers.append(racer)
    winners = []
    bets = {}
    bot.edit_message_text('Новый забег вот-вот начнется!\n\n' + get_formated_text(), chat_id=CHANNEL_ID, message_id=msg_id,
                          parse_mode='Markdown')


def run_race(msg_id):
    while len(winners) < 3:
        random_move_racers()
        bot.edit_message_text('Идет забег!!!\n\n' + get_formated_text(), chat_id=CHANNEL_ID, message_id=msg_id,
                              parse_mode='Markdown')
        time.sleep(1.5)


def finish_race(msg_id):
    bot.edit_message_text('Забег завершен.\n\n' + get_formated_text(), chat_id=CHANNEL_ID, message_id=msg_id,
                          parse_mode='Markdown')

    won_bets = [[],[],[]]

    for bet in bets.items():
        if bet[1] == winners[0]:
            won_bets[0].append(bet[0])
        elif bet[1] == winners[1]:
            won_bets[1].append(bet[0])
        elif bet[1] == winners[2]:
            won_bets[2].append(bet[0])

    result_text = '''*Победители забега:*
    
    `🥇 - {}` ({})
    `🥈 - {}` ({})
    `🥉 - {}` ({})'''.format(racers[winners[0]]['animal'], won_bets[0],
                            racers[winners[1]]['animal'], won_bets[1],
                            racers[winners[2]]['animal'], won_bets[2])
    bot.send_message(CHANNEL_ID, result_text, parse_mode='Markdown')


def get_formated_text():
    result_text = []
    for racer_num in range(TRACKS_NUM):
        position = racers[racer_num]['position']
        animal = racers[racer_num]['animal']
        if position < RACE_LEN:
            racer_row = '`🏁{}{}{}|{}️⃣`'.format('-' * (RACE_LEN - position), animal, '-' * position, racer_num + 1)
        else:
            if racer_num == winners[0]: prize = '🏆'
            elif racer_num == winners[1]: prize = '🥈'
            elif racer_num == winners[2]: prize = '🥉'
            else: prize = '🏁'
            racer_row = '`{}{}{}|{}️⃣`'.format(prize, animal, '-' * RACE_LEN, racer_num + 1)
        result_text.append(racer_row)

    return '\n'.join(result_text)


def random_move_racers():
    global racers
    rnd_num = random.sample(range(TRACKS_NUM), TRACKS_NUM)
    for racer_num in rnd_num:
        rnd = random.randint(0, 100)
        if rnd < 20: rnd = 0
        elif rnd < 50: rnd = 2
        else: rnd = 1
        racers[racer_num]['position'] += rnd
        if racers[racer_num]['position'] >= RACE_LEN and not racer_num in winners: winners.append(racer_num)
        if len(winners) >= 3: break


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
