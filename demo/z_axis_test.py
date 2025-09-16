#!/usr/bin/env python3
"""
Z-Axis Test Script
Tests Z-axis movement and checks machine configuration to diagnose Z-axis issues.
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from liquid_cnc import load_config, CNC_Controller

def test_z_movement(controller, target_z):
    """Test Z movement to a specific target"""
    print(f"\n--- Testing Z Movement to {target_z}mm ---")
    
    try:
        # Get current position
        coords = controller.read_coordinates()
        if coords:
            print(f"Current position: X={coords['X']:.2f}, Y={coords['Y']:.2f}, Z={coords['Z']:.2f}")
        
        # Try direct Z command
        import serial
        with serial.Serial(controller.SERIAL_PORT_PATH, controller.BAUD_RATE) as ser:
            controller.wake_up(ser)
            
            # Send Z movement command
            z_command = f"G0 Z{target_z}\n"
            print(f"Sending command: {repr(z_command)}")
            ser.write(str.encode(z_command))
            
            # Wait for movement
            print("Waiting for movement...")
            time.sleep(3)
            
            # Check status multiple times
            for i in range(5):
                ser.reset_input_buffer()
                ser.write(b"?\n")
                time.sleep(0.2)
                response = ser.readline().decode().strip()
                print(f"Status {i+1}: {repr(response)}")
                
                if 'MPos:' in response:
                    mpos_start = response.find('MPos:') + 5
                    mpos_end = response.find('|', mpos_start)
                    if mpos_end == -1:
                        mpos_end = len(response)
                    try:
                        coordinates = list(map(float, response[mpos_start:mpos_end].split(',')))
                        print(f"  Position: X={coordinates[0]:.2f}, Y={coordinates[1]:.2f}, Z={coordinates[2]:.2f}")
                    except (ValueError, IndexError):
                        pass
                
                if 'Alarm' in response:
                    print("  ⚠ ALARM STATE DETECTED!")
                elif 'Idle' in response:
                    print("  ✅ Machine is idle")
                elif 'Run' in response:
                    print("  🔄 Machine is running")
                    
    except Exception as e:
        print(f"Error during Z movement test: {e}")
        import traceback
        traceback.print_exc()

def check_machine_config(controller):
    """Check machine configuration settings"""
    print("\n--- Checking Machine Configuration ---")
    
    try:
        import serial
        with serial.Serial(controller.SERIAL_PORT_PATH, controller.BAUD_RATE) as ser:
            controller.wake_up(ser)
            
            # Check Z-axis specific settings
            z_settings = [
                ("$110", "Z-axis steps/mm"),
                ("$111", "Z-axis max rate"),
                ("$112", "Z-axis acceleration"),
                ("$132", "Z-axis max travel"),
            ]
            
            for command, description in z_settings:
                print(f"\n{description} ({command}):")
                ser.reset_input_buffer()
                ser.write(str.encode(command + "\n"))
                time.sleep(0.5)
                response = ser.read_all().decode().strip()
                if response:
                    print(f"  Response: {repr(response)}")
                else:
                    print("  No response")
            
            # Check all settings
            print(f"\nAll machine settings ($):")
            ser.reset_input_buffer()
            ser.write(b"$$\n")
            time.sleep(1)
            response = ser.read_all().decode().strip()
            if response:
                # Parse and show relevant Z-axis settings
                lines = response.split('\n')
                for line in lines:
                    if line.startswith('$110') or line.startswith('$111') or \
                       line.startswith('$112') or line.startswith('$132'):
                        print(f"  {line}")
            else:
                print("  No response")
                
    except Exception as e:
        print(f"Error checking machine config: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("=== Z-Axis Diagnostic Test ===")
    
    try:
        # Load configuration
        config = load_config("cnc_settings.yaml", 'Genmitsu 4040 PRO')
        print("Configuration loaded successfully!")
        
        # Connect to CNC
        port = "COM5"
        print(f"Connecting to {port}...")
        controller = CNC_Controller(port, config)
        print(f"Connected to CNC on {port}")
        
        # Check if machine is homed
        print("\n--- Machine Status Check ---")
        if not controller.is_homed():
            print("⚠ Machine not homed - homing first...")
            controller.home_xyz()
            print("Homing completed")
        else:
            print("✅ Machine is homed")
        
        # Check current position
        print("\n--- Current Position ---")
        coords = controller.read_coordinates()
        if coords:
            print(f"X: {coords['X']:.2f} mm")
            print(f"Y: {coords['Y']:.2f} mm")
            print(f"Z: {coords['Z']:.2f} mm")
        
        # Check machine configuration
        check_machine_config(controller)
        
        # Test Z movements with different targets
        z_targets = [-1, -5, -10, -15, -20, -25]
        
        print(f"\n--- Testing Z Movements ---")
        print("Testing Z targets:", z_targets)
        print("Press Enter to start Z-axis tests...")
        input()
        
        for target_z in z_targets:
            test_z_movement(controller, target_z)
            print(f"Z={target_z} test completed")
            
            # Ask if user wants to continue
            if target_z < max(z_targets):
                response = input(f"Continue to next test (Z={z_targets[z_targets.index(target_z)+1]})? (y/n): ")
                if response.lower() not in ['y', 'yes']:
                    break
        
        # Final position check
        print("\n--- Final Position Check ---")
        coords = controller.read_coordinates()
        if coords:
            print(f"Final X: {coords['X']:.2f} mm")
            print(f"Final Y: {coords['Y']:.2f} mm")
            print(f"Final Z: {coords['Z']:.2f} mm")
        
    except Exception as e:
        print(f"Error during Z-axis test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nZ-axis diagnostic test finished.")

if __name__ == "__main__":
    main()
