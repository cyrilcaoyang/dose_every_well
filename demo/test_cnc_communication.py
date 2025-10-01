#!/usr/bin/env python3
"""
Test CNC communication to diagnose connection issues
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import serial
import time

def test_cnc_communication():
    print("=== CNC Communication Test ===")
    
    try:
        print("1. Opening serial connection to COM14...")
        ser = serial.Serial('COM14', 115200, timeout=5)
        print(f"   ✓ Connected: {ser.is_open}")
        
        # Wait for any startup messages
        time.sleep(2)
        
        print("2. Checking for any incoming data...")
        if ser.in_waiting > 0:
            data = ser.read_all().decode('utf-8', errors='ignore')
            print(f"   Received: {repr(data)}")
        else:
            print("   No incoming data")
        
        print("3. Sending status query (?)...")
        ser.write(b'?\n')
        time.sleep(1)
        
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"   ✓ Response: {response}")
        else:
            print("   ✗ No response to status query")
        
        print("4. Sending soft reset (Ctrl+X)...")
        ser.write(b'\x18')
        time.sleep(3)
        
        # Clear any reset messages
        if ser.in_waiting > 0:
            data = ser.read_all().decode('utf-8', errors='ignore')
            print(f"   Reset response: {repr(data)}")
        
        print("5. Testing status query after reset...")
        ser.write(b'?\n')
        time.sleep(1)
        
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"   ✓ Response after reset: {response}")
            print("   CNC communication is working!")
        else:
            print("   ✗ Still no response after reset")
            print("   CNC may need power cycle")
        
        ser.close()
        
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print("Check:")
        print("- CNC is powered on")
        print("- USB cable is connected")
        print("- No other programs using COM14")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_cnc_communication()
