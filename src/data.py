# -*- coding: utf-8 -*-

import attr
from attr.validators import instance_of


@attr.s(frozen=True)
class Region:
    id = attr.ib()
    name = attr.ib()


@attr.s(eq=False)
class Country:
    name = attr.ib()
    region = attr.ib(validator=instance_of(Region))
    seeder = attr.ib(default=False)
    win_chance = attr.ib(default=50)

    def exportAsJSONObject(self):
        return {
            'name': self.name,
            'region': self.region.id,
            'seeder': self.seeder,
            'win_chance': self.win_chance
        }


_REGIONS = [['AFC', _("Asia")],
            ['CAF', _("Africa")],
            ['CONCACAF', _("North and Central America")],
            ['CONMEBOL', _("South America")],
            ['OFC', _("Oceania")],
            ['UEFA', _("Europe")]]

_REGIONS_OBJECTS = [Region(id, name) for id, name in _REGIONS]


def GetRegions():
    return _REGIONS_OBJECTS

def GetRegionById(id):
    for r in _REGIONS_OBJECTS:
        if id == r.id:
            return r
    return None
