#!/usr/bin/env python3
"""Script to home the CNC machine. Written by the Cursor code writer.
Some comments by me"""

import sys
import os

# Add the src directory to the Python path so we can import liquid_cnc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from liquid_cnc import CNC_Controller, load_config


def main():
    """Home the CNC machine"""
    print("=== CNC Machine Homing Script ===")
    
    try:
        # Load configuration for 4040-PRO
        config = load_config("cnc_settings.yaml", 'Genmitsu 4040 PRO')
        print("Configuration loaded successfully!")
        
        # Connect to COM5
        # This is hardcoded for now but subject to change
        port = "COM14"
        print(f"Connecting to {port}...")
        
        controller = CNC_Controller(port, config)
        print(f"Connected to CNC on {port}")
        
        # Print coordinates before homing
        print("\n--- Coordinates Before Homing ---")

        # ok so this function reads the current coordinates
        coords = controller.read_coordinates()
        if coords:
            print(f"X: {coords['X']:.2f} mm")
            print(f"Y: {coords['Y']:.2f} mm")
            print(f"Z: {coords['Z']:.2f} mm")
        else:
            print("Could not read coordinates")
        
        # Home the machine
        print("\n--- Starting Homing Process ---")
        print("WARNING: Ensure tool is clear of workpiece!")
        input("Press Enter to continue with homing...")
        
        # built-in hime function, ok
        controller.home_xyz()
        print("Homing completed successfully!")
        
        # Print coordinates after homing
        print("\n--- Coordinates After Homing ---")
        coords = controller.read_coordinates()
        if coords:
            print(f"X: {coords['X']:.2f} mm")
            print(f"Y: {coords['Y']:.2f} mm")
            print(f"Z: {coords['Z']:.2f} mm")
        else:
            print("Could not read coordinates")
            
    except Exception as e:
        print(f"Error during homing: {e}")
    
    finally:
        print("\nHoming script finished.")


if __name__ == "__main__":
    main()
