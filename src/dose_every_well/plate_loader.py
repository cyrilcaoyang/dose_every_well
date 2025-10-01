#!/usr/bin/env python3
"""
Motorized Plate Loader Controller
Controls well plate loading mechanism using PCA9685 PWM controller and servo motors.

Hardware:
- Raspberry Pi 5
- PCA9685 16-channel PWM HAT
- 3x 5V Servo Motors:
  - Channel 3: Well plate lift (synchronized with channel 6)
  - Channel 6: Well plate lift (synchronized with channel 3)
  - Channel 9: Lid open/close mechanism
- OEM Load Cell (connected to ADC)
"""

import time
import logging
from typing import Optional, Tuple

try:
    from adafruit_pca9685 import PCA9685
    import board
    import busio
    from adafruit_motor import servo
except ImportError as e:
    print("Required libraries not installed. On Raspberry Pi, run:")
    print("  pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-motor")
    raise e


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlateLoader:
    """
    Controls motorized well plate loader with synchronized servos.
    
    Attributes:
        PLATE_LIFT_1: Channel 3 - First plate lift servo
        PLATE_LIFT_2: Channel 6 - Second plate lift servo (synchronized)
        LID_SERVO: Channel 9 - Lid open/close servo
    """
    
    # Servo channel assignments
    PLATE_LIFT_1 = 3
    PLATE_LIFT_2 = 6
    LID_SERVO = 9
    
    # Servo angle limits (adjust for your hardware)
    PLATE_DOWN_ANGLE = 0      # Well plate fully lowered
    PLATE_UP_ANGLE = 90       # Well plate fully raised
    LID_CLOSED_ANGLE = 0      # Lid closed position
    LID_OPEN_ANGLE = 90       # Lid open position
    
    # Movement parameters
    DEFAULT_MOVE_SPEED = 20   # Degrees per step
    DEFAULT_MOVE_DELAY = 0.05 # Seconds between steps
    
    def __init__(self, i2c_address: int = 0x40, frequency: int = 50):
        """
        Initialize the plate loader controller.
        
        Args:
            i2c_address: I2C address of PCA9685 (default 0x40)
            frequency: PWM frequency in Hz (default 50 for servos)
        """
        logger.info("Initializing Plate Loader...")
        
        # Initialize I2C bus
        self.i2c = busio.I2C(board.SCL, board.SDA)
        
        # Initialize PCA9685
        self.pca = PCA9685(self.i2c, address=i2c_address)
        self.pca.frequency = frequency
        
        # Initialize servos
        self.plate_lift_1 = servo.Servo(
            self.pca.channels[self.PLATE_LIFT_1],
            min_pulse=500,
            max_pulse=2500
        )
        
        self.plate_lift_2 = servo.Servo(
            self.pca.channels[self.PLATE_LIFT_2],
            min_pulse=500,
            max_pulse=2500
        )
        
        self.lid_servo = servo.Servo(
            self.pca.channels[self.LID_SERVO],
            min_pulse=500,
            max_pulse=2500
        )
        
        # Current positions
        self._plate_position = self.PLATE_DOWN_ANGLE
        self._lid_position = self.LID_CLOSED_ANGLE
        
        # Initialize to default positions
        self._set_plate_servos(self.PLATE_DOWN_ANGLE)
        self.lid_servo.angle = self.LID_CLOSED_ANGLE
        
        logger.info("Plate Loader initialized successfully")
        logger.info(f"  Plate lift servos: channels {self.PLATE_LIFT_1}, {self.PLATE_LIFT_2}")
        logger.info(f"  Lid servo: channel {self.LID_SERVO}")
    
    def _set_plate_servos(self, angle: float):
        """
        Set both plate lift servos to the same angle (synchronized movement).
        
        Args:
            angle: Target angle in degrees
        """
        self.plate_lift_1.angle = angle
        self.plate_lift_2.angle = angle
        self._plate_position = angle
    
    def _move_smooth(self, current: float, target: float, 
                     set_func, speed: float = None, delay: float = None):
        """
        Move servo smoothly from current to target position.
        
        Args:
            current: Current angle
            target: Target angle
            set_func: Function to set the servo angle
            speed: Movement speed in degrees per step
            delay: Delay between steps in seconds
        """
        speed = speed or self.DEFAULT_MOVE_SPEED
        delay = delay or self.DEFAULT_MOVE_DELAY
        
        if current == target:
            return
        
        direction = 1 if target > current else -1
        steps = abs(int((target - current) / speed))
        
        for i in range(steps + 1):
            angle = current + (direction * speed * i)
            # Clamp to target
            if direction > 0:
                angle = min(angle, target)
            else:
                angle = max(angle, target)
            
            set_func(angle)
            time.sleep(delay)
        
        # Ensure we reach exact target
        set_func(target)
    
    def raise_plate(self, degrees: Optional[float] = None, smooth: bool = True):
        """
        Raise the well plate by specified degrees or to full up position.
        
        Args:
            degrees: Rotation degrees (None = full raise to PLATE_UP_ANGLE)
            smooth: If True, move smoothly; if False, move directly
        """
        if degrees is None:
            target = self.PLATE_UP_ANGLE
        else:
            target = min(self._plate_position + degrees, self.PLATE_UP_ANGLE)
        
        logger.info(f"Raising plate from {self._plate_position}° to {target}°")
        
        if smooth:
            self._move_smooth(
                self._plate_position,
                target,
                self._set_plate_servos
            )
        else:
            self._set_plate_servos(target)
        
        logger.info("Plate raised successfully")
    
    def lower_plate(self, degrees: Optional[float] = None, smooth: bool = True):
        """
        Lower the well plate by specified degrees or to full down position.
        
        Args:
            degrees: Rotation degrees (None = full lower to PLATE_DOWN_ANGLE)
            smooth: If True, move smoothly; if False, move directly
        """
        if degrees is None:
            target = self.PLATE_DOWN_ANGLE
        else:
            target = max(self._plate_position - degrees, self.PLATE_DOWN_ANGLE)
        
        logger.info(f"Lowering plate from {self._plate_position}° to {target}°")
        
        if smooth:
            self._move_smooth(
                self._plate_position,
                target,
                self._set_plate_servos
            )
        else:
            self._set_plate_servos(target)
        
        logger.info("Plate lowered successfully")
    
    def move_plate_to(self, angle: float, smooth: bool = True):
        """
        Move plate to specific angle.
        
        Args:
            angle: Target angle (0-180 degrees)
            smooth: If True, move smoothly; if False, move directly
        """
        # Clamp angle to valid range
        angle = max(self.PLATE_DOWN_ANGLE, min(angle, self.PLATE_UP_ANGLE))
        
        logger.info(f"Moving plate to {angle}°")
        
        if smooth:
            self._move_smooth(
                self._plate_position,
                angle,
                self._set_plate_servos
            )
        else:
            self._set_plate_servos(angle)
    
    def open_lid(self, smooth: bool = True):
        """
        Open the lid.
        
        Args:
            smooth: If True, move smoothly; if False, move directly
        """
        logger.info(f"Opening lid from {self._lid_position}° to {self.LID_OPEN_ANGLE}°")
        
        if smooth:
            self._move_smooth(
                self._lid_position,
                self.LID_OPEN_ANGLE,
                lambda angle: setattr(self.lid_servo, 'angle', angle)
            )
        else:
            self.lid_servo.angle = self.LID_OPEN_ANGLE
        
        self._lid_position = self.LID_OPEN_ANGLE
        logger.info("Lid opened")
    
    def close_lid(self, smooth: bool = True):
        """
        Close the lid.
        
        Args:
            smooth: If True, move smoothly; if False, move directly
        """
        logger.info(f"Closing lid from {self._lid_position}° to {self.LID_CLOSED_ANGLE}°")
        
        if smooth:
            self._move_smooth(
                self._lid_position,
                self.LID_CLOSED_ANGLE,
                lambda angle: setattr(self.lid_servo, 'angle', angle)
            )
        else:
            self.lid_servo.angle = self.LID_CLOSED_ANGLE
        
        self._lid_position = self.LID_CLOSED_ANGLE
        logger.info("Lid closed")
    
    def rotate_lid(self, angle: float, smooth: bool = True):
        """
        Rotate lid to specific angle.
        
        Args:
            angle: Target angle (0-180 degrees)
            smooth: If True, move smoothly; if False, move directly
        """
        # Clamp angle to valid range
        angle = max(self.LID_CLOSED_ANGLE, min(angle, self.LID_OPEN_ANGLE))
        
        logger.info(f"Rotating lid to {angle}°")
        
        if smooth:
            self._move_smooth(
                self._lid_position,
                angle,
                lambda a: setattr(self.lid_servo, 'angle', a)
            )
        else:
            self.lid_servo.angle = angle
        
        self._lid_position = angle
    
    def get_positions(self) -> Tuple[float, float]:
        """
        Get current positions of plate and lid.
        
        Returns:
            Tuple of (plate_angle, lid_angle)
        """
        return (self._plate_position, self._lid_position)
    
    def load_sequence(self):
        """
        Execute complete plate loading sequence:
        1. Open lid
        2. Raise plate
        3. Wait for plate insertion
        4. Lower plate
        5. Close lid
        """
        logger.info("Starting plate loading sequence")
        
        self.open_lid(smooth=True)
        time.sleep(1)
        
        self.raise_plate(smooth=True)
        logger.info("Plate ready for loading. Insert plate and press Enter...")
        input()  # Wait for user
        
        self.lower_plate(smooth=True)
        time.sleep(0.5)
        
        self.close_lid(smooth=True)
        logger.info("Plate loading sequence complete")
    
    def unload_sequence(self):
        """
        Execute complete plate unloading sequence:
        1. Open lid
        2. Raise plate
        3. Wait for plate removal
        4. Lower plate
        5. Close lid
        """
        logger.info("Starting plate unloading sequence")
        
        self.open_lid(smooth=True)
        time.sleep(1)
        
        self.raise_plate(smooth=True)
        logger.info("Plate ready for removal. Remove plate and press Enter...")
        input()  # Wait for user
        
        self.lower_plate(smooth=True)
        time.sleep(0.5)
        
        self.close_lid(smooth=True)
        logger.info("Plate unloading sequence complete")
    
    def calibrate(self):
        """
        Calibration routine to test servo ranges.
        """
        logger.info("Starting calibration...")
        
        logger.info("Testing plate lift servos...")
        self.lower_plate(smooth=True)
        time.sleep(1)
        self.raise_plate(smooth=True)
        time.sleep(1)
        self.lower_plate(smooth=True)
        
        logger.info("Testing lid servo...")
        self.close_lid(smooth=True)
        time.sleep(1)
        self.open_lid(smooth=True)
        time.sleep(1)
        self.close_lid(smooth=True)
        
        logger.info("Calibration complete")
    
    def home(self):
        """
        Return all servos to home position (plate down, lid closed).
        """
        logger.info("Homing all servos...")
        self.lower_plate(smooth=True)
        self.close_lid(smooth=True)
        logger.info("All servos at home position")
    
    def shutdown(self):
        """
        Safely shutdown the controller.
        """
        logger.info("Shutting down Plate Loader...")
        self.home()
        self.pca.deinit()
        logger.info("Plate Loader shutdown complete")


def main():
    """Example usage of PlateLoader"""
    print("=== Plate Loader Controller ===")
    print("Initializing...")
    
    try:
        loader = PlateLoader()
        
        # Calibration
        print("\n1. Running calibration...")
        loader.calibrate()
        
        # Test individual movements
        print("\n2. Testing plate movements...")
        loader.raise_plate(degrees=45, smooth=True)
        time.sleep(1)
        loader.lower_plate(degrees=45, smooth=True)
        
        print("\n3. Testing lid movements...")
        loader.open_lid(smooth=True)
        time.sleep(1)
        loader.close_lid(smooth=True)
        
        # Full sequences
        print("\n4. Ready for full sequence test")
        choice = input("Test (L)oad or (U)nload sequence? [L/U]: ").strip().upper()
        
        if choice == 'L':
            loader.load_sequence()
        elif choice == 'U':
            loader.unload_sequence()
        
        # Get current positions
        plate_pos, lid_pos = loader.get_positions()
        print(f"\nFinal positions: Plate={plate_pos}°, Lid={lid_pos}°")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if 'loader' in locals():
            loader.shutdown()


if __name__ == "__main__":
    main()

