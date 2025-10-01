#!/usr/bin/env python3
"""Simple demo to connect to 4040-PRO and print XYZ coordinates."""

import sys
import os

# Add the src directory to the Python path so we can import dose_every_well
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dose_every_well import CNC_Controller, load_config, find_port


def main():
    """Connect to 4040-PRO and print coordinates"""
    print("=== Simple 4040-PRO Connection Demo ===")
    
    try:
        # Load configuration for 4040-PRO
        config = load_config("cnc_settings.yaml", 'Genmitsu 4040 PRO')
        print("Configuration loaded successfully!")
        
        # Auto-detect CNC port (works on Windows, Linux, macOS)
        port = find_port()
        print(f"Connecting to {port}...")
        
        controller = CNC_Controller(port, config)
        print(f"Connected to CNC on {port}")
        
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


if __name__ == "__main__":
    main()
