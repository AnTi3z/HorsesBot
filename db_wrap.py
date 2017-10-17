import sqlite3
import logging

from config import *

logger = logging.getLogger('AnimalRaces')

logging.SQL = 5
logging.addLevelName(logging.SQL, "SQL")


def sql(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if self.isEnabledFor(logging.SQL):
        self._log(logging.SQL, message, args, **kws)


logging.Logger.sql = sql


def update_user(user_id, user_name, first_name, last_name):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.sql(
                "INSERT or IGNORE INTO User (tlg_id, user_name, first_name, last_name) VALUES(%d,'%s','%s','%s')",
                user_id, user_name, first_name, last_name)
            curs = conn.execute('''INSERT or IGNORE INTO User
            (tlg_id, user_name, first_name, last_name) VALUES(?,?,?,?)''',
                                (user_id, user_name, first_name, last_name))
            if curs.rowcount == 0:
                logger.sql("UPDATE User SET user_name='%s', first_name='%s', last_name='%s' WHERE tlg_id=%d",
                           user_name, first_name, last_name, user_id)
                conn.execute('UPDATE User SET user_name=?, first_name=?, last_name=? WHERE tlg_id=?',
                             (user_name, first_name, last_name, user_id))
                # logger.debug('User updated')
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
            logger.sql("""PRAGMA foreign_keys=ON;
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
        logger.exception('Ошибка создания нового забега в БД')
        return None


def get_animals(race_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.sql('SELECT animal FROM tracks WHERE race_id = %d ORDER BY track', race_id)
            results = conn.execute('SELECT animal FROM tracks WHERE race_id = ? ORDER BY track', (race_id,)).fetchall()
    except sqlite3.Error:
        logger.info('SELECT animal FROM tracks WHERE race_id = %d ORDER BY track', race_id)
        logger.exception('Ошибка получения из БД списка животных в забеге')
        return None

    animals = []
    for result in results:
        animals.append(result[0])
    return animals


def set_bet(user_id, race_id, track_num, money):
    try:
        with sqlite3.connect(SQLITE_DB_FILE, isolation_level=None) as conn:
            logger.sql('''BEGIN;
            PRAGMA foreign_keys=ON;
            WITH track_bet AS
            (SELECT %d as user_id, id as track_id, %d as money 
            FROM Tracks WHERE race_id = %d AND track = %d)
            INSERT INTO Bets (user_id, track_id, money) SELECT * FROM track_bet;
            COMMIT''', user_id, money, race_id, track_num)
            conn.execute('BEGIN')
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('''WITH track_bet AS
            (SELECT ? as user_id, id as track_id, ? as money FROM Tracks WHERE race_id = ? AND track = ?)
            INSERT INTO Bets (user_id, track_id, money) SELECT * FROM track_bet''',
                         (user_id, money, race_id, track_num))
            conn.execute('COMMIT')
            return True
    except sqlite3.Error:
        logger.info('''BEGIN;
        PRAGMA foreign_keys=ON;
        WITH track_bet AS
        (SELECT %d as user_id, id as track_id, %d as money 
        FROM Tracks WHERE race_id = %d AND track = %d)
        INSERT INTO Bets (user_id, track_id, money) SELECT * FROM track_bet;
        COMMIT''', user_id, money, race_id, track_num)
        logger.exception('Ставка от %d (money: %d) не принята в БД', user_id, money)
        return False


def set_result(race_id, first_track, second_track, third_track):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.sql('''INSERT INTO Result (track_id, place) VALUES
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
        logger.exception('Ошибка записи результата забега %d в БД', race_id)
    else:
        update_bets_result(race_id)


def update_bets_result(race_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.sql('''UPDATE User SET Money = Money +
            (SELECT won FROM Bets_result WHERE User.tlg_id = Bets_result.user_id AND Bets_result.race_id = %d)
            WHERE tlg_id IN (SELECT user_id FROM Bets_result WHERE Bets_result.race_id = %d)''', race_id, race_id)
            conn.execute('''UPDATE User SET Money = Money +
            (SELECT won FROM Bets_result WHERE User.tlg_id = Bets_result.user_id AND Bets_result.race_id = ?)
            WHERE tlg_id IN (SELECT user_id FROM Bets_result WHERE Bets_result.race_id = ?)''', (race_id, race_id))
    except sqlite3.Error:
        logger.info('''UPDATE User SET Money = Money +
        (SELECT won FROM Bets_result WHERE User.tlg_id = Bets_result.user_id AND Bets_result.race_id = %d)
        WHERE tlg_id IN (SELECT user_id FROM Bets_result WHERE Bets_result.race_id = %d)''', race_id, race_id)
        logger.exception('Ошибка расчета призовых забега %d в БД', race_id)


def get_bets_result(race_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            logger.sql('SELECT * FROM Bets_result WHERE race_id = %d'
                       'ORDER BY place IS NULL, place, won DESC, money DESC', race_id)
            return conn.execute('SELECT * FROM Bets_result WHERE race_id = ?'
                                'ORDER BY place IS NULL, place, won DESC, money DESC',
                                (race_id,)).fetchall()
    except sqlite3.Error:
        logger.info('SELECT * FROM Bets_result WHERE race_id = %d'
                    'ORDER BY place IS NULL, place, won DESC, money DESC', race_id)
        logger.exception('Ошибка получения из БД результатов забега', race_id)


def get_money(user_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.sql('SELECT Money FROM User WHERE tlg_id = %d', user_id)
            return conn.execute('SELECT Money FROM User WHERE tlg_id = ?', (user_id,)).fetchone()[0]
    except sqlite3.Error:
        logger.info('SELECT Money FROM User WHERE tlg_id = %d', user_id)
        logger.exception('Ошибка получения из БД количества денег игрока: %d', user_id)


def set_money(user_id, money):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.sql('UPDATE User SET Money = %d WHERE tlg_id = %d', money, user_id)
            conn.execute('UPDATE User SET Money = ? WHERE tlg_id = ?', (money, user_id))
    except sqlite3.Error:
        logger.info('UPDATE User SET Money = %d WHERE tlg_id = %d', money, user_id)
        logger.exception('Ошибка записи в БД %d денег игроку: %d', money, user_id)


def get_last_bet(user_id):
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.sql('''SELECT money FROM Bets JOIN Tracks ON track_id = Tracks.id
            JOIN Race ON race_id = Race.id WHERE user_id = %d
            ORDER BY utc_time DESC LIMIT 1''', user_id)
            result = conn.execute('''SELECT money FROM Bets JOIN Tracks ON track_id = Tracks.id
            JOIN Race ON race_id = Race.id WHERE user_id = ?
            ORDER BY utc_time DESC LIMIT 1''', (user_id,)).fetchone()
            if result:
                return result[0]
            else:
                return None
    except sqlite3.Error:
        logger.info('''SELECT money FROM Bets JOIN Tracks ON track_id = Tracks.id
                    JOIN Race ON race_id = Race.id WHERE user_id = %d
                    ORDER BY utc_time DESC LIMIT 1''', user_id)
        logger.exception('Ошибка получения из БД последней ставки игрока: %d', user_id)


def get_main_stat():
    result = {}
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            logger.sql('SELECT COUNT(*) FROM User')
            result['users'] = conn.execute('SELECT COUNT(*) FROM User').fetchone()[0]
            logger.sql('SELECT COUNT(*) FROM Race')
            result['races'] = conn.execute('SELECT COUNT(*) FROM Race').fetchone()[0]
            logger.sql('SELECT COUNT(*) FROM Animal')
            result['animals'] = conn.execute('SELECT COUNT(*) FROM Animal').fetchone()[0]
            logger.sql('SELECT COUNT(*), SUM(money) FROM Bets')
            result['bets'], result['moneys'] = conn.execute('SELECT COUNT(*), SUM(money) FROM Bets').fetchone()
            return result
    except sqlite3.Error:
        logger.info('SELECT COUNT(*) FROM User')
        logger.info('SELECT COUNT(*) FROM Race')
        logger.info('SELECT COUNT(*) FROM Animal')
        logger.info('SELECT COUNT(*), SUM(money) FROM Bets')
        logger.exception('Ошибка получения статистики из БД')
        return None


def get_players_stat():
    try:
        with sqlite3.connect(SQLITE_DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            logger.sql('SELECT * FROM Players_stat')
            return conn.execute('SELECT * FROM Players_stat').fetchall()
    except sqlite3.Error:
        logger.info('SELECT * FROM Players_stat')
        logger.exception('Ошибка получения из БД статистики игроков')
