import random

import db_wrap
from config import *


class Racing:
    def __init__(self, tracks_cnt=TRACKS_NUM, race_len=RACE_LEN, race_width=RACE_WIDTH):
        self._tracks_cnt = tracks_cnt
        self._race_len = race_len
        self._race_width = race_width
        self._race_id = None
        self._finished = None
        self._started = None
        self._racers = None
        self._winners = None
        self._result = None

    def new_race(self, user_id=None):
        self._finished = False
        self._started = False
        self._racers = []
        self._winners = []
        self._result = None

        self._race_id = db_wrap.new_race(self._tracks_cnt, user_id)
        animals = db_wrap.get_animals(self._race_id)
        for track in range(self._tracks_cnt):
            self._racers.append({'animal': animals[track], 'position': 0})

    def set_bet(self, user_id, track, money):
        user_bal = db_wrap.get_money(user_id)
        return db_wrap.set_bet(user_id, self._race_id, track, min(user_bal, money))

    def run(self):
        if not self._race_id:
            raise ValueError('Init new race by new_race() first')

        if not self._started:
            self._started = True

        if not self._finished:
            # Сделать один ход
            rnd_num = random.sample(range(self._tracks_cnt), self._tracks_cnt)
            for racer_num in rnd_num:
                if self._racers[racer_num]['position'] == self._race_len:
                    break  # already finished
                rnd = random.randint(0, 100)
                if rnd < 20:
                    rnd = 0
                elif rnd < 50:
                    rnd = 2
                else:
                    rnd = 1
                self._racers[racer_num]['position'] += rnd
                if self._racers[racer_num]['position'] >= self._race_len and racer_num not in self._winners:
                    self._winners.append(racer_num)
                    self._racers[racer_num]['position'] = self._race_len
                if len(self._winners) >= 3:
                    # ФИНИШ
                    db_wrap.set_result(self._race_id, self._winners[0]+1, self._winners[1]+1, self._winners[2]+1)
                    self._result = db_wrap.get_bets_result(self._race_id)
                    self._finished = True
                    break
        return not self._finished

    @property
    def formatted_tracks(self):
        result_text = []
        for racer_num in range(self._tracks_cnt):
            position = self._racers[racer_num]['position']
            animal = self._racers[racer_num]['animal']
            if position < self._race_len:
                racer_row = '`🏁{}{}{}|{}️⃣`'.format(
                    '-' * (self._race_width - position), animal, '-' * position, racer_num + 1
                )
            else:
                if racer_num == self._winners[0]:
                    prize = '🏆'
                elif racer_num == self._winners[1]:
                    prize = '🥈'
                elif racer_num == self._winners[2]:
                    prize = '🥉'
                else:
                    prize = '🏁'
                racer_row = '`{}{}{}|{}️⃣`'.format(prize, animal, '-' * self._race_width, racer_num + 1)
            result_text.append(racer_row)

        return '\n'.join(result_text)

    @property
    def result(self):
        return self._result

    @property
    def finished(self):
        return self._finished

    @property
    def racers(self):
        return self._racers

    @property
    def tracks_cnt(self):
        return self._tracks_cnt

    @property
    def winners(self):
        if self._finished:
            return (self._racers[self._winners[0]]['animal'],
                    self._racers[self._winners[1]]['animal'],
                    self._racers[self._winners[2]]['animal'])
        else:
            return None

    @property
    def formatted_tracks_new(self):
        max_pos = max([racer['position'] for racer in self._racers])
        tracks_pos = max_pos - self._race_width//2
        max_tracks_pos = self._race_len - self._race_width
        tracks_pos = max(0, tracks_pos) and min(tracks_pos, max_tracks_pos)

        # result_text = []
        result_text = [': {}'.format(tracks_pos)]
        for racer_num in range(self._tracks_cnt):
            position = self._racers[racer_num]['position']
            animal = self._racers[racer_num]['animal']

            if position < (tracks_pos-2):
                racer_row = '{}'.format('-' * (self._race_width+3))
            else:
                racer_row = '{}{}{}'.format(
                    '-' * (self._race_width - (position - tracks_pos)), animal, '-' * (position - tracks_pos))

            if tracks_pos == max_tracks_pos:
                if racer_num in self._winners:
                    if racer_num == self._winners[0]:
                        prize = '🏆'
                    elif racer_num == self._winners[1]:
                        prize = '🥈'
                    elif racer_num == self._winners[2]:
                        prize = '🥉'
                else:
                    prize = '🏁'
                racer_row = '{}{}'.format(prize, racer_row)
            else:
                racer_row = '---{}'.format(racer_row)

            if tracks_pos == 0:
                racer_row = '{}|{}️⃣'.format(racer_row, racer_num + 1)
            else:
                racer_row = '{}----'.format(racer_row)
            result_text.append('`{}`'.format(racer_row))

        return '\n'.join(result_text)
