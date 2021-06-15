import logging
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.toplogger.nu/v1/"


@dataclass
class Area:
    id: int
    name: str

    def soft_match(self, name: str) -> bool:
        return name.casefold() in self.name.casefold()

    def hard_match(self, name: str) -> bool:
        return name.casefold() == self.name.casefold()

    def __str__(self):
        return f"{self.name}"


@dataclass
class Gym:
    id: int
    id_name: str
    slug: str
    name: str
    short_name: str

    def soft_match(self, name: str) -> bool:
        return any([name.casefold() in x.casefold() for x in [self.id_name, self.slug, self.name, self.short_name]])

    def hard_match(self, name: str) -> bool:
        return any([name.casefold() == x.casefold() for x in [self.id_name, self.slug, self.name, self.short_name]])


@dataclass
class TopLoggerRequest:
    gym_id: int
    area_id: int
    date: str
    url: str = BASE_URL + "gyms/{0}/slots"

    def __call__(self, time_slot) -> Optional[Tuple[int, int]]:
        params = {'date': self.date, 'reservation_area_id': self.area_id, 'slim': True}

        url = self.url.format(self.gym_id)
        r = requests.get(url=url, params=params)

        data = r.json()

        for entry in data:
            start_at = entry['start_at']
            if time_slot in start_at:
                spots_booked = entry['spots_booked']
                total_spots = entry['spots']
                return spots_booked, total_spots

        raise ValueError(f"No time slot that starts at '{time_slot}'")


class TopLoggerResultEnum(Enum):
    ERROR = -1
    FULL = 0
    PLEKKKKKIIE = 1


@dataclass
class TopLoggerResult:
    homo: TopLoggerResultEnum
    message: str

    @property
    def toastable(self):
        return self.homo == TopLoggerResultEnum.PLEKKKKKIIE

    @property
    def error(self):
        return self.homo == TopLoggerResultEnum.ERROR


class GymResolver:
    Gyms_url: str = BASE_URL + "gyms/"
    Areas_url: str = Gyms_url + "{0}/reservation_areas"

    @staticmethod
    def find_match(data, name):
        matches = [x for x in data if x.hard_match(name)]
        if not matches:
            matches = [x for x in data if x.soft_match(name)]
        return matches

    @staticmethod
    def resolve(gym_name: str, area_name: str) -> Tuple[Gym, Area]:
        gyms_data = requests.get(GymResolver.Gyms_url).json()

        gyms = [Gym(x['id'], x['id_name'], x['slug'], x['name'], x['name_short']) for x in gyms_data]
        matches = GymResolver.find_match(gyms, gym_name)

        if not matches:
            raise KeyError(f"'{gym_name}' cannot be found!")
        elif len(matches) > 1:
            raise KeyError(f"Multiple matches found for: '{gym_name}'! {matches}")

        gym = matches.pop()

        areas_data = requests.get(GymResolver.Areas_url.format(gym.id)).json()
        areas = [Area(x['id'], x['name']) for x in areas_data]
        area_matches = GymResolver.find_match(areas, area_name)

        if not area_matches:
            raise KeyError(f"'{area_name}' is not a valid area for {gym.short_name}!"
                           f" Valid areas: {[str(x) for x in areas]}")
        elif len(area_matches) > 1:
            raise KeyError(f"Multiple matches found for: '{area_name}'! {area_matches}")

        area = area_matches.pop()
        return gym, area


@dataclass
class TopLogger:
    gym: Gym
    date: str
    time_slot: str
    spots: int
    area: Area

    @property
    def gym_area(self):
        return f"({self.gym.name}:{self.area.name})"

    def __call__(self) -> TopLoggerResult:
        try:
            request = TopLoggerRequest(self.gym.id, self.area.id, self.date)
            booked, all_spots = request(self.time_slot)
        except ValueError as err:
            message = f"{self!r} is invalid -> {err}"
            logger.error(message)
            return TopLoggerResult(TopLoggerResultEnum.ERROR, message)

        spots = all_spots - booked
        if spots >= self.spots:
            message = f"Free spots for {self.gym_area} {self.date} at {self.time_slot} : {spots}"
            logger.info(message)
            return TopLoggerResult(TopLoggerResultEnum.PLEKKKKKIIE, message)

        message = f"Status for {self.gym_area} for {self.date} at {self.time_slot} : {booked}/{all_spots} booked"
        logger.info(message)
        return TopLoggerResult(TopLoggerResultEnum.FULL, message)

    def __str__(self):
        return f"Looking for {self.spots} spots ({self.gym_area} for {self.date} at {self.time_slot})"

    def __repr__(self):
        return f"TopLogger(gym={self.gym.name}, area={self.area.name}, date='{self.date}'" \
               f", time_slot='{self.time_slot}', spots={self.spots})"

    @classmethod
    def from_json(cls, data):
        area_name = data['area']
        gym_name = data['gym']

        gym, area = GymResolver.resolve(gym_name, area_name)

        result = cls(gym, data['date'], data['time_slot'], data['spots'], area)
        logger.info(f"{result}")
        return result
