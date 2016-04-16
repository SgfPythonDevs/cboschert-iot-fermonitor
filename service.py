#!/usr/bin/python
import argparse
from datetime import datetime
from time import sleep
from common import DbRepo, celcius_to_farenheit
import RPi.GPIO as GPIO
import dht11

# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

# read data using pin 4
instance = dht11.DHT11(pin = 4)


def read():
    err_count = 0
    while err_count < 50:
        result = instance.read()
	if result.is_valid():
            err_count = 0
            n = datetime.now()
            c = round(result.temperature, 1)
            f = round(celcius_to_farenheit(result.temperature), 1)
            h = round(result.humidity, 1)
            return n, c, f, h
	else:  		
            err_count += 1

    raise Exception()


def run(location, poll_interval=60):
    db = DbRepo()
    while True:
        try:
            n, c, f, h = read()
        except Exception:
            print('oops')
            continue
        
        db.add_temp(n, location, c, f, h)
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
