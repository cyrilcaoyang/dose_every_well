import serial
import time

ser = serial.Serial ('COM4', 9600, timeout = 1)
time.sleep(2)  # wait for the serial connection to initialize

print ("Choose a command: 'Open', 'Close', 'Grasp', 'Set (angle)'")

while True:
        cmd = input("> ").strip()
        ser.write((cmd + "\n").encode())
        print(ser.readline().decode().strip())