import sqlite3
import logging
from config import *

logger = logging.getLogger('AnimalRaces')


def update_user(user_id, user_name, first_name, last_name):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.debug(
                "INSERT or IGNORE INTO User (tlg_id, user_name, first_name, last_name) VALUES(%d,'%s','%s','%s')",
                user_id, user_name, first_name, last_name)
            curs = conn.execute('''INSERT or IGNORE INTO User
            (tlg_id, user_name, first_name, last_name) VALUES(?,?,?,?)''',
                                (user_id, user_name, first_name, last_name))
            if curs.rowcount == 0:
                logger.debug("UPDATE User SET user_name='%s', first_name='%s', last_name='%s' WHERE tlg_id=%d",
                             user_name, first_name, last_name, user_id)
                conn.execute('UPDATE User SET user_name=?, first_name=?, last_name=? WHERE tlg_id=?',
                             (user_name, first_name, last_name, user_id))
                logger.debug('User updated')
                return False
            else:
                logger.info('Новый пользователь: %d `%s %s` (@`%s`)', user_id, first_name, last_name, user_name)
                return True
    except sqlite3.Error:
        logger.info("INSERT or IGNORE into User (tlg_id, user_name, first_name, last_name) VALUES(%d,'%s','%s','%s')",
                    user_id, user_name, first_name, last_name)
        logger.info("UPDATE User SET user_name='%s', first_name='%s', last_name='%s' WHERE tlg_id=%d",
                    user_name, first_name, last_name, user_id)
        logger.warning('Ошибка добавления/обновления записи TlgrUser: %d `%s %s` (@`%s`)',
                       user_id, first_name, last_name, user_name)
        return False


def new_race(tracks_cnt, user_id):
    if not 0 < tracks_cnt <= 10:
        logger.error('Количество дорожек должно быть от 1 до 10')
        return None
    try:
        with sqlite3.connect(SQLITE_DB_FILE, isolation_level=None) as conn:
            logger.debug("""PRAGMA foreign_keys=ON;
            INSERT INTO Race (utc_time, started_user) SELECT strftime('%%s', 'now'), %d;
            CREATE TEMP TABLE rnd_emoji AS
            SELECT emoji, last_insert_rowid() as race_id FROM Animal ORDER BY RANDOM() LIMIT %d;
            WITH tracks_gen AS (SELECT race_id,
            (SELECT COUNT(*) FROM rnd_emoji b WHERE a.rowid >= b.rowid) as track, emoji as animal
            FROM rnd_emoji a)
            INSERT INTO Tracks (race_id, animal, track) SELECT * FROM tracks_gen;
            SELECT race_id FROM Tracks WHERE id = last_insert_rowid()""", user_id or -1, tracks_cnt)
            conn.execute('BEGIN')
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute("INSERT INTO Race (utc_time, started_user) SELECT strftime('%s', 'now'), ?", (user_id,))
            conn.execute('''CREATE TEMP TABLE rnd_emoji AS
            SELECT emoji as animal, last_insert_rowid() as race_id FROM Animal ORDER BY RANDOM() LIMIT ?''',
                         (tracks_cnt,))
            conn.execute('''WITH tracks_gen AS (SELECT animal, race_id,
            (SELECT COUNT(*) FROM rnd_emoji b WHERE a.rowid >= b.rowid) as track
            FROM rnd_emoji a)
            INSERT INTO Tracks (animal, race_id, track) SELECT * FROM tracks_gen''')
            race_id = conn.execute('SELECT race_id FROM Tracks WHERE id = last_insert_rowid()').fetchone()[0]
            conn.execute('COMMIT')
            return race_id
    except sqlite3.Error:
        logger.info("""PRAGMA foreign_keys=ON;
        INSERT INTO Race (utc_time, started_user) SELECT strftime('%%s', 'now'), %d;
        CREATE TEMP TABLE rnd_emoji AS
        SELECT emoji, last_insert_rowid() as race_id FROM Animal ORDER BY RANDOM() LIMIT %d;
        WITH tracks_gen AS (SELECT race_id,
        (SELECT COUNT(*) FROM rnd_emoji b WHERE a.rowid >= b.rowid) as track, emoji as animal
        FROM rnd_emoji a)
        INSERT INTO Tracks (race_id, animal, track) SELECT * FROM tracks_gen;
        SELECT race_id FROM Tracks WHERE id = last_insert_rowid()""", user_id or -1, tracks_cnt)
        logger.error('Ошибка создания нового забега в БД')
        return None


def get_animals(race_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.debug('SELECT animal FROM tracks WHERE race_id = %d ORDER BY track', race_id)
            results = conn.execute('SELECT animal FROM tracks WHERE race_id = ? ORDER BY track', (race_id,)).fetchall()
    except sqlite3.Error:
        logger.info('SELECT animal FROM tracks WHERE race_id = %d ORDER BY track', race_id)
        logger.error('Ошибка получения из БД списка животных в забеге')
        return None

    animals = []
    for result in results:
        animals.append(result[0])
    return animals


def set_bet(user_id, race_id, track_num, money):
    try:
        with sqlite3.connect(SQLITE_DB_FILE, isolation_level=None) as conn:
            logger.debug('''BEGIN TRANSACTION;
            PRAGMA foreign_keys=ON;
            WITH track_bet AS
            (SELECT %d as user_id, id as track_id, %d as money 
            FROM Tracks WHERE race_id = %d AND track = %d)
            INSERT INTO Bets (user_id, track_id, money) SELECT * FROM track_bet;
            COMMIT TRANSACTION''', user_id, money, race_id, track_num)
            conn.execute('BEGIN TRANSACTION')
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('UPDATE User SET money = MAX(0,money - ?) WHERE tlg_id = ?', (money, user_id))
            conn.execute('''WITH track_bet AS
            (SELECT ? as user_id, id as track_id, ? as money FROM Tracks WHERE race_id = ? AND track = ?)
            INSERT INTO Bets (user_id, track_id, money) SELECT * FROM track_bet''',
                         (user_id, money, race_id, track_num))
            conn.execute('COMMIT TRANSACTION')
    except sqlite3.Error:
        logger.info('''BEGIN TRANSACTION;
        PRAGMA foreign_keys=ON;
        WITH track_bet AS
        (SELECT %d as user_id, id as track_id, %d as money 
        FROM Tracks WHERE race_id = %d AND track = %d)
        INSERT INTO Bets (user_id, track_id, money) SELECT * FROM track_bet;
        COMMIT TRANSACTION''', user_id, money, race_id, track_num)
        logger.error('Ставка от %d (money: %d) не принята в БД', user_id, money)


def set_result(race_id, first_track, second_track, third_track):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.debug('''INSERT INTO Result (track_id, place) VALUES
            ((SELECT id FROM Tracks WHERE race_id = %d AND track = %d), 1),
            ((SELECT id FROM Tracks WHERE race_id = %d AND track = %d), 2),
            ((SELECT id FROM Tracks WHERE race_id = %d AND track = %d), 3)''',
                         race_id, first_track, race_id, second_track, race_id, third_track)
            conn.execute('''INSERT INTO Result (track_id, place) VALUES
            ((SELECT id FROM Tracks WHERE race_id = ? AND track = ?), 1),
            ((SELECT id FROM Tracks WHERE race_id = ? AND track = ?), 2),
            ((SELECT id FROM Tracks WHERE race_id = ? AND track = ?), 3)''',
                         (race_id, first_track, race_id, second_track, race_id, third_track))
    except sqlite3.Error:
        logger.info('''INSERT INTO Result (track_id, place) VALUES
                    ((SELECT id FROM Tracks WHERE race_id = %d AND track = %d), 1),
                    ((SELECT id FROM Tracks WHERE race_id = %d AND track = %d), 2),
                    ((SELECT id FROM Tracks WHERE race_id = %d AND track = %d), 3)''',
                    race_id, first_track, race_id, second_track, race_id, third_track)
        logger.error('Ошибка записи результата забега %d в БД', race_id)
    else:
        # проверить ставки игроков и выдать призовые
        update_winners(race_id)


def update_winners(race_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.debug('''UPDATE User SET Money = Money +
            (SELECT bet+won FROM Bets_won WHERE User.tlg_id = Bets_won.user_id AND Bets_won.race_id = %d)
            WHERE tlg_id IN (SELECT user_id FROM Bets_won WHERE Bets_won.race_id = %d)''', race_id, race_id)
            conn.execute('''UPDATE User
            SET Money = Money + (SELECT bet+won FROM Bets_won WHERE User.tlg_id = Bets_won.user_id AND Bets_won.race_id = ?)
            WHERE tlg_id IN (SELECT user_id FROM Bets_won WHERE Bets_won.race_id = ?)''', (race_id, race_id))
    except sqlite3.Error:
        logger.info('''UPDATE User SET Money = Money +
                    (SELECT won FROM Bets_won WHERE User.tlg_id = Bets_won.user_id AND Bets_won.race_id = %d)
                    WHERE tlg_id IN (SELECT user_id FROM Bets_won WHERE Bets_won.race_id = %d)''', race_id, race_id)
        logger.error('Ошибка выдачи призовых забега %d в БД', race_id)


def get_bets_result(race_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            logger.debug('SELECT * FROM Bets_won WHERE race_id = %d ORDER BY won, place', race_id)
            return conn.execute('SELECT * FROM Bets_won WHERE race_id = ? ORDER BY place, won DESC, money DESC',
                                (race_id,)).fetchall()
    except sqlite3.Error:
        logger.info('SELECT * FROM Bets_won WHERE race_id = %d ORDER BY place, won DESC, money DESC', race_id)
        logger.error('Ошибка получения из БД результатов забега', race_id)


def get_money(user_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.debug('SELECT Money FROM User WHERE tlg_id = %d', user_id)
            return conn.execute('SELECT Money FROM User WHERE tlg_id = ?', (user_id,)).fetchone()[0]
    except sqlite3.Error:
        logger.info('SELECT Money FROM User WHERE tlg_id = %d', user_id)
        logger.error('Ошибка получения из БД количества денег игрока: %d', user_id)


def get_last_bet(user_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.debug('''SELECT money FROM Bets JOIN Tracks ON track_id = Tracks.id
            JOIN Race ON race_id = Race.id WHERE user_id = %d
            ORDER BY utc_time DESC LIMIT 1''', user_id)
            return conn.execute('''SELECT money FROM Bets JOIN Tracks ON track_id = Tracks.id
            JOIN Race ON race_id = Race.id WHERE user_id = ?
            ORDER BY utc_time DESC LIMIT 1''', (user_id,)).fetchone()[0]
    except sqlite3.Error:
        logger.info('''SELECT money FROM Bets JOIN Tracks ON track_id = Tracks.id
                    JOIN Race ON race_id = Race.id WHERE user_id = %d
                    ORDER BY utc_time DESC LIMIT 1''', user_id)
        logger.error('Ошибка получения из БД последней ставки игрока: %d', user_id)
