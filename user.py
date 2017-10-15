import db_wrap
import queue
import time


class User:

    def __init__(self, user_id):
        self._user_id = user_id
        self.track = None
        self.menu = 0
        self._last_msg_utc = 0

        self._money = db_wrap.get_money(self._user_id)
        self._bet = db_wrap.get_last_bet(self._user_id) or 10
        self._msg_queue = queue.Queue()

    @property
    def status_msg(self):
        return '`Баланс: {:>12}💰`\n`Размер ставки: {:>5}💰`\n\n' \
               '`Макс. ставка: {:>6}💰`\n\n' \
               '[Наблюдать за гонкой](https://t.me/animal_races)'.format(self._money, self._bet, self.max_bet)

    def end_race(self, result):
        if self.track:
            self.track = None
            self._money = db_wrap.get_money(self._user_id)
            if result['place']:
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}
                self.put_msg('Поздравляю! Ваша ставка заняла {} место.\nВы заработали {}💰'.format(
                    medal[result['place']], result['won']))
            else:
                self.put_msg('К сожалению, Ваша ставка проиграла.\nВы потеряли {}💰'.format(-result['won']))
                if self._money <= 100:
                    credit = 1000 - self._money
                    db_wrap.set_money(self._user_id, 1000)
                    self.put_msg('Невероятнейшим образом Вам удалось спустить почти все ваши деньги на скачках.\n'
                                 'Приняв предложение распорядителя, от которого Вы не смогли отказаться, '
                                 'и проведя с ним бурную ночь, Вы получили от него {}💰\n'
                                 '(Сложилось впечатление, что с Вами это не впервой)'.format(credit))
                    self._money = db_wrap.get_money(self._user_id)
                if self._bet > self.max_bet:
                    self.set_bet(self.max_bet)

            self.put_msg(self.status_msg)

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
        return max(int(self._money * 0.1), self._money - 1000)

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
        now = time.clock()
        if not self._msg_queue.empty() and (now - self._last_msg_utc) >= 1:
            self._last_msg_utc = now
            next_msg = self._msg_queue.get()
            if next_msg[1] is not None:
                self.menu = next_msg[1]
            return next_msg[0]
        else:
            return None

    def put_msg(self, msg, menu=None):
        self._msg_queue.put((msg, menu))
