import sqlite3
import logging
from config import *

logger = logging.getLogger('AnimalRaces')

def update_user(user_id, user_name, first_name, last_name):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.debug(
                "INSERT or IGNORE into User (tlg_id, user_name, first_name, last_name) VALUES(%d,'%s','%s','%s')",
                user_id, user_name, first_name, last_name)
            curs = conn.execute('INSERT or IGNORE into TlgrUser (tlg_id, user_name, first_name, last_name) VALUES(?,?,?,?)',
                         (user_id, user_name, first_name, last_name))
            if curs.rowcount == 0:
                logger.debug("UPDATE User SET user_name='%s', first_name='%s', last_name='%s' WHERE tlg_id=%d",
                             user_name, first_name, last_name, user_id)
                conn.execute('UPDATE User SET user_name=?, first_name=?, last_name=? WHERE tlg_id=?',
                             (user_name, first_name, last_name, user_id))
                logger.debug('User updated')
                return False
            else:
                logger.info('Tlgr user added: %d `%s %s` (@`%s`)', user_id, first_name, last_name, user_name)
                return True
    except sqlite3.IntegrityError:
        logger.warning('Ошибка добавления/обновления записи TlgrUser: %d `%s %s` (@`%s`)', user_id, first_name, last_name, user_name)
        return False


def new_race():
    # return race_id
    pass


def set_tracks(race_id, animals):
    pass


def set_bet(user_id, race_id, track_num, money):
    pass


def set_result(race_id, first_track, second_track, third_track):
    pass


def get_bets_result(race_id):
    pass


def get_animals():
    pass
