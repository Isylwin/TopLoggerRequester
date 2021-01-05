import argparse
import json
import logging
import random
import time
from json import JSONDecodeError
from pathlib import Path
from typing import List

from playsound import playsound
from plyer import notification

from toplogger import TopLogger
from pushsafer import init, Client

logger = logging.getLogger(__name__)


class Toaster:
    def __init__(self, audio_dir):
        self.audio_files = [x for x in audio_dir.glob("*.mp3")]

    def toast(self, message):
        notification.notify(title='Hallo, ik ben je computer', message=message, timeout=10)
        audio_file = random.choice(self.audio_files)
        if audio_file:
            playsound(str(audio_file))


def main(p_args):
    config_file = p_args.config
    delay = p_args.delay
    audio_dir = p_args.audio

    toaster = Toaster(audio_dir)

    ##Uncomment the following line and insert your private key!
    #init("<privatekey>")

    try:
        top_loggers: List[TopLogger] = json.load(config_file.open(), object_hook=TopLogger.from_json)

        while 1:
            for top_logger in top_loggers:
                result = top_logger()
                if result.error:
                    raise ValueError(result.message)
                if result.toastable:
                    toaster.toast(result.message)
                    Client("").send_message(result.message, "Free spot", "0", "0", "", "2", "", "", "0", "2", "60", "600", "1", "", "", "")
            time.sleep(delay)
    except JSONDecodeError as err:
        raise Exception(f"Simon je bent dom je bent de komma vergeten in '{config_file.resolve()}'!") from err


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--delay", type=int, default=240, help="Delay between requests.")
    parser.add_argument("-c", "--config", type=Path, default="config.json", help="The json file with your config")
    parser.add_argument("--audio", type=Path, default="audio", help="Glorious directory of amazing sound")
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                        datefmt="%Y-%m-%dT%H:%M:%S%z",
                        level=logging.INFO)
    args = parse_args()
    main(args)
