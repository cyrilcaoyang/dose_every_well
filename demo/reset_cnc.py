#!/usr/bin/env python3
"""
Quick CNC reset script to clear any stuck states
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from liquid_cnc import load_config, CNC_Controller
import time

def reset_cnc():
    try:
        config = load_config("cnc_settings.yaml", 'Genmitsu 4040 PRO')
        controller = CNC_Controller("COM14", config)
        print("Connected to CNC")
        
        # Send GRBL soft reset (Ctrl+X)
        print("Sending GRBL soft reset...")
        import serial
        with serial.Serial("COM14", 115200, timeout=2) as ser:
            ser.write(b'\x18')  # Ctrl+X soft reset
            time.sleep(2)
            ser.reset_input_buffer()
            print("Reset sent")
        
        time.sleep(3)
        
        # Try to reconnect and check status
        print("Reconnecting...")
        controller = CNC_Controller("COM14", config)
        coords = controller.read_coordinates()
        if coords:
            print(f"CNC is responsive: X={coords['X']:.2f}, Y={coords['Y']:.2f}, Z={coords['Z']:.2f}")
            print("CNC reset successful!")
        else:
            print("CNC not responding to status query")
            
    except Exception as e:
        print(f"Reset failed: {e}")
        print("\nTry these manual steps:")
        print("1. Power cycle the CNC machine (unplug for 10 seconds)")
        print("2. Disconnect and reconnect USB cable")
        print("3. Close any other programs using COM14")

if __name__ == "__main__":
    reset_cnc()
