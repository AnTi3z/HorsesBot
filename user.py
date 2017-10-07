import db_wrap
from functools import partial


class User:
    # msg_callback = None

    def __init__(self, user_id):
        # if not self.__class__.msg_callback:
        #    raise AttributeError('You should initialize msg_callback class attribute first.')
        self._user_id = user_id
        self._bet = None
        self.track = None
        self._menu = None
        self._money = None
        # self._msg_callback = partial(self.__class__.msg_callback, user_id)

        self._get_user_data()

    def _get_user_data(self):
        self._money = db_wrap.get_money(self._user_id)
        self._set_bet(db_wrap.get_last_bet(self._user_id) or 10)

    def status_msg(self):
        self._msg_callback('')
        return 'Баланс: {:>5}'.format(self._money)

    def end_race(self, result):
        if self._track:
            if result['place']:
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}
                # self._msg_callback('Поздравляю!')
                result_text = 'Поздравляю!'.format()
            else:
                # self._msg_callback(
                result_text = 'К сожалению, Ваша ставка проиграла.\n'\
                              'Вы потеряли {}💰'.format(-result['won'])
        self.track = None
        self._money = db_wrap.get_money(self._user_id)
        return result_text

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

    def set_bet(self, val):
        result_text = []
        if self._money > 100:
            max_bet = int(self._money * 0.1)
            if val > max_bet:
                self._bet = max_bet
                result_text.append('Ставка не может превышать 10% имеющейся суммы.\n')
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
            result_text.append('К сожалению, у Вас осталось всего: {}💰.')

        result_text.append('Размер ставки установлен {}💰'.format(self._bet))

        # self._msg_callback(''.join(result_text))
        return result_text

    # bet_size = property(_get_bet, _set_bet)

    def _get_menu(self):
        pass

    def _set_menu(self, val):
        pass

    menu = property(_get_menu, _set_menu)
