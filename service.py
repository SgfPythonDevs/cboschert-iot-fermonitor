#!/usr/bin/python
import argparse
from datetime import datetime
from random import randint
from time import sleep
from common import DbRepo, farenheit_to_celcius

last_f, last_h = 720, 500


def read():
    global last_f, last_h

    last_f = randint(last_f - 30, last_f + 30)
    last_h = randint(last_h - 30, last_h + 30)

    if last_h > 1000:
        last_h = 1000

    if last_h < 0:
        last_h = 0

    f = last_f * 0.1

    return round(f, 1), round(farenheit_to_celcius(f),1), round(last_h * 0.1, 1)


def run(location, poll_interval=60):
    db = DbRepo()
    while True:
        f, c, h = read()
        db.add_temp(datetime.now(), location, c, f, h)
        print(c, f, h)
        sleep(poll_interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Starts the Monitoring Service",
        prog="service.py")
    parser.add_argument('location', help='The value stored in the where field of temperature log entries.')
    parser.add_argument('-i', '-interval', help='The number of seconds between temperature readings. DEFAULT %(default)s', type=int, default=60)

    args = parser.parse_args()
    print('Running {} with [{}]'.format(parser.prog, args))

    run(args.location, args.i)
