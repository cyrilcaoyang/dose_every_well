#!/usr/bin/env python3
"""Demo script for liquid_cnc axis movement testing."""

import sys
import os
import time

# Add the src directory to the Python path so we can import liquid_cnc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from liquid_cnc.cnc_controller import CNC_Controller, load_config, find_port


def main():
    """Main demo function"""
    print("=== Liquid CNC Axis Movement Demo ===")
    
    try:
        # Load configuration and initialize controller
        config = load_config("cnc_settings.yaml", 'Genmitsu 4040 PRO')
        port = find_port()
        controller = CNC_Controller(port, config)
        print(f"CNC controller initialized on port: {port}")
        
        # Test different step values
        step_values = [10, 20, 50]
        step_size = 1.0  # 1mm per step
        
        print(f"\nTesting movement with step size: {step_size} mm")
        print("=" * 50)
        
        for steps in step_values:
            print(f"\n{'='*20} TESTING {steps} STEPS {'='*20}")
            
            # Test X-axis movement
            print(f"\n--- Moving X-axis by {steps} steps ({steps * step_size} mm) ---")
            print_coordinates(controller, "Before X movement")
            controller.move_to_point(steps * step_size, 0)
            controller.execute_movement()
            time.sleep(2)
            print_coordinates(controller, "After X movement")
            
            # Test Y-axis movement
            print(f"\n--- Moving Y-axis by {steps} steps ({steps * step_size} mm) ---")
            print_coordinates(controller, "Before Y movement")
            controller.move_to_point(0, steps * step_size)
            controller.execute_movement()
            time.sleep(2)
            print_coordinates(controller, "After Y movement")
            
            # Test Z-axis movement (be careful with Z!)
            print(f"\n--- Moving Z-axis by {steps} steps ({steps * step_size} mm) ---")
            print("WARNING: Z-axis movement - ensure tool is clear of workpiece!")
            input("Press Enter to continue with Z-axis movement...")
            
            print_coordinates(controller, "Before Z movement")
            controller.move_to_height(steps * step_size)
            controller.execute_movement()
            time.sleep(2)
            print_coordinates(controller, "After Z movement")
            
            print(f"\nCompleted testing with {steps} steps")
            print("-" * 50)
        
        print("\n=== Demo completed successfully! ===")
        print("Final coordinates:")
        print_coordinates(controller, "Final position")
        
    except Exception as e:
        print(f"Error during demo: {e}")
    
    finally:
        print("\nDemo finished. Exiting...")


def print_coordinates(controller, step_name=""):
    """Print current machine coordinates"""
    try:
        coords = controller.read_coordinates()
        if coords:
            print(f"{step_name} - Current coordinates: X={coords['X']:.2f}, Y={coords['Y']:.2f}, Z={coords['Z']:.2f}")
        else:
            print(f"{step_name} - Could not read coordinates")
    except Exception as e:
        print(f"{step_name} - Error reading coordinates: {e}")


if __name__ == "__main__":
    main()
