import queue
import time
import logging

import db_wrap
from utils import strip_emoji

logger = logging.getLogger('AnimalRaces')


class User:
    msgs_queued = 0

    def __init__(self, user_id):
        self._user_id = user_id
        self.track = None
        self.menu = 0
        self._last_msg_utc = 0

        user_data = db_wrap.get_user_data(self._user_id)
        self.first_name = strip_emoji(user_data['first_name'])
        self._money = user_data['money']
        self._level = user_data['level']
        self._bet = db_wrap.get_last_bet(self._user_id) or 10
        self._msg_queue = queue.Queue()

    @property
    def status_msg(self):
        return ' *{}*\n' \
               '️Уровень {}⚜️️\n\n' \
               '`Баланс {:>15}💰`\n' \
               '`Размер ставки {:>8}💰`\n\n' \
               '`Макс. ставка  {:>8}💰`\n' \
               '`Начальный кредит {:>5}💰`\n' \
               '`След. уровень {:>8}💰`\n\n' \
               '[Ссылка на забеги](https://t.me/animal_races)'.format(self.first_name, self._level,
                                                                      self._money, self._bet,
                                                                      self.max_bet, self.low_limit, self.max_limit)

    def end_race(self, result):
        if self.track:
            self.track = None
            self._money = db_wrap.get_money(self._user_id)
            if result['place']:
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}
                self.put_msg('Поздравляю! Ваша ставка заняла {} место.\nВы заработали {}💰'.format(
                    medal[result['place']], result['won']))
                self._check_money()
            else:
                self.put_msg('К сожалению, Ваша ставка проиграла.\nВы потеряли {}💰'.format(-result['won']))
                self._check_money()
            self.put_msg(self.status_msg)

    def _check_money(self):
        if self._money >= self.max_limit:
            self._level_up()
        elif self._money <= self.low_limit / 10:
            self._give_credit()
        if self._bet > self.max_bet:
            self.set_bet(self.max_bet)

    def set_money(self, money):
        self._money = money
        self._check_money()

    @property
    def user_id(self):
        return self._user_id

    @property
    def money(self):
        return self._money

    @property
    def bet(self):
        if not self._bet:
            self._bet = db_wrap.get_last_bet(self._user_id) or 10
        return self._bet

    @property
    def max_bet(self):
        return max(int(self._money * 0.1), self._money - self.low_limit)

    @property
    def low_limit(self):
        return 1000 * (self._level * self._level + self._level) // 2

    @property
    def max_limit(self):
        return self.low_limit * 20

    def _give_credit(self):
        logger.debug('Выдача кредита: %s', self.first_name)
        credit = self.low_limit - self._money
        if db_wrap.set_money(self._user_id, self.low_limit):
            self._money = self.low_limit
            self.put_msg('Невероятнейшим образом Вам удалось спустить почти все ваши деньги на скачках.\n'
                         'Приняв предложение распорядителя, от которого Вы не смогли отказаться, '
                         'и проведя с ним бурную ночь, Вы получили от него {}💰\n'
                         '(Сложилось впечатление, что с Вами это не впервой)'.format(credit))
        else:
            logger.error('Ошибка при выдаче кредита: %s', self.first_name)

    def _level_up(self):
        logger.debug('Повышение уровня: %s', self.first_name)
        credit = self.low_limit + (self._level+1) * 1000
        if db_wrap.set_level_money(self._user_id, self._level+1, credit):
            self._level += 1
            self._money = self.low_limit
            self.put_msg('Поздравляем. Вы достигли {} уровня.\n'
                         'Ваш начальный кредит и максимальная сумма на счете возросли, '
                         'но Вам за это пришлось расплатиться почти всей имеющейся у Вас '
                         'наличностью.\n'.format(self._level))
        else:
            logger.error('Ошибка повышения уровня игрока: %s', self.first_name)

    def set_bet(self, val):
        result_text = []

        if val > self.max_bet:
            self._bet = self.max_bet
            result_text.append('У Вас на счету {}💰\n'
                               'Вы можете поставить максимум {}💰\n'.format(self._money, self.max_bet))
        elif val < 10:
            self._bet = 10
            result_text.append('Минимальная ставка 10💰\n')
        else:
            self._bet = val

        result_text.append('Размер ставки установлен {}💰'.format(self._bet))
        self.put_msg(''.join(result_text))

    def get_msg(self):
        if self._msg_queue.empty():
            return None

        now = time.perf_counter()
        if (now - self._last_msg_utc) < 0.7:
            return None

        self._last_msg_utc = now
        next_msg = self._msg_queue.get()
        User.msgs_queued -= 1
        if next_msg[1] is not None:
            self.menu = next_msg[1]
        return next_msg[0]

    def put_msg(self, msg, menu=None):
        self._msg_queue.put((msg, menu))
        User.msgs_queued += 1
