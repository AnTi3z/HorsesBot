import db_wrap
from functools import partial


class User:

    def __init__(self, user_id):
        self._user_id = user_id
        self.track = None
        self._menu = None

        self._money = db_wrap.get_money(self._user_id)
        self._bet = db_wrap.get_last_bet(self._user_id) or 10


    def status_msg(self):
        return '`Баланс: {:>12}💰`\n`Размер ставки: {:>5}💰`'.format(self._money, self._bet)

    def end_race(self, result):
        if self.track:
            if result['place']:
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}
                result_text = 'Поздравляю! Ваша ставка заняла {} место.\nВы заработали {}💰'.format(
                    medal[result['place']], result['won'])
            else:
                result_text = 'К сожалению, Ваша ставка проиграла.\nВы потеряли {}💰'.format(-result['won'])
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

        return ''.join(result_text)


    def _get_menu(self):
        pass

    def _set_menu(self, val):
        pass

    menu = property(_get_menu, _set_menu)
