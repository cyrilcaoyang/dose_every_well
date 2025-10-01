import serial
import time

def connect_and_send_command():
    """
    Simple demo to connect to Arduino on COM10 and send 'run' command
    """
    arduino = None
    try:
        # Connect to Arduino on COM10 with 9600 baud rate
        print("Connecting to Arduino on COM10...")
        arduino = serial.Serial('COM10', 9600, timeout=2)
        
        # Wait for Arduino to initialize
        time.sleep(2)
        print("Connected successfully!")
        
        # Send the "run" command
        command = "run"
        print(f"Sending command: '{command}'")
        arduino.write(command.encode('utf-8'))
        
        # Wait a moment for response
        time.sleep(1)
        
        # Read any response from Arduino
        if arduino.in_waiting > 0:
            response = arduino.readline().decode('utf-8').strip()
            print(f"Arduino response: '{response}'")
        else:
            print("No response received from Arduino")
                
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")
        print("Make sure:")
        print("- Arduino is connected to COM10")
        print("- Arduino is not being used by another program - this includes the Arduino IDE")
        print("- Correct baud rate (9600)")
    except Exception as e:
        print(f"Unexpected error: {e}")

        
    finally:
        # Always close the connection if it was opened
        if arduino and arduino.is_open:
            arduino.close()
            print("Serial connection closed")

if __name__ == "__main__":
    connect_and_send_command()
