#!/usr/bin/env python3
"""Simple demo to connect to 4040-PRO on COM5 and print XYZ coordinates."""
import serial.tools.list_ports
import sys
import os
import time

# Add the src directory to the Python path so we can import liquid_cnc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from liquid_cnc import CNC_Controller, load_config


def main():
    """Connect to 4040-PRO on COM5 and print coordinates"""
    print("=== Simple 4040-PRO Connection Demo ===")
    
    try:
        # Load configuration and initialize controller
        config = load_config("cnc_settings.yaml", 'Genmitsu 4040 PRO')
        port = find_port()
        controller = CNC_Controller(port, config)
        print(f"CNC controller initialized on port: {port}")
        
        
        
        # Load configuration for 4040-PRO
        config = load_config("cnc_settings.yaml", 'Genmitsu 4040 PRO')
        print("Configuration loaded successfully!")
        
        # # Connect directly to COM5
        # port = "COM5"
        # print(f"Connecting to {port}...")
        
        # controller = CNC_Controller(port, config)
        # print(f"Connected to CNC on {port}")
        
        # Print current coordinates
        print("\n--- Current Machine Coordinates ---")
        coords = controller.read_coordinates()
        if coords:
            print(f"X: {coords['X']:.2f} mm")
            print(f"Y: {coords['Y']:.2f} mm")
            print(f"Z: {coords['Z']:.2f} mm")
        else:
            print("Could not read coordinates")
            
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        print("\nDemo finished.")

def find_port():
    # Get list of available serial ports
    ports = serial.tools.list_ports.comports()

    if not ports:
        raise Exception("No serial ports found! Check your connection.")

    if len(ports) == 1:
        print(f"Automatically selected only available port: {ports[0].device}")
        return ports[0].device

    # If multiple ports found, try to identify the CNC
    print("Found multiple ports. Attempting to detect CNC...")
    for port in ports:
        try:
            # Try to communicate with CNC
            with serial.Serial(port.device, baudrate=115200, timeout=0.5) as ser:
                ser.write(b"\r\n\r\n")  # Wake up command
                time.sleep(1)
                ser.write(b"$$\n")  # Request settings (common CNC command)
                response = ser.read_all().decode()

                if 'ok' in response.lower() or 'grbl' in response.lower():
                    print(f"CNC detected on port: {port.device}")
                    return port.device
        except Exception as e:
            continue

    raise Exception("Could not automatically detect CNC port. Please check connections.")




if __name__ == "__main__":
    main()
