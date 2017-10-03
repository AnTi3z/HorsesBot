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
                logger.debug("UPDATE User SET user_name='%s', first_name='%s', last_name='%s' WHERE user_id=%d",
                             user_name, first_name, last_name, user_id)
                conn.execute('UPDATE User SET user_name=?, first_name=?, last_name=? WHERE user_id=?',
                             (user_name, first_name, last_name, user_id))
                logger.debug('User updated')
                return False
            else:
                logger.info('Новый пользователь: %d `%s %s` (@`%s`)', user_id, first_name, last_name, user_name)
                return True
    except sqlite3.IntegrityError:
        logger.warning('Ошибка добавления/обновления записи TlgrUser: %d `%s %s` (@`%s`)', user_id, first_name, last_name, user_name)
        return False


def new_race(tracks_cnt):
    if not 0 < tracks_cnt <= 10:
        logger.error('Количество дорожек должно быть от 1 до 10')
        return None
    try:
        with sqlite3.connect(SQLITE_DB_FILE, isolation_level=None) as conn:
            logger.debug(
                "PRAGMA foreign_keys=ON;"
                "INSERT INTO Race (utc_time) SELECT strftime('%s', 'now');"
                "CREATE TEMP TABLE rnd_emoji AS "
                "SELECT emoji, last_insert_rowid() as race_id FROM Animal ORDER BY RANDOM() LIMIT %d;"
                "WITH tracks_gen AS (SELECT race_id,"
                "(SELECT COUNT(*) FROM rnd_emoji b WHERE a.rowid >= b.rowid) as track,"
                "emoji as animal"
                "FROM rnd_emoji a)"
                "INSERT INTO Tracks (race_id, animal, track) SELECT * FROM tracks_gen;"
                "SELECT race_id FROM Tracks WHERE id = last_insert_rowid()",
                tracks_cnt)
            conn.execute('BEGIN TRANSACTION')
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute("INSERT INTO Race (utc_time) SELECT strftime('%s', 'now')")
            conn.execute('''CREATE TEMP TABLE rnd_emoji AS
                SELECT emoji as animal, last_insert_rowid() as race_id FROM Animal ORDER BY RANDOM() LIMIT ?''',(tracks_cnt,))
            conn.execute('''WITH tracks_gen AS (SELECT animal, race_id,
                (SELECT COUNT(*) FROM rnd_emoji b WHERE a.rowid >= b.rowid) as track
                FROM rnd_emoji a)
                INSERT INTO Tracks (animal, race_id, track) SELECT * FROM tracks_gen''')
            race_id = conn.execute('SELECT race_id FROM Tracks WHERE id = last_insert_rowid()').fetchone()[0]
            conn.execute('COMMIT')
            return race_id
    except sqlite3.Error:
        logger.error('Ошибка создания нового забега в БД')
        return None


def get_animals(race_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.debug('SELECT animal FROM tracks WHERE race_id = %d ORDER BY track', race_id)
            results = conn.execute('SELECT animal FROM tracks WHERE race_id = ? ORDER BY track', (race_id,)).fetchall()
    except sqlite3.Error:
        logger.error('Ошибка получения списка животных в забеге')
        return None

    animals = []
    for result in results:
        animals.append(result[0])
    return animals


def set_bet(user_id, race_id, track_num, money):
    # conn.execute('BEGIN TRANSACTION')
    # conn.execute('PRAGMA foreign_keys=ON')
    # уменьшить сумму у игрока
    # получить track_id = ('SELECT id FROM Tracks WHERE race_id = ? AND track = ?', (race_id, track_num)).fetchone()[0]
    # записать ставку
    # ('INSERT INTO Bets (user_id, track_id, money) VALUES (?,?,?)', (user_id, track_id, money))
    pass


def set_result(race_id, first_track, second_track, third_track):
    # записать результат в базу
    # проверить ставки игроков
    pass


def get_bets_result(race_id):
    pass

