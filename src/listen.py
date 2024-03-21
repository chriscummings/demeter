"""
	This script listens to the serial port for testing.
"""

import os
import serial
from dotenv import load_dotenv

load_dotenv()

BAUDRATE = int(os.getenv("BAUDRATE"))
ARDUINO_PORT = os.getenv("ARDUINO_PORT")

ser = serial.Serial(port=ARDUINO_PORT, baudrate=BAUDRATE, timeout=.1)

while True:
	try:
		message = ser.readline().decode().strip()
		if message:
			print(message)
	except Exception as error:
		print(error)
