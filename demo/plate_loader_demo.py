#!/usr/bin/env python3
"""
Plate Loader Demo Script
Demonstrates the motorized well plate loading system.

Requirements:
- Raspberry Pi 5
- PCA9685 HAT
- 3x 5V Servo Motors connected to channels 3, 6, and 9

Installation:
    pip install -e ".[rpi]"
"""

import sys
import os
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from dose_every_well import PlateLoader
except ImportError as e:
    print("Error: PlateLoader requires Raspberry Pi libraries.")
    print("\nInstall with:")
    print("  pip install -e '.[rpi]'")
    print("\nOr manually:")
    print("  pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-motor")
    sys.exit(1)


def print_menu():
    """Display interactive menu"""
    print("\n" + "="*50)
    print("  PLATE LOADER CONTROL MENU")
    print("="*50)
    print("1. Calibrate servos")
    print("2. Raise plate")
    print("3. Lower plate")
    print("4. Open lid")
    print("5. Close lid")
    print("6. Full load sequence")
    print("7. Full unload sequence")
    print("8. Manual plate angle")
    print("9. Manual lid angle")
    print("0. Home (reset to default)")
    print("S. Show current positions")
    print("Q. Quit")
    print("="*50)


def main():
    """Interactive plate loader demo"""
    print("="*50)
    print("  Plate Loader Demo")
    print("="*50)
    print("\nInitializing plate loader...")
    
    try:
        # Initialize the plate loader
        loader = PlateLoader()
        
        print("✓ Plate loader initialized successfully!")
        print("\nServo Configuration:")
        print(f"  • Channels 3 & 6: Plate lift (synchronized)")
        print(f"  • Channel 9: Lid open/close")
        
        # Interactive loop
        while True:
            print_menu()
            choice = input("\nEnter choice: ").strip().upper()
            
            if choice == '1':
                print("\n→ Running calibration...")
                loader.calibrate()
                print("✓ Calibration complete")
            
            elif choice == '2':
                degrees = input("Enter degrees to raise (or press Enter for full): ").strip()
                if degrees:
                    loader.raise_plate(degrees=float(degrees), smooth=True)
                else:
                    loader.raise_plate(smooth=True)
                print("✓ Plate raised")
            
            elif choice == '3':
                degrees = input("Enter degrees to lower (or press Enter for full): ").strip()
                if degrees:
                    loader.lower_plate(degrees=float(degrees), smooth=True)
                else:
                    loader.lower_plate(smooth=True)
                print("✓ Plate lowered")
            
            elif choice == '4':
                print("\n→ Opening lid...")
                loader.open_lid(smooth=True)
                print("✓ Lid opened")
            
            elif choice == '5':
                print("\n→ Closing lid...")
                loader.close_lid(smooth=True)
                print("✓ Lid closed")
            
            elif choice == '6':
                print("\n→ Starting load sequence...")
                print("   1. Opening lid")
                print("   2. Raising plate")
                print("   3. Waiting for plate insertion")
                print("   4. Lowering plate")
                print("   5. Closing lid")
                loader.load_sequence()
                print("✓ Load sequence complete")
            
            elif choice == '7':
                print("\n→ Starting unload sequence...")
                print("   1. Opening lid")
                print("   2. Raising plate")
                print("   3. Waiting for plate removal")
                print("   4. Lowering plate")
                print("   5. Closing lid")
                loader.unload_sequence()
                print("✓ Unload sequence complete")
            
            elif choice == '8':
                angle = input("Enter plate angle (0-90): ").strip()
                if angle:
                    loader.move_plate_to(float(angle), smooth=True)
                    print(f"✓ Plate moved to {angle}°")
            
            elif choice == '9':
                angle = input("Enter lid angle (0-90): ").strip()
                if angle:
                    loader.rotate_lid(float(angle), smooth=True)
                    print(f"✓ Lid rotated to {angle}°")
            
            elif choice == '0':
                print("\n→ Homing all servos...")
                loader.home()
                print("✓ All servos at home position")
            
            elif choice == 'S':
                plate_pos, lid_pos = loader.get_positions()
                print(f"\nCurrent Positions:")
                print(f"  • Plate: {plate_pos}°")
                print(f"  • Lid: {lid_pos}°")
            
            elif choice == 'Q':
                print("\n→ Shutting down...")
                break
            
            else:
                print("✗ Invalid choice. Please try again.")
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'loader' in locals():
            print("\n→ Shutting down plate loader...")
            loader.shutdown()
            print("✓ Shutdown complete")
        
        print("\nDemo finished. Goodbye!")


if __name__ == "__main__":
    main()

