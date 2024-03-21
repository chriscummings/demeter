"""
	This script compiles a sketch and flashes the Arduino.
"""

import os
import subprocess
from glob import glob
from dotenv import load_dotenv


load_dotenv()

# Paths
HOME_PATH = os.getenv("HOME_PATH")
PROJECT_FOLDER = os.getenv("PROJECT_FOLDER")
PROJECT_PATH = os.path.join(HOME_PATH, PROJECT_FOLDER)
VENV_PY3_PATH = os.path.join(HOME_PATH, PROJECT_FOLDER, "venv/bin/python3")
ARDUINO_CLI_PATH = os.path.join(HOME_PATH, "bin/arduino-cli")
AVRDUDE_PATH = os.path.join(HOME_PATH, ".arduino15/packages/arduino/tools/avrdude/6.3.0-arduino17/bin/avrdude")
SKETCHES_PATH = "/tmp/arduino/sketches/*/*"
# Avrdude Flash
BOARD_DESIGNATION = os.getenv("BOARD")
RPI_PORT = os.getenv("ARDUINO_PORT")
AVRDUDE_CONF_PATH = os.path.join(HOME_PATH, "avrdude.conf")
PART_NO = os.getenv("PART_NO")
PROGRAMMER_ID = os.getenv("PROGRAMMER_ID")

# Delete old compiled sketches
subprocess.run(["rm", "-rf", SKETCHES_PATH])

# Find sketch .ino
ino_file = glob(os.path.join(PROJECT_PATH, "*.ino"))[0]
if not ino_file:
	raise Exception(f"No .ino file found in {PROJECT_PATH}")

# Compile sketch to hex
# https://arduino.github.io/arduino-cli/0.35/
subprocess.run([ARDUINO_CLI_PATH, "compile", "-b", BOARD_DESIGNATION, ino_file])

print("\nCompilation done!")

# Locate hex file
hex_loc = None

for f in glob(SKETCHES_PATH):
	if ".hex" in f and not "bootloader" in f:
		hex_loc=f

if not hex_loc:
	raise Exception("Missing hex file.")

# Flash Arduino.
# https://avrdude.readthedocs.io/en/latest/2-Command_Line_Options.html
result = subprocess.run(
	[
		AVRDUDE_PATH,
		"-c", PROGRAMMER_ID,
		"-p", PART_NO,
		"-C", AVRDUDE_CONF_PATH,
		"-U", f"flash:w:{hex_loc}",
		"-P", RPI_PORT
	],
	capture_output=True,
	text=True)

print(result.stderr.strip())
print(result.stdout.strip())

print("OK")
