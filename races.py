#!/usr/local/bin/python

import time
import telebot
from telebot import types
import logging
import requests
import random
import threading
from config import *



#logging.basicConfig(level = logging.DEBUG)


bot = telebot.TeleBot(TOKEN, threaded=False)
me = bot.get_me()
#horses = []
#winners = []
#animals = ['🐒','🦆','🐓','🐿','🐑','🐖','🐀','🦍','🐐']
animals = ['🐆','🐅','🐃','🐂','🐄','🦌','🐪','🐫','🐘','🦏','🦍','🐎','🐖','🐐','🐏','🐑','🐕','🐩','🐈','🐓','🦃','🕊','🐇','🐁','🐀','🐿','🐢','🐜','🐍','🦂','🦀']
racers_position = []
winners = []
bets = {}

@bot.message_handler(func=lambda msg: True, commands=['start'])
def on_start(msg):
    show_start_btn()


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global bets
    if call.data == 'call_start':
        init_race(call.message.message_id)
        threading.Thread(target=do_race, args=(call.message.message_id,)).start()
    elif 'call_bet_' in call.data:
        bets[call.from_user.first_name] = int(call.data[9:])
        print(bets)


def show_start_btn():
    markup = types.InlineKeyboardMarkup(row_width=2)
    start_btn = types.InlineKeyboardButton('СТАРТ!', callback_data='call_start')
    markup.add(start_btn)
    bot.send_message(CHANNEL_ID, 'Начать новый забег?', reply_markup=markup)


def show_bets_panel():
    markup = types.InlineKeyboardMarkup(row_width=4)
    btns = []
    for num in range(TRACKS_NUM):
        btns.append(types.InlineKeyboardButton(str(num+1) + ' - ' + animals[num], callback_data='call_bet_'+str(num)))
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
    global racers_position, winners, bets
    racers_position = TRACKS_NUM * [0]
    winners = []
    bets = {}
    random.shuffle(animals)
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
    `🥉 - {}` ({})'''.format(animals[winners[0]], won_bets[0],
                            animals[winners[1]], won_bets[1],
                            animals[winners[2]], won_bets[2])
    bot.send_message(CHANNEL_ID, result_text, parse_mode='Markdown')


def get_formated_text():
    result_text = []
    for racer_num in range(TRACKS_NUM):
        if racers_position[racer_num] < RACE_LEN:
            racer_row = '`🏁{}{}{}|{}️⃣`'.format('-' * (RACE_LEN - racers_position[racer_num]),
                                                 animals[racer_num], '-' * racers_position[racer_num], racer_num + 1)
        else:
            if racer_num == winners[0]: prize = '🏆'
            elif racer_num == winners[1]: prize = '🥈'
            elif racer_num == winners[2]: prize = '🥉'
            else: prize = '🏁'
            racer_row = '`{}{}------------------|{}️⃣`'.format(prize, animals[racer_num], racer_num + 1)
        result_text.append(racer_row)

    return '\n'.join(result_text)


def random_move_racers():
    global racers_position
    rnd_num = random.sample(range(TRACKS_NUM), TRACKS_NUM)
    # random.shuffle(rnd_num)
    for racer_num in rnd_num:
        rnd = random.randint(0, 100)
        if rnd < 20: rnd = 0
        elif rnd < 50: rnd = 2
        else: rnd = 1
        racers_position[racer_num] = racers_position[racer_num] + rnd
        if racers_position[racer_num] >= RACE_LEN and not racer_num in winners: winners.append(racer_num)
        if len(winners) >= 3: break


if __name__ == '__main__':
    show_start_btn()
    while 1:
        try:
            logging.info("start polling")
            bot.polling(none_stop=True)
        except requests.exceptions.ReadTimeout as e:
            logging.exception('ReadTimeout')
            print(e)
            time.sleep(10)
        except requests.exceptions.ConnectionError as e:
            logging.exception('ConnectionError')
            print(e)
            time.sleep(10)
        except KeyboardInterrupt as e:
            print('хуй')
            logging.exception('Inetrrupted by user')
            raise SystemExit(0)
        except Exception as e:
            logging.exception('unexpected Exception')
            print(e)
            time.sleep(10)