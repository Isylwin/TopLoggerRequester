import argparse
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List

from toplogger import TopLogger

logger = logging.getLogger(__name__)


def create_task(delay, top_logger):
    def wrapped():
        alive = True

        while alive:
            alive = top_logger.run()
            time.sleep(delay)

    return wrapped


def run_in_parallel(tasks):
    with ThreadPoolExecutor() as executor:
        running_tasks = [executor.submit(task) for task in tasks]
        for running_task in running_tasks:
            running_task.result()


def main(p_args):
    config_file = p_args.config

    try:
        data: List[TopLogger] = json.load(config_file.open(), object_hook=TopLogger.from_json)
    except Exception as err:
        raise RuntimeError(f"Simon je bent dom je bent de komma vergeten in '{config_file.resolve()}'!") from err

    delay = p_args.delay

    tasks = []

    for item in data:
        settings = f"Looking for {item.spots} spots ({item.gym.name}:{item.reservation_area[0]} for {item.date} at {item.time_slot})"
        logger.info(settings)
        task = create_task(delay, item)
        tasks.append(task)

    run_in_parallel(tasks)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--delay", type=int, default=240, help="Delay between requests.")
    parser.add_argument("-c", "--config", type=Path, default="config.json", help="The json file with your config")
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                        datefmt="%Y-%m-%dT%H:%M:%S%z",
                        level=logging.INFO)
    args = parse_args()
    main(args)
