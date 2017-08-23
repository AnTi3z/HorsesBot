#!/usr/local/bin/python

import time
import telebot
import logging
import requests
import random


TOKEN = '374411418:AAFLZOyh7eNisH0cYut1uwKry-af7t6At8I'
#CHANNEL_ID =  -1001141707367 #Animal races channel
CHANNEL_ID = -1001128050160 #testing group
TRACKS_NUM = 8


#logging.basicConfig(level = logging.DEBUG)


bot = telebot.TeleBot(TOKEN,threaded=False)
me = bot.get_me()
#horses = []
#winners = []
#animals = ['🐒','🦆','🐓','🐿','🐑','🐖','🐀','🦍','🐐']
animals = ['🐆','🐅','🐃','🐂','🐄','🦌','🐪','🐫','🐘','🦏','🦍','🐎','🐖','🐐','🐏','🐑','🐕','🐩','🐈','🐓','🦃','🕊','🐇','🐁','🐀','🐿','🐢','🐜','🐍','🦂','🦀']


@bot.message_handler(func=lambda msg: True, commands=['start'])
def on_start(msg):
    while 1:
        msg_id = init_race()
        time.sleep(60)
        go_race(msg_id)
        finish_race()
        time.sleep(600)


def init_race():
    global horses, winners
    horses = TRACKS_NUM * [0]
    winners = []
    random.shuffle(animals)
    msg = bot.send_message(CHANNEL_ID, 'Новый забег вот-вот начнется!\n\n' + get_formated_text(), parse_mode='Markdown')
    return msg.message_id


def go_race(msg_id):
    while len(winners) < 3:
        random_move_horses()
        bot.edit_message_text('Идет забег!!!\n\n' + get_formated_text(), chat_id=CHANNEL_ID, message_id=msg_id, parse_mode='Markdown')
        #bot.send_message(CHANNEL_ID, get_formated_text(), parse_mode='Markdown')
        time.sleep(1)
    bot.edit_message_text('Забег завершен.\n\n' + get_formated_text(), chat_id=CHANNEL_ID, message_id=msg_id,
                          parse_mode='Markdown')


def finish_race():
    result_text = '''*Победители забега:*
    
    `🥇 - {}`
    `🥈 - {}`
    `🥉 - {}`'''.format(animals[winners[0]], animals[winners[1]], animals[winners[2]])
    bot.send_message(CHANNEL_ID, result_text, parse_mode='Markdown')


def get_formated_text():
    result_text = []
    for horse_num in range(len(horses)):
        if horses[horse_num] < 18:
            horse_row = '`🏁{}{}{}|{}️⃣`'.format('-'*(18-horses[horse_num]),
                                                           animals[horse_num], '-'*horses[horse_num],horse_num+1)
        else:
            if horse_num == winners[0]: prize = '🏆'
            elif horse_num == winners[1]: prize = '🥈'
            elif horse_num == winners[2]: prize = '🥉'
            else: prize = '🏁'
            horse_row = '`{}{}------------------|{}️⃣`'.format(prize, animals[horse_num], horse_num + 1)
        result_text.append(horse_row)

    return '\n'.join(result_text)


def random_move_horses():
    global horses
    rnd_num = [x for x in range(len(horses))]
    random.shuffle(rnd_num)
    for horse_num in rnd_num:
        rnd = random.randint(0, 100)
        if rnd < 20: rnd = 0
        elif rnd < 50: rnd = 2
        else: rnd = 1
        horses[horse_num] = horses[horse_num] + rnd
        if horses[horse_num] >= 18 and not horse_num in winners: winners.append(horse_num)
        if len(winners) >= 3: break


if __name__ == '__main__':
    while 1:
        try:
            logging.info("start polling")
            bot.polling(none_stop=True, interval=1)
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