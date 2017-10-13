import db_wrap
import queue
import time


class User:

    def __init__(self, user_id):
        self._user_id = user_id
        self.track = None
        self._menu = None
        self._last_msg_utc = 0

        self._money = db_wrap.get_money(self._user_id)
        self._bet = db_wrap.get_last_bet(self._user_id) or 10
        self._msg_queue = queue.Queue()

    def send_status_msg(self):
        self._msg_queue.put('`Баланс: {:>12}💰`\n`Размер ставки: {:>5}💰`'.format(self._money, self._bet))

    def end_race(self, result):
        if self.track:
            self.track = None
            self._money = db_wrap.get_money(self._user_id)
            if result['place']:
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}
                self._msg_queue.put('Поздравляю! Ваша ставка заняла {} место.\nВы заработали {}💰'.format(
                    medal[result['place']], result['won']))
            else:
                self._msg_queue.put('К сожалению, Ваша ставка проиграла.\nВы потеряли {}💰'.format(-result['won']))
                if self._money <= 100:
                    credit = 1000 - self._money
                    db_wrap.set_money(self._user_id, 1000)
                    self._msg_queue.put('Невероятнейшим образом Вам удалось спустить почти все ваши деньги на скачках.'
                                        '\nПриняв предложение распорядителя, от которого Вы не смогли отказаться, '
                                        'и проведя с ним бурную ночь, Вы получили от него {}💰.'
                                        '\n(Сложилось впечатление, что с Вами это не впервой.)'.format(credit))
                    self._money = db_wrap.get_money(self._user_id)
                if self._bet > self.max_bet:
                    self.set_bet(self.max_bet)

            self.send_status_msg()

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
        m_b = int(self._money * 0.1) #, self._money - 1000)
        if m_b < 10:
            return min(10, self._money)
        else:
            return m_b

    def set_bet(self, val):
        result_text = []

        if self._money > 100:
            max_bet = int(self._money * 0.1)
            if val > max_bet:
                self._bet = max_bet
                result_text.append('У Вас осталось всего {}💰.\n'
                                   'Ставка не может превышать 10% имеющейся суммы.\n'.format(self._money))
            elif val < 10:
                self._bet = 10
                result_text.append('Минимальная ставка 10💰.\n')
            else:
                self._bet = val
        elif self._money > 10:
            if val > 10:
                self._bet = 10
                result_text.append('У Вас осталось всего {}💰.\n'
                                   'Ваших денег хватит только на минимальную ставку 10.\n'.format(self._money))
            elif val < 10:
                self._bet = 10
                result_text.append('Минимальная ставка 10💰.\n')
            else:
                self._bet = val
        else:
            self._bet = self._money
            result_text.append('К сожалению, у Вас осталось всего: {}💰.\n'.format(self._money))

        result_text.append('Размер ставки установлен {}💰.'.format(self._bet))
        self._msg_queue.put(''.join(result_text))


    def get_msg(self):
        now = time.clock()
        if not self._msg_queue.empty() and (now - self._last_msg_utc) >= 1:
            self._last_msg_utc = now
            return self._msg_queue.get()
        else:
            return None

    def put_msg(self, msg):
        self._msg_queue.put(msg)

    def _get_menu(self):
        pass

    def _set_menu(self, val):
        pass

    menu = property(_get_menu, _set_menu)
