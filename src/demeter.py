""" Controls and logs environmental details from connected Arduino.
"""
import os
import serial 
from datetime import datetime
from dotenv import load_dotenv
from Adafruit_IO import Client
import redis
import time
import subprocess


BAUDRATE = 9600
PORT = '/dev/ttyACM0'

load_dotenv()
AIO_USER = os.getenv('AIO_USER')
AIO_PASS = os.getenv('AIO_PASS')

print(AIO_USER)
print(AIO_PASS)

class DemeterClient():

	ENV_UPDATE_FREQ = 60
	AIO_UPDATE_FREQ = 60

	R_HALT_KEY = "demeter_halt_immediately"
	R_ENV_UPDATED_KEY = "demeter_env_updated_at"
	R_AIO_UPDATED_KEY = "demeter_aio_updated_at"
	R_ARD_RESET_AT_KEY = "demeter_ard_reset_at"

	redis = None
	ser = None

	def setup_redis_keys(self):
		resetable_keys = [
			self.R_HALT_KEY,
			self.R_AIO_UPDATED_KEY,
			self.R_ENV_UPDATED_KEY,
			self.R_ARD_RESET_AT_KEY]

		for k in resetable_keys:
			self.redis.set(k, "0")

	def __init__(self, port, baud):
		self.port = port
		self.baud = baud
		self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
		self.setup_redis_keys()
		self.ser = serial.Serial(port=self.port, baudrate=self.baud, timeout=.1)
		self.aio = Client(AIO_USER, AIO_PASS)

	def handle_msg(self, msg):
		print("response:" + msg)

		msg_segments = msg.split(",")

		# Handle status code 4 (updating env data)
		if	msg_segments[0] == "4":
			self.redis.set(self.R_ENV_UPDATED_KEY, (datetime.now().timestamp()))

		# Handle status code 3 (returning env data)
		if	msg_segments[0] == "3":
			env_str = msg_segments[2]
			env_pairs = env_str.split("|")

			# Send datapoints to AIO.
			last_updated = datetime.fromtimestamp(float(self.redis.get(self.R_AIO_UPDATED_KEY)))
			if((datetime.now() - last_updated).seconds > self.AIO_UPDATE_FREQ):
				self.redis.set(self.R_AIO_UPDATED_KEY, (datetime.now().timestamp()))

				for kv_pair in env_pairs:
					# todo: try aio
					if kv_pair.startswith("tf"):
						tempf = int(kv_pair.split(":")[1])/10
						self.aio.send('temp', tempf)

					if kv_pair.startswith("ph"):
						ph = int(kv_pair.split(":")[1])/100
						self.aio.send('ph', ph)

					if kv_pair.startswith("tds"):
						tds = int(kv_pair.split(":")[1])
						self.aio.send('tds', tds)

					if kv_pair.startswith("wh"):
						wh = int(kv_pair.split(":")[1])
						self.aio.send('water-high', wh)

					if kv_pair.startswith("wl"):
						wl = int(kv_pair.split(":")[1])
						self.aio.send('water-low', wl)

	def run(self):
		while True:
			# Handle a halt request.
			to_halt = self.redis.get(self.R_HALT_KEY) == "1"
			if to_halt:
				self.redis.set(self.R_HALT_KEY, "0")
				raise Exception("Halt requested")

			# Fetch serial.
			try:
				message = self.read_serial()
				if message:
					pass
					#print(message)
			except Exception as error:
				print(error)

			# Process a valid message.
			if message.startswith("<") and message.endswith(">"):
				try:
					self.handle_msg(message[1:-1])
				except Exception as e:
					print(e)

			# Request update env data?
			last_updated = datetime.fromtimestamp(float(self.redis.get(self.R_ENV_UPDATED_KEY)))
			if((datetime.now() - last_updated).seconds > self.ENV_UPDATE_FREQ):
				print(datetime.now() - last_updated)
				print("Requesting environmental update.")
				self.write_serial("<3>")

			# Bounce Arduino if no update.
			ard_last_reset_at = datetime.fromtimestamp(float(self.redis.get(self.R_ARD_RESET_AT_KEY)))
			if((datetime.now() - last_updated).seconds > self.ENV_UPDATE_FREQ*2):
				if((datetime.now() - ard_last_reset_at).seconds > 60):
					try:
						self.aio.send('spam', 'Forcing hard reset...')
						self.redis.set(self.R_ARD_RESET_AT_KEY, (datetime.now().timestamp()))
						subprocess.run(["python3", "reset.py"])
					except Exception as err:
						pass

	def read_serial(self):
		return self.ser.readline().decode().strip()		

	def write_serial(self, str):
		self.ser.reset_output_buffer()
		value = str if str.endswith("\n") else str+"\n"
		self.ser.write(bytes(value, 'utf-8'))


demeter_client = DemeterClient(PORT, baud=BAUDRATE)
demeter_client.run()
