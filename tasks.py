import os
from invoke import task
from dotenv import load_dotenv
import paramiko
from glob import glob

# use `arduino-cli lib search <keyword>` to determine libary ids.
SKETCH_LIBRARIES = [
]

SOURCE_PATH = "src"
DOTENV_PATH = ".env"

# Load environment variables.
load_dotenv()

PI_USER = os.getenv("PI_USER")
PI_PASS = os.getenv("PI_PASS")
PI_PORT = int(os.getenv("PI_PORT"))
PI_IP = os.getenv("PI_IP")

HOME_PATH = os.getenv("HOME_PATH")
REMOTE_SRC_PATH = os.path.join(HOME_PATH, os.getenv("PROJECT_FOLDER"))
ARDUINO_CLI_PATH = os.path.join(HOME_PATH, "bin/arduino-cli")
VENV_PY3_PATH = os.path.join(REMOTE_SRC_PATH, "venv/bin/python3")
FLASH_SCRIPT_PATH = os.path.join(REMOTE_SRC_PATH, "flash.py")
HALT_SCRIPT_PATH = os.path.join(REMOTE_SRC_PATH, "halt.py")
RESET_SCRIPT_PATH = os.path.join(REMOTE_SRC_PATH, "reset.py")

@task
def halt(ctx):
	"""
	Halts a process.
	"""

	ssh, sftp = create_connections()

	stage_environment(ssh, sftp)

	print("\n* Halting Process *\n")
	_, stdout, _ = ssh.exec_command(f"{VENV_PY3_PATH} {HALT_SCRIPT_PATH}")
	stdout.channel.set_combine_stderr(True)
	output = "".join(stdout.readlines()) # Waits for command to finish
	print(output)


@task
def reset(ctx):
	"""
	Hard resets Arduino.
	"""

	GPIO_RESET_PIN = os.getenv("GPIO_RESET_PIN")
	RESET_DIRECTION = os.getenv("RESET_DIRECTION")
	RESET_INTERVAL = os.getenv("RESET_INTERVAL")

	ssh, sftp = create_connections()

	stage_environment(ssh, sftp)

	# Hard reset Arduino.
	print("\n* Reseting *\n")
	_, stdout, _ = ssh.exec_command(f"{VENV_PY3_PATH} {RESET_SCRIPT_PATH} {GPIO_RESET_PIN} {RESET_DIRECTION} {RESET_INTERVAL}")
	stdout.channel.set_combine_stderr(True)
	output = "\n".join(stdout.readlines()) # Waits for command to finish
	print(output)

@task
def deploy(ctx):
	"""
	Deploys source and reboots system.
	"""

	ssh, sftp = create_connections()

	stage_environment(ssh, sftp)

	# Copy source & config.
	print("\n* Source files *\n")

	for source_file in glob(os.path.join(SOURCE_PATH, "*")):
		local_path = os.path.join(source_file)
		dest_path = os.path.join(REMOTE_SRC_PATH, source_file.split("/")[-1])
		sftp.put(local_path, dest_path)
		print(f"Copied source file: {source_file}")

	# Install python dependencies
	print("\n* Python Dependencies *\n")
	_, stdout, _ = ssh.exec_command(os.path.join(REMOTE_SRC_PATH, "venv/bin/pip3")+" install -r "+os.path.join(REMOTE_SRC_PATH, "requirements.txt")) # FIXME:
	stdout.channel.set_combine_stderr(True)
	output = "".join(stdout.readlines()) # Waits for command to finish
	print(f"{output.strip()}")

	# Install sketch libraries to Pi.
	print("\n* Sketch Libraries *\n")
	_, stdout, _ = ssh.exec_command(f"{ARDUINO_CLI_PATH} lib list")
	stdout.channel.set_combine_stderr(True)
	output = "\n".join(stdout.readlines()) # Waits for command to finish
	for l in SKETCH_LIBRARIES:
		if l in output:
			print(f"{l} already installed.")
		else:
			print(f"Installing library: {l}")
			_, stdout, _ = ssh.exec_command(f"{ARDUINO_CLI_PATH} lib install '{l}'")
			stdout.channel.set_combine_stderr(True)
			output = "\n".join(stdout.readlines()) # Waits for command to finish
			print(output.strip())

	# Kill running py process that might prevent upload.
	print("\n* Halting Remote Processes *\n")
	_, stdout, _ = ssh.exec_command(f"{VENV_PY3_PATH} {HALT_SCRIPT_PATH}")
	stdout.channel.set_combine_stderr(True)
	output = "".join(stdout.readlines()) # Waits for command to finish
	print(output.strip())

	# Compile & flash.
	print("\n* Running Compile & Flash *\n")
	_, stdout, _ = ssh.exec_command(f"{VENV_PY3_PATH} {FLASH_SCRIPT_PATH} {REMOTE_SRC_PATH}")
	stdout.channel.set_combine_stderr(True)
	output = "".join(stdout.readlines()) # Waits for command to finish
	print(output)

def create_connections(ssh=True, sftp=True):
	"""
	Creates & returns a tuple of ssh & sftp connections.
	"""

	print("\n* Connections *\n")

	ssh_conn = None
	sftp_conn = None

	if sftp:
		# SFTP Connection.
		transport = paramiko.Transport((PI_IP, PI_PORT))
		transport.connect(None, PI_USER, PI_PASS)
		sftp_conn = paramiko.SFTPClient.from_transport(transport)
		print("SFTP connection created.")

	if ssh:
		# SSH Connection.
		ssh_conn = paramiko.client.SSHClient()
		ssh_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh_conn.connect(PI_IP, port=PI_PORT, username=PI_USER, password=PI_PASS)
		print("SSH connection created.")

	return (ssh_conn, sftp_conn)

def stage_environment(ssh, sftp):
	"""
	Checks for and sets up environment as needed.
	"""

	print("\n* Environment *\n")

	# Ensure project directory.
	_, stdout, _ = ssh.exec_command(f"mkdir {REMOTE_SRC_PATH}")
	stdout.channel.set_combine_stderr(True)
	output = " ".join(stdout.readlines()) # Waits for command to finish
	print("Project directory.")

	# Copy .env file over.
	sftp.put(DOTENV_PATH, os.path.join(REMOTE_SRC_PATH, ".env"))
	print(".env file.")

	# Virtual Environment.
	_, stdout, _ = ssh.exec_command(f"ls {REMOTE_SRC_PATH} | grep venv")
	stdout.channel.set_combine_stderr(True)
	output = " ".join(stdout.readlines()) # Waits for command to finish
	if "venv" not in output:
		print("Virtual environment not found. Creating...")
		_, stdout, _ = ssh.exec_command(f"python3 -m venv {os.path.join(REMOTE_SRC_PATH, 'venv')}")
		stdout.channel.set_combine_stderr(True)
		output = " ".join(stdout.readlines()) # Waits for command to finish
		print(output)
	else:
		print("Virtual environment found.")
