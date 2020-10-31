import logging
import random
from enum import Enum
from pathlib import Path
from typing import Dict

import requests
from playsound import playsound
from plyer import notification

logger = logging.getLogger(__name__)

URL = "https://api.toplogger.nu/v1/gyms/{0}/slots"


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
            raise KeyError(f"{name} is not a valid area for {self.name}! Valids = {self._areas.keys()}")
        return name, value

    def _missing_(cls, value):
        return cls.MONK


class TopLogger:
    def __init__(self, gym, date, time_slot, spots, reservation_area):
        self.gym = gym
        self.date = date
        self.time_slot = time_slot
        self.spots = spots
        self.reservation_area = reservation_area
        self.slim = True

    @classmethod
    def from_json(cls, data):
        area_name = data['area'].upper()
        gym_name = data['gym'].upper()

        gym: Gym = Gym[gym_name]
        area = gym.get_area(area_name)
        return cls(gym, data['date'], data['time_slot'], data['spots'], area)

    def make_request(self):
        params = {'date': self.date, 'reservation_area_id': self.reservation_area[1], 'slim': self.slim}

        url = URL.format(self.gym.id)
        r = requests.get(url=url, params=params)

        data = r.json()

        for entry in data:
            start_at = entry['start_at']
            if self.time_slot in start_at:
                spots_booked = entry['spots_booked']
                total_spots = entry['spots']
                return spots_booked, total_spots

        logger.error("Amaai zeg, dat kan niet, we zitten in de grote penarie!")
        logger.error("%s", self)
        return -1, -1  # TODO result object maken jij grote slet

    def make_toast(self):
        notification.notify(
            title='Hallo, ik ben je computer',
            message=f"Spots for {self.date} at {self.time_slot} : {self.spots}",
            app_icon=None,  # e.g. 'C:\\icon_32x32.ico'
            timeout=10,  # seconds
        )

        audio_dir = Path("audio")
        files = [x for x in audio_dir.glob("*.mp3")]
        audio_file = random.choice(files)

        # sound_idx = random.randint(0, 4)
        # audio_file = / f"nice_toast{sound_idx}.mp3"
        if audio_file:
            playsound(str(audio_file), block=False)

    def run(self):
        booked, all_spots = self.make_request()

        if booked == -1 and all_spots == -1:
            return False

        logger.info(
            f"Current status for ({self.gym.name}:{self.reservation_area[0]}) for {self.date} at {self.time_slot}: {booked}/{all_spots} spots booked")

        spots = all_spots - booked
        if spots >= self.spots:
            self.make_toast()

        return True

    def __repr__(self):
        return "Date: {0} | Time: {1} | Spots: {2}".format(self.date, self.time_slot, self.spots)
