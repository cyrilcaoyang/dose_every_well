#!/usr/bin/env python3
"""
CNC Machine Movement Script
Moves the machine to specific X, Y, Z coordinates with proper G-code management.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from liquid_cnc import load_config, CNC_Controller
import time

def main():
    print("=== CNC Machine Movement Script ===")
    
    # Target coordinates
    target_x = 100
    target_y = 100
    
    target_z = -25  # Negative Z for downward movement
    
    print(f"Target coordinates: X={target_x}, Y={target_y}, Z={target_z}")
    
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
        if controller.is_homed():
            print("✅ Machine is homed and ready for movement")
        else:
            print("⚠ Machine may not be homed - homing recommended")
            response = input("Do you want to home the machine first? (y/n): ")
            if response.lower() in ['y', 'yes']:
                print("Homing machine...")
                controller.home_xyz()
                print("Homing completed")
        
        # Display current coordinates
        print("\n--- Current Coordinates Before Movement ---")
        coords = controller.read_coordinates()
        if coords:
            print(f"X: {coords['X']:.2f} mm")
            print(f"Y: {coords['Y']:.2f} mm")
            print(f"Z: {coords['Z']:.2f} mm")
        else:
            print("Could not read coordinates")
        
        # Safety prompt
        print(f"\n--- Moving to Target Position ---")
        print(f"Target: X={target_x}, Y={target_y}, Z={target_z}")
        print("WARNING: Ensure tool is clear of workpiece!")
        input("Press Enter to continue with movement...")
        
        print("Executing movement...")
        
        # Move X and Y together (XY plane)
        print("Moving X and Y axes...")
        controller.gcode = ""  # Clear any previous G-code
        controller.move_to_point(target_x, target_y)
        controller.execute_movement()
        print("XY movement completed")
        
        # Verify XY position before Z movement
        print("\n--- Verifying XY Position ---")
        coords = controller.read_coordinates()
        if coords:
            print(f"Current X: {coords['X']:.2f} mm (target: {target_x})")
            print(f"Current Y: {coords['Y']:.2f} mm (target: {target_y})")
            print(f"Current Z: {coords['Z']:.2f} mm")
        
        # Move Z to target height
        print("\nMoving Z axis...")
        controller.gcode = ""  # Clear previous G-code
        controller.move_to_height(target_z)
        controller.execute_movement()
        print("Z movement completed")
        
        # Wait for Z movement to fully complete before reading coordinates
        print("Waiting for Z movement to stabilize...")
        time.sleep(2)  # Give machine time to complete movement and report final position
        
        # Final coordinate verification
        print("\n--- Coordinates After Movement ---")
        coords = controller.read_coordinates()
        if coords:
            print(f"X: {coords['X']:.2f} mm")
            print(f"Y: {coords['Y']:.2f} mm")
            print(f"Z: {coords['Z']:.2f} mm")
            
            # Check if targets were reached
            x_diff = abs(coords['X'] - target_x)
            y_diff = abs(coords['Y'] - target_y)
            z_diff = abs(coords['Z'] - target_z)
            
            if x_diff > 1.0 or y_diff > 1.0 or z_diff > 1.0:
                print("⚠ Movement completed but target may not be fully reached")
                print(f"  X: target={target_x}, actual={coords['X']:.2f}")
                print(f"  Y: target={target_y}, actual={coords['Y']:.2f}")
                print(f"  Z: target={target_z}, actual={coords['Z']:.2f}")
                
                # Debug: Show raw machine response
                print("\n--- Debug: Raw Machine Response ---")
                try:
                    import serial
                    with serial.Serial(controller.SERIAL_PORT_PATH, controller.BAUD_RATE) as ser:
                        controller.wake_up(ser)
                        ser.reset_input_buffer()
                        ser.write(b"?\n")
                        time.sleep(0.2)
                        response = ser.read_all().decode().strip()
                        print(f"Raw response: {repr(response)}")
                        
                        if 'MPos:' in response:
                            mpos_start = response.find('MPos:') + 5
                            mpos_end = response.find('|', mpos_start)
                            if mpos_end == -1:
                                mpos_end = len(response)
                            mpos_section = response[mpos_start:mpos_end]
                            print(f"MPos section: {repr(mpos_section)}")
                except Exception as e:
                    print(f"Debug error: {e}")
            else:
                print("✅ All targets reached successfully!")
        else:
            print("Could not read final coordinates")
            
    except Exception as e:
        print(f"Error during movement: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nMovement script finished.")

if __name__ == "__main__":
    main()
