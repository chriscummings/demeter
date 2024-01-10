""" Copies source code to Pi, compiles sketch, flashes Arduino.
"""

import os
import paramiko
from dotenv import load_dotenv

load_dotenv()
AIO_USER = os.getenv('AIO_USER')
AIO_PASS = os.getenv('AIO_PASS')

PI_IP = os.getenv('PI_IP')
PI_USER = os.getenv('PI_USER')
PI_PASS = os.getenv('PI_PASS')
PI_PORT = os.getenv('PI_PORT')

# ==============================================================================
# SSH params:
host = PI_IP
port = int(PI_PORT)
username = PI_USER
password = PI_PASS # input("SSH password?: ")
# Sketch params:
sketch_destination = "/home/chris/demeter"
sketch_files = [
	"demeter.ino",
	"demeter.h",
	"demeter.py",
	".env"
]
sketch_libraries = [
	"OneWire",
	"DallasTemperature",
	"Adafruit SSD1306"
]
arduino_port = "/dev/ttyACM0" # GPIO /dev/ttyS0
# Serial params:
baudrate = 9600
# ==============================================================================

paramiko.util.log_to_file("paramiko.log")

# SFTP
transport = paramiko.Transport((host, port))
transport.connect(None, username, password)
sftp = paramiko.SFTPClient.from_transport(transport)

# SSH
ssh = paramiko.client.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port=port, username=username, password=password)

# Ensure parent directory.
stdin, stdout, stderr = ssh.exec_command('mkdir ~/demeter')

# Upload sketch source files to RaspberryPi
for f in sketch_files:
	local_path = os.path.abspath(f)
	dest_path = os.path.join(sketch_destination, f)
	print(local_path,dest_path)
	sftp.put(local_path, dest_path)

# Install sketch libraries to Pi
	
stdin, stdout, stderr = ssh.exec_command('/home/chris/bin/arduino-cli lib list')
output = " ".join(stdout.readlines()) # Waits for command to finish
for l in sketch_libraries:
	print("Checking library: "+l)

	if l in output:
		print(l+" already installed.")
	else:
		print("Installing library: "+l)
		stdin, stdout, stderr = ssh.exec_command('/home/chris/bin/arduino-cli lib install "'+l+'"')
		stdout.channel.set_combine_stderr(True)
		output = stdout.readlines() # Waits for command to finish
		print(output)

# Compile sketch on Pi
for f in sketch_files:
	if "ino" in f:
		print("Compiling sketch "+f)
		stdin, stdout, stderr = ssh.exec_command('/home/chris/bin/arduino-cli compile -b arduino:avr:uno ./demeter')
		stdout.channel.set_combine_stderr(True)
		output = stdout.readlines() # Waits for command to finish
		print(output)

# Flash sketch onto Arduino
print("Flashing sketch to Arduino")
stdin, stdout, stderr = ssh.exec_command('/home/chris/bin/arduino-cli upload -b arduino:avr:uno -p '+arduino_port+' ~/demeter')
stdout.channel.set_combine_stderr(True)
output = stdout.readlines() # Waits for command to finish

print(output)

# Cleanup
if ssh:
	ssh.close()
	del ssh, stdin, stdout, stderr
if sftp: sftp.close()
if transport: transport.close()
