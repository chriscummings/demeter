"""
	This script hard resets the Arduino by pulling its reset pin low. How you
	achieve this depends on the switching mechanism you're using from the RPi:
		- Logic Level Convertor
		- Transistor
		- etc.

	That's why this script takes everything as a parameter, to support any
	configuration.

    params:
		- gpio_reset_pin: any valid GPIO pin.
		- reset_direction: "high" or "low".
		- reset_interval: seconds to hold for.
"""

import os
import time
import RPi.GPIO as GPIO
from dotenv import load_dotenv

load_dotenv()

GPIO_RESET_PIN = int(os.getenv("GPIO_RESET_PIN"))
RESET_DIRECTION = os.getenv("RESET_DIRECTION")
RESET_INTERVAL_SEC = float(os.getenv("RESET_INTERVAL"))

if all([RESET_DIRECTION, GPIO_RESET_PIN, RESET_INTERVAL_SEC]):

	# Configure GPIO pins
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(GPIO_RESET_PIN, GPIO.OUT)

	# Bounce Arduino
	if RESET_DIRECTION == "high":
			GPIO.output(GPIO_RESET_PIN, GPIO.HIGH)
			time.sleep(RESET_INTERVAL_SEC)
			GPIO.output(GPIO_RESET_PIN, GPIO.LOW)
	else:
			GPIO.output(GPIO_RESET_PIN, GPIO.LOW)
			time.sleep(RESET_INTERVAL_SEC)
			GPIO.output(GPIO_RESET_PIN, GPIO.HIGH)

	print("OK")
