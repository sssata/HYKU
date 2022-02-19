import serial
import subprocess

port = serial.Serial()

port.port = "COM13"

port.baudrate = 1200

port.open()
port.close()
port.open()
port.close()

subprocess.call()