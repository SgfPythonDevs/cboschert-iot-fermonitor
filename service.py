#!/usr/bin/python
import argparse
from datetime import datetime
from time import sleep
from common import DbRepo, celsius_to_fahrenheit
import RPi.GPIO as GPIO
import dht11


def read():
    """Reads the current temperature and humidity from attached DHT11"""
    # The DHT11 library uses polling which can be unreliable. We retry up to 50 times
    # if needed to get a valid reason. Rarely takes this many time in my testing though.
    err_count = 0
    while err_count < 50:
        result = temp_sensor.read()

        # When we get a valid reading, return the time, temps, and humidity
        if result.is_valid():
            n = datetime.now()
            c = round(result.temperature, 1)
            f = round(celsius_to_fahrenheit(result.temperature), 1)
            h = round(result.humidity, 1)
            return n, c, f, h
        else:
            err_count += 1

    # Throw an exception if we didn't get a reading from the sensor
    raise Exception()


def run(location, poll_interval=60):
    """The application loop for the Fermonitor service. Runs infinitely until terminated, Ctrl+C on the Pi."""
    db = DbRepo()
    while True:
        try:
            # Get the next reading
            n, c, f, h = read()
        except Exception:
            print('oops')
            continue

        # Get the current state of the PST switch; 1 = on, 0 = off
        pst = GPIO.input(pst_pin)

        # Save it to the database log
        db.add_measurement(n, location, c, f, h, pst)
        print(c, f, h, pst)

        # Read the current target temperature from config in the DB
        target_c = db.get_target_temp()
        if target_c:  # If configured, maintain the target temperature
            if pst:  # Heater is on
                if c >= target_c + 1:  # heat to +1C to prevent frequent cycling
                    GPIO.output(pst_pin, False)
            else:  # heater is off
                if c < target_c:  # turn heater on when we drop below target temp
                    GPIO.output(pst_pin, True)
        else:  # no target temp is configured, ensure heater is off
            if GPIO.input(pst_pin):
                GPIO.output(pst_pin, False)
        
        # Sleep until the next interval
        sleep(poll_interval)


try:
    # initialize GPIO
    GPIO.setmode(GPIO.BCM)

    # control PowerSwitch Tail data using pin 7
    pst_pin = 7
    GPIO.setup(pst_pin, GPIO.OUT)
    GPIO.output(pst_pin, False)
    
    # read DHT11 data using pin 4
    temp_sensor = dht11.DHT11(pin=4)

    if __name__ == "__main__":
        # Parse command line arguments to get service settings
        parser = argparse.ArgumentParser(
            description="Starts the Monitoring Service",
            prog="service.py")
        parser.add_argument('location', help='The value stored in the where field of temperature log entries.')
        parser.add_argument('-i', '-interval', help='The number of seconds between temperature readings. DEFAULT %(default)s', type=int, default=60)

        args = parser.parse_args()
        print('Running {} with [{}]'.format(parser.prog, args))

        # Start the application loop
        run(args.location, args.i)
finally:
    # This will set all the GPIO pins we used back to inputs
    GPIO.output(pst_pin, False)
    GPIO.cleanup()
