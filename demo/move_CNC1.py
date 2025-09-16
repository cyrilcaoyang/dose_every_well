#!/usr/bin/env python3
"""
CNC Machine Movement Script
Moves the machine to specific X, Y, Z coordinates with proper G-code management.
Drafted with Cursor code writer
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from liquid_cnc import load_config, CNC_Controller
import time


def move_cnc(target_x, target_y, target_z, controller):

    # Move X and Y together (XY plane)
    print("Moving X and Y axes...")
    controller.gcode = ""  # Clear any previous G-code
    controller.move_to_point(target_x, target_y)
    controller.execute_movement()

    time.sleep(2)
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
            print("Movement completed but target may not be fully reached")
            print(f"  X: target={target_x}, actual={coords['X']:.2f}")
            print(f"  Y: target={target_y}, actual={coords['Y']:.2f}")
            print(f"  Z: target={target_z}, actual={coords['Z']:.2f}")
            
            # Debug: Show raw machine response
            # print("\n--- Debug: Raw Machine Response ---")
            # try:
            #     import serial
            #     with serial.Serial(controller.SERIAL_PORT_PATH, controller.BAUD_RATE) as ser:
            #         controller.wake_up(ser)
            #         ser.reset_input_buffer()
            #         ser.write(b"?\n")
            #         time.sleep(0.2)
            #         response = ser.read_all().decode().strip()
            #         print(f"Raw response: {repr(response)}")
                    
            #         if 'MPos:' in response:
            #             mpos_start = response.find('MPos:') + 5
            #             mpos_end = response.find('|', mpos_start)
            #             if mpos_end == -1:
            #                 mpos_end = len(response)
            #             mpos_section = response[mpos_start:mpos_end]
            #             print(f"MPos section: {repr(mpos_section)}")
            # except Exception as e:
            #     print(f"Debug error: {e}")
        else:
            print("All targets reached successfully!")
    else:
        print("Could not read final coordinates")

def get_well_dict(num_rows, num_cols, A1_x, A1_y, dx, dy):

    """Input: various wellplate statistics
       Output: dictionary of well names and xy coordinates """
    
    # add more if needed
    letters = "ABCDEFGH"
    well_dict = {}

    for num in range(num_cols):
        # actual location coordinates are computed with the raw index
        # this is intentionally flipped due to the particular setup
        well_y = A1_x + (num)*dx

        for i_lett in range(num_rows):
            # actual location coordinates are computed with the raw index
            # this is intentionally flipped due to the particular setup
            well_x = A1_y + (i_lett)*dy

            lett = letters[i_lett]
            # add 1 to the displayed well name
            well_dict[f"{lett}{num+1}"] = [well_x, well_y]

    return well_dict
def main():

    print("=== CNC Machine Movement Script ===")

    # eventual goals:
    # 1. Move to A1 on the wellplate
    # 2. Move down and wait for input
    # 3. Move up, then move to B1
    # 4. Do the same for the rest of the wells
    # like the opentrons, it should take in A1 location and well spacings
    # and also number of wells (n rows and n cols)

    # Initial coordinates
    A1_x = 200
    A1_y = 200
    plate_z = -10 # top of Z axis is 0
    plate_dz = -10

    dx = -15
    dy = -10

    num_rows = 4
    num_cols = 6
    well_dict = get_well_dict(num_rows, num_cols, A1_x, A1_y, dx, dy)
    print(f"A1 location: X={A1_x}, Y={A1_y}, Z={plate_z}")
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
            print("Machine is homed and ready for movement")
        else:
            print("**Machine may not be homed - homing recommended**")
            response = input("Do you want to home the machine first? (clear the deck if yes) (y/n): ")
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
        print(f"\n--- Moving to A1 ---")
        print(f"Target: X={A1_x}, Y={A1_y}, Z={plate_z}")
        print("WARNING: Ensure tool is clear of workpiece!")
        input("Press Enter to continue with movement...")
        
        print("Executing movement...")
        move_cnc(A1_x, A1_y, plate_z, controller)

        response = input("Check if A1 is aligned (y/n) ")
        if response.lower() in ['y', 'yes']:
            print("Lowering head")

            controller.gcode = ""  # Clear previous G-code
            controller.move_to_height(plate_z+plate_dz)
            controller.execute_movement()
            print("Head lowered")
        else:
            print("Repeat code with updated A1 coordinates")
            
            return

        response = input("Press enter after dispense is complete")

        controller.gcode = ""  # Clear previous G-code
        controller.move_to_height(plate_z)
        controller.execute_movement()

        # start at 1, because the machine is already at A1
        for well in list(well_dict.keys())[1:]:
            print(well)

            # move to the well's xy. Z should be the same
            controller.gcode = ""  # Clear any previous G-code
            controller.move_to_point(well_dict[well][0], well_dict[well][1])
            controller.execute_movement()

            # move_cnc(well_dict[well][0], well_dict[well][1], plate_z, controller)

            controller.gcode = ""  # Clear previous G-code
            controller.move_to_height(plate_z+plate_dz)
            controller.execute_movement()

            response = input("Press enter after dispense is complete")
            controller.gcode = ""  # Clear previous G-code
            controller.move_to_height(plate_z)
            controller.execute_movement()
            




        





        

    except Exception as e:
        print(f"Error during movement: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nMovement script finished.")

if __name__ == "__main__":
    main()
