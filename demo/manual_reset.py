import serial
import time

print("Manual CNC reset...")
try:
    with serial.Serial('COM14', 115200, timeout=2) as ser:
        print("Connected to COM14")
        ser.write(b'\x18')  # Ctrl+X reset
        time.sleep(3)
        ser.write(b'?\n')   # Status query
        time.sleep(1)
        if ser.in_waiting > 0:
            response = ser.read_all().decode('utf-8', errors='ignore')
            print(f"Response: {response}")
        else:
            print("No response - try power cycling CNC")
except Exception as e:
    print(f"Error: {e}")
