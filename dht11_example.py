import RPi.GPIO as GPIO
import dht11
import time
import datetime

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
			return result
		else:  		
			err_count += 1
	
	raise "Err"

try:
	for x in range(0,10):
		result = read()
		print("Last valid input: " + str(datetime.datetime.now()))
		print("Temperature: %d C" % result.temperature)
		print("Humidity: %d %%" % result.humidity)

finally:
	GPIO.cleanup(4)
