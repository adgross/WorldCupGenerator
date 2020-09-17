# -*- coding: utf-8 -*-

import random
import operator
from collections import Counter
from itertools import combinations
from data import GetRegions

class GenMethod:
    # definition of rules
    #   rules['mins'][region] => minimum number of teams from region
    #   rules['max'][region] => maximum number of teams from region
    #   rules['SeedersOn'] = true/false, seeders enabled

    def __init__(self, rules, countries, freezed):
        self.rules = rules
        self.countries = countries.copy()
        self.freezed = freezed

        self.region_slots = Counter()
        for r in GetRegions():
            self.region_slots[r] = self.rules['max'][r.id]

    def GetSelections(self, n, isSeeder=False):
        selections = []

        # we should not append the freezed countries now
        # only contabilize it so rules are safe
        for c in self.freezed:
            if c in self.countries:
                self.countries.remove(c)
                subCounter = {c.region: 1}
                self.region_slots.subtract(subCounter)

        n_countries_to_generate = range(n - len(selections))
        for i in n_countries_to_generate:
            if isSeeder:
                allowedCountries = [
                    c for c in self.countries
                    if self.region_slots[c.region] > 0 and c.seeder
                ]
            else:
                allowedCountries = [
                    c for c in self.countries
                    if self.region_slots[c.region] > 0
                ]

            pick = self._pickOne(allowedCountries)
            selections.append(pick)
            self.countries.remove(pick)

            # -1 slot for the country region
            subCounter = {pick.region: 1}
            self.region_slots.subtract(subCounter)

        random.shuffle(selections)
        return selections

    def _pickOne(self, countryList):
        pass

class SuperLeague(GenMethod):
    def __init__( self, rules, countries, freezed ):
        GenMethod.__init__(self, rules, countries, freezed)

        # iterate on constructor so is safe to call _pickOne
        self._doTheLeague()

    def _pickOne(self, countryList):
        return max(countryList, key=operator.attrgetter('points'))

    # there is no draw chance, win or lose
    def _doTheLeague(self):
        # here we create a new attribute inside the country object
        # create/reset 'points'
        for c in self.countries:
            c.points = 0

        matchs = combinations(self.countries, 2)
        for m in matchs:
            winner = self._getWinner(m[0], m[1])
            winner.points += 3

    def _getWinner(self, team1, team2):
        total = team1.win_chance + team2.win_chance
        r = random.uniform(0, total)
        if r <= team1.win_chance:
            return team1
        else:
            return team2

class AllRandom(GenMethod):
    def _pickOne(self, countryList):
        return random.choice(countryList)
