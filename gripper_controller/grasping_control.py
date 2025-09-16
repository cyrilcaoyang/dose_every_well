import sys
import os
import time
from pathlib import Path
# Add the src directory to the path
sys.path.insert (0, os.path.join (os.path.dirname(__file__), '..', 'src'))
from liquid_cnc.cnc_controller import CNC_Controller, load_config, find_port
from serial_monitor import SerialMonitor
if __name__ == "__main__":

    # Load CNC configuration and find port
    config = load_config ("cnc_settings.yaml", "Genmitsu 4040 PRO")
    port = find_port()
    try:
        controller = CNC_Controller(port, config)
        print(f"CNC controller ready on {controller.SERIAL_PORT_PATH}")
    except Exception as e:
        print(f"Warning: CNC controller error: {e}")
        sys.exit(1)

    # Initialize gripper on COM4 (adjust port if needed)
    gripper = SerialMonitor ("COM4", 9600)
    try:
        response = gripper.send("?")  # Send status query to gripper
        print ("Gripper controller ready on COM4")
    except Exception as e:
            print(f"Warning: Gripper communication error: {e}")
            sys.exit(1)
    
    # Starting the workflow after doing initial checks
    try:
        print ("\nInitial Coordinates:")
        coords = controller.read_coordinates()
        if coords:
            print (f"Current coordinates: X={coords['X']:.2f}, Y={coords['Y']:.2f}, Z={coords['Z']:.2f}")
        else:
            print ("Could not read coordinates")
        
        # Ensure gripper is open before starting
        print ("\nOpening Gripper to Start")
        try:
            response = gripper.send ("OPEN")  # Command to open gripper
            print(f"Gripper open response: {response}")
            time.sleep (1)  # Wait for gripper to open
        except Exception as e:
            print (f"Gripper open error: {e}")
        
        # Home the CNC machine
        print ("\nHoming CNC Machine")
        controller.home_xyz()
        print ("CNC is in the home position")
        
        # Moving in steps to grasp the dosing head
        # Moving to a safe XY position infront of the dosing head
        print("\n--- Moving to safe position")
        controller.move_to_point(388, 225)
        controller.execute_movement()
        time.sleep(15)
        print("XY safe movement completed")
        
        # Move Z down to grasping height
        print("\n--- Moving Z to grasping height ")
        controller.move_to_height(-42.708)
        controller.execute_movement()
        time.sleep(5)
        
        # Moving ahead to be in line with the dosing head
        print("\nMoving forward to align with dosing head")
        controller.move_to_point(388, 50)
        controller.execute_movement()
        time.sleep(10)
        
        # Close gripper to grasp the dosing head
        print("\nClosing Gripper to grasp the dosing head")
        response = gripper.send ("GRASP")
        print(f"Gripper close response: {response}")
        time.sleep(2)
        print("Dosing head grasped")
        
        # Lift object up
        print("\nLifting Dosing Head off the rack")
        controller.move_to_height(-42)
        controller.execute_movement()
        time.sleep(6)
        print("Object lifted to safe height")

        
        # Move to a different location
        print("\nMoving Object to New Location")
        controller.move_to_point(393, 220)  # Move to new location
        controller.execute_movement()
        time.sleep(10)
        print("Moved to new location")
        
        print("\nOpening Gripper to Release")
        response = gripper.send("OPEN")  # Command to open gripper
        print(f"Gripper open response: {response}")
        time.sleep(1)  # Wait for gripper to open
        print(":Object released")
        print("\nFinal Position")
        coords = controller.read_coordinates()
        if coords:
            print(f"Final coordinates: X={coords['X']:.2f}, Y={coords['Y']:.2f}, Z={coords['Z']:.2f}")
        else:
            print("Could not read final coordinates")
        print("Complete pick-and-place operation finished!")
    except Exception as e:
        print(f"Error during operation: {e}")
    finally:
        print("Done.")
