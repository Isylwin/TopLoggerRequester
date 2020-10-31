import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple, Optional

import requests

logger = logging.getLogger(__name__)


class Gym(Enum):
    _id: int
    _areas: Dict[str, int]

    MONK = (6, {'UP': 33, 'DOWN': 64})
    STERK = (20, {'BOULDER': 4, 'TRAIN': 69})

    def __init__(self, id_, areas):
        self._id = id_
        self._areas = areas

    @property
    def id(self):
        return self._id

    def get_area(self, name):
        value = self._areas.get(name.upper())
        if value is None:
            raise KeyError(f"{name} is not a valid area for {self.name}! Valid areas are: {self._areas.keys()}")
        return name, value


@dataclass
class TopLoggerRequest:
    gym_id: int
    area_id: int
    date: str
    url: str = "https://api.toplogger.nu/v1/gyms/{0}/slots"

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


@dataclass
class TopLogger:
    gym: Gym
    date: str
    time_slot: str
    spots: int
    area: Tuple[str, int]

    @property
    def gym_area(self):
        return f"({self.gym.name}:{self.area[0]})"

    def __call__(self) -> TopLoggerResult:
        try:
            request = TopLoggerRequest(self.gym.id, self.area[1], self.date)
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
        return f"TopLogger(gym={self.gym.name}, area={self.area[0]}, date='{self.date}', time_slot='{self.time_slot}', spots={self.spots})"

    @classmethod
    def from_json(cls, data):
        area_name = data['area'].upper()
        gym_name = data['gym'].upper()

        gym: Gym = Gym[gym_name]
        area = gym.get_area(area_name)

        result = cls(gym, data['date'], data['time_slot'], data['spots'], area)
        logger.info(f"{result}")
        return result
