from operator import itemgetter

import db_wrap
from utils import *


def players_gold(user_id):
    stat = db_wrap.get_players_stat()
    sorted_stat = sorted(stat, key=itemgetter('money'), reverse=True)[:10]
    result = ['💰Золото\n\n']
    for row in sorted_stat:
        result.append('`{:<14.14}  {:>5}💰`\n'.format(strip_emoji(row['first_name']), str_human_int(row['money'])))
    return ''.join(result)


def players_level(user_id):
    stat = db_wrap.get_players_stat()
    sorted_stat = sorted(stat, key=itemgetter('level', 'money'), reverse=True)[:10]
    result = ['⚜️Уровень\n\n']
    for row in sorted_stat:
        result.append('`{:<16.16}  {:>3}⚜`\n'.format(strip_emoji(row['first_name']), row['level']))
    return ''.join(result)


def players_wins(user_id, sort_rate=False):
    if sort_rate:
        def sort_key(x):
            if x['bets_cnt'] >= 100:
                return x['wins']/x['bets_cnt'], 0
            else:
                return 0, x['bets_cnt']
    else:
        sort_key = itemgetter('wins')
    stat = db_wrap.get_players_stat()
    sorted_stat = sorted(stat, key=sort_key, reverse=True)[:10]
    result = ['🏆Победы\n\n']
    for row in sorted_stat:
        if sort_rate:
            if row['bets_cnt'] >= 100:
                percent = round(row['wins']*100/row['bets_cnt'], 1)
            else:
                percent = '~~'
            result.append('`{:<10.10} {:>4}% / {:>4}`\n'.format(strip_emoji(row['first_name']),
                                                                 percent, row['bets_cnt']))
        else:
            result.append('`{:<11.11} {:>4} / {:>4}`\n'.format(strip_emoji(row['first_name']),
                                                                row['wins'], row['bets_cnt']))
    return ''.join(result)


def players_prizes(user_id, sort_rate=False):
    if sort_rate:
        def sort_key(x):
            if x['bets_cnt'] >= 100:
                return x['prizes']/x['bets_cnt'], 0
            else:
                return 0, x['bets_cnt']
    else:
        sort_key = itemgetter('prizes')
    stat = db_wrap.get_players_stat()
    sorted_stat = sorted(stat, key=sort_key, reverse=True)[:10]
    result = ['🥇🥈🥉Медали\n\n']
    for row in sorted_stat:
        if sort_rate:
            if row['bets_cnt'] >= 100:
                percent = round(row['prizes']*100/row['bets_cnt'], 1)
            else:
                percent = '~~'
            result.append('`{:<10.10} {:>4}% / {:>4}`\n'.format(strip_emoji(row['first_name']),
                                                                percent, row['bets_cnt']))
        else:
            result.append('`{:<11.11} {:>4} / {:>4}`\n'.format(strip_emoji(row['first_name']),
                                                               row['prizes'], row['bets_cnt']))
    return ''.join(result)


def players_bets(user_id, sort_sum=False):
    if sort_sum:
        sort_key = itemgetter('bets_sum')
    else:
        sort_key = itemgetter('bets_cnt')
    stat = db_wrap.get_players_stat()
    sorted_stat = sorted(stat, key=sort_key, reverse=True)[:10]
    result = ['💰Ставки\n\n']
    for row in sorted_stat:
        if sort_sum:
            result.append('`{:<15.15}  {:>5}💰`\n'.format(strip_emoji(row['first_name']),
                                                          str_human_int(row['bets_sum'])))
        else:
            result.append('`{:<16.16}  {:>4}`\n'.format(strip_emoji(row['first_name']), row['bets_cnt']))
    return ''.join(result)
