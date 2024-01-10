""" Controls and logs environmental details from connected Arduino.
"""
import os
import serial 
from datetime import datetime
from dotenv import load_dotenv
from Adafruit_IO import Client
#import redis

load_dotenv()
AIO_USER = os.getenv('AIO_USER')
AIO_PASS = os.getenv('AIO_PASS')

class Demeter():
	BAUDRATE = 9600
	PORT = '/dev/ttyACM0'
	USING_VIRTUAL_PORT = False
	DATA_FLAG = ">D:"
	UPDATE_ENVIRONMENT_CMD = "update_environment"

	# FIXME:
	aio = Client(AIO_USER, AIO_PASS)

	last_update_at = None
	last_ph = 0
	last_ph_at = datetime.min 
	last_tds = 0
	last_tds_at = datetime.min 
	last_tempf = 0
	last_tempf_at = datetime.min 
	last_water_low = 0
	last_water_high = 0
	last_water_high_at = datetime.min 
	last_water_low_at = datetime.min 

	def __init__(self):
		pass

	def log_report(self, report):
		print(report)
		value_pairs = report.replace(self.DATA_FLAG, "").replace("<","").split(",")

		for pair in value_pairs:
			if "f:" in pair:
				t = float(pair.split(":")[1])
				if t > 30 and t < 90:
					if t != self.last_tempf or ((now - self.last_tempf_at).total_seconds() / 60.0) > 2:
						self.last_tempf = t
						self.last_tempf_at = now
						self.aio.send('temp', t)

			if "t:" in pair:
				t = float(pair.split(":")[1])
				if t != self.last_tds or ((now - self.last_tds_at).total_seconds() / 60.0) > 2:
					self.last_tds = t
					self.last_tds_at = now
					self.aio.send('tds', t)

			if "p:" in pair:
				last_ph = pair.split(":")[1]
				p = float(pair.split(":")[1])
				if p > 0 and p < 14.1:
					if p != self.last_ph or ((now - self.last_ph_at).total_seconds() / 60.0) > 2:
						self.last_ph = p
						self.last_ph_at = now
						self.aio.send('ph', p)

			if "l:" in pair:
				l = pair.split(":")[1]
				if l != self.last_water_low or ((now - self.last_water_low_at).total_seconds() / 60.0) > 2:
					self.last_water_low = l
					self.last_water_low_at = now
					self.aio.send('water-low', l)

			if "h:" in pair:
				h = pair.split(":")[1]
				if h != self.last_water_high or ((now - self.last_water_high_at).total_seconds() / 60.0) > 2:
					self.last_water_high = h
					self.last_water_high_at = now
					self.aio.send('water-high', h)		


demeter = Demeter()
ser = serial.Serial(port=Demeter.PORT, baudrate=Demeter.BAUDRATE, timeout=.1)
if Demeter.USING_VIRTUAL_PORT:
	ser.rtscts = True # Set True for virtual ports.
	ser.dsrdtr = True # Set True for virtual ports.

def read():
	ser.reset_input_buffer()
	value = ser.readline().decode().strip()
	# if value:
	# 	print(str(int(datetime.now().timestamp()))+" * RX:"+value)
	return value

def write(str):
	value = str
	if not value.endswith("\n"):
		value = value+"\n"
	ser.reset_output_buffer()
	ser.write(bytes(value, 'utf-8'))

if __name__ == "__main__":
	while True:
		try:
			value =  read()
		except Exception as err:
			continue

		# If we're getting a ready or data msg
		if value.startswith(Demeter.DATA_FLAG) and value.endswith("<"):
			now = datetime.now()

			# If its never been updated or hasn't for N minutes, update environs.
			if not demeter.last_update_at or ((now - demeter.last_update_at).total_seconds() / 60.0) > .5:
				write(Demeter.UPDATE_ENVIRONMENT_CMD)
				demeter.last_update_at = now
				print("Environ Update Requested.")
			# Otherwise, process data.
			else:
				demeter.log_report(value)
