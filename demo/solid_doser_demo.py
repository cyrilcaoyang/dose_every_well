#!/usr/bin/env python3
"""
Solid Doser Demo Script
Demonstrates the solid dosing mechanism control with power-safe operation.

Hardware Requirements:
- Raspberry Pi 5
- Waveshare PCA9685 HAT (I2C default address 0x40)
- 1x Servo for gate control (connected to Channel 0 on HAT)
- 1x 5V Relay Module (GPIO 17, Physical Pin 11)
- 1x DC motor (connected via relay)
- 5V 5A power supply (single plug powers everything)

Usage:
    python3 solid_doser_demo.py
"""

import sys
import time
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dose_every_well import SolidDoser


def demo_basic_controls(doser: SolidDoser):
    """Demonstrate basic gate and motor controls"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Gate and Motor Controls")
    print("="*60)
    
    print("\n1. Testing gate movements...")
    print("   - Closing gate...")
    doser.close_gate()
    
    print("   - Opening gate fully...")
    doser.open_gate()
    
    print("   - Setting gate to 45° (half open)...")
    doser.set_gate_angle(45)
    
    print("   - Closing gate...")
    doser.close_gate()
    
    print("\n2. Testing motor control...")
    print("   - Starting motor...")
    doser.motor_on()
    time.sleep(2)
    
    print("   - Stopping motor...")
    doser.motor_off()
    
    status = doser.get_status()
    print(f"\n   Current Status: {status}")


def demo_dispense_sequences(doser: SolidDoser):
    """Demonstrate automated dispense sequences"""
    print("\n" + "="*60)
    print("DEMO 2: Automated Dispense Sequences")
    print("="*60)
    
    print("\n1. Small dose (2 seconds, full gate opening)...")
    doser.dispense(duration=2.0)
    time.sleep(1)
    
    print("\n2. Medium dose (5 seconds, full gate opening)...")
    doser.dispense(duration=5.0)
    time.sleep(1)
    
    print("\n3. Precise dose with partial gate opening...")
    print("   (3 seconds, gate at 30°)")
    doser.dispense(duration=3.0, gate_angle=30)
    time.sleep(1)


def demo_gate_flow_control(doser: SolidDoser):
    """Demonstrate flow control using gate angle"""
    print("\n" + "="*60)
    print("DEMO 3: Flow Control via Gate Angle")
    print("="*60)
    
    gate_angles = [20, 40, 60, 80, 90]
    
    print(f"\nDispensing at different gate angles...")
    print("(Motor runs constantly, gate angle varies)\n")
    
    for angle in gate_angles:
        print(f"  - Gate angle: {angle}° (dispensing for 3 seconds)...")
        doser.dispense(duration=3.0, gate_angle=angle)
        time.sleep(1)
    
    print("\nFlow control demo complete!")


def demo_purge_function(doser: SolidDoser):
    """Demonstrate purge function"""
    print("\n" + "="*60)
    print("DEMO 4: Purge Function")
    print("="*60)
    
    print("\nRunning purge cycle to clear material...")
    doser.purge(duration=3.0)
    print("Purge complete!")


def interactive_menu(doser: SolidDoser):
    """Interactive menu for manual testing"""
    print("\n" + "="*60)
    print("INTERACTIVE MODE")
    print("="*60)
    
    while True:
        print("\nOptions:")
        print("  1. Open gate")
        print("  2. Close gate")
        print("  3. Set gate angle")
        print("  4. Motor ON")
        print("  5. Motor OFF")
        print("  6. Dispense (timed)")
        print("  7. Purge")
        print("  8. Show status")
        print("  9. Home (safe position)")
        print("  0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        try:
            if choice == '1':
                doser.open_gate()
                print("✓ Gate opened")
            
            elif choice == '2':
                doser.close_gate()
                print("✓ Gate closed")
            
            elif choice == '3':
                angle = float(input("Enter gate angle (0-90): "))
                doser.set_gate_angle(angle)
                print(f"✓ Gate set to {angle}°")
            
            elif choice == '4':
                doser.motor_on()
                print("✓ Motor started")
            
            elif choice == '5':
                doser.motor_off()
                print("✓ Motor stopped")
            
            elif choice == '6':
                duration = float(input("Duration (seconds): "))
                gate = input("Gate angle (press Enter for full open): ").strip()
                gate_angle = float(gate) if gate else None
                doser.dispense(duration=duration, gate_angle=gate_angle)
                print("✓ Dispense complete")
            
            elif choice == '7':
                duration = float(input("Purge duration (seconds, default=2): ").strip() or "2")
                doser.purge(duration=duration)
                print("✓ Purge complete")
            
            elif choice == '8':
                status = doser.get_status()
                print("\nCurrent Status:")
                print(f"  Gate Position: {status['gate_position']}°")
                print(f"  Motor Running: {status['motor_running']}")
                print(f"  Is Dispensing: {status['is_dispensing']}")
            
            elif choice == '9':
                doser.home()
                print("✓ Moved to home position")
            
            elif choice == '0':
                print("Exiting interactive mode...")
                break
            
            else:
                print("Invalid option. Please try again.")
        
        except ValueError as e:
            print(f"Invalid input: {e}")
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main demo program"""
    print("="*60)
    print("SOLID DOSER DEMO")
    print("="*60)
    print("\nThis demo tests the solid dosing mechanism.")
    print("\nHardware Setup:")
    print("  - Waveshare PCA9685 HAT (default I2C address 0x40)")
    print("  - Servo on Channel 0 (gate control)")
    print("  - Relay on GPIO 17 / Physical Pin 11 (motor control)")
    print("  - 5V 5A power supply (single plug)")
    print("  - Note: Channels 3, 6, 9 reserved for plate_loader")
    print("\n" + "="*60)
    
    # Configuration
    i2c_address = 0x40  # Waveshare default
    motor_gpio = 17
    
    # Allow override
    print(f"\nDefault I2C address: 0x{i2c_address:02X}")
    print(f"Default motor GPIO: {motor_gpio}")
    custom = input("\nUse defaults? (Y/N): ").strip().upper()
    
    if custom == 'N':
        addr_input = input(f"Enter I2C address (hex, default 0x{i2c_address:02X}): ").strip()
        if addr_input:
            i2c_address = int(addr_input, 16)
        
        gpio_input = input(f"Enter motor GPIO pin (BCM, default {motor_gpio}): ").strip()
        if gpio_input:
            motor_gpio = int(gpio_input)
    
    try:
        # Initialize solid doser
        print(f"\nInitializing Solid Doser...")
        print(f"  I2C Address: 0x{i2c_address:02X}")
        print(f"  Motor GPIO: {motor_gpio}")
        
        doser = SolidDoser(i2c_address=i2c_address, motor_gpio_pin=motor_gpio)
        
        # Calibration
        print("\nRunning initial calibration...")
        doser.calibrate()
        
        # Demo menu
        while True:
            print("\n" + "="*60)
            print("DEMO MENU")
            print("="*60)
            print("\n1. Basic Controls (gate & motor)")
            print("2. Automated Dispense Sequences")
            print("3. Gate Flow Control")
            print("4. Purge Function")
            print("5. Interactive Mode")
            print("6. Run All Demos")
            print("7. Recalibrate")
            print("8. Show Status")
            print("0. Exit")
            
            choice = input("\nSelect demo: ").strip()
            
            if choice == '1':
                demo_basic_controls(doser)
            elif choice == '2':
                demo_dispense_sequences(doser)
            elif choice == '3':
                demo_gate_flow_control(doser)
            elif choice == '4':
                demo_purge_function(doser)
            elif choice == '5':
                interactive_menu(doser)
            elif choice == '6':
                demo_basic_controls(doser)
                demo_dispense_sequences(doser)
                demo_gate_flow_control(doser)
                demo_purge_function(doser)
                print("\n✓ All demos completed!")
            elif choice == '7':
                print("\nRecalibrating...")
                doser.calibrate()
            elif choice == '8':
                status = doser.get_status()
                print(f"\nStatus: {status}")
            elif choice == '0':
                print("\nExiting...")
                break
            else:
                print("Invalid selection. Please try again.")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'doser' in locals():
            print("\nShutting down...")
            doser.shutdown()
            print("Done!")


if __name__ == "__main__":
    main()

