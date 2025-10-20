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

Configuration:
All settings are loaded from 'plate_settings.yaml' including:
- Servo channel assignments and angle limits
- Movement parameters (speed, delays)
- Plate types with collision avoidance settings
- PWM controller settings

Collision Avoidance:
The controller includes configurable collision avoidance to prevent the lid from
hitting the plate. Plate types can be customized in plate_settings.yaml:
- 'shallow_plate': For standard 96-well plates
- 'deep_well': For deep-well plates with extra clearance
- 'custom_384_well': Custom plate type example
- 'disabled': Disables collision checking (use with caution!)

Safety Rules (for shallow_plate):
- When plate is raised (< 50°), lid must stay open (<= 40°)
- When lid is closed (> 40°), plate must stay lowered (>= 50°)

Example:
    # Plate type MUST be explicitly specified for safety
    loader = PlateLoader(plate_type='shallow_plate')
    loader = PlateLoader(plate_type='deep_well')
    loader.print_collision_info()  # View current settings
    
    # Change plate type after initialization
    loader.set_plate_type('custom_384_well')
"""

import time
import logging
from typing import Optional, Tuple
from pathlib import Path
import yaml

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
    
    Configuration is loaded from plate_settings.yaml which includes:
    - Servo channel assignments
    - Servo angle limits
    - Movement parameters
    - Plate types with collision avoidance settings
    """
    
    @staticmethod
    def _load_config(config_path: Optional[Path] = None) -> dict:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file. If None, uses default location.
            
        Returns:
            Configuration dictionary
        """
        if config_path is None:
            # Default to plate_settings.yaml in the same directory as this module
            config_path = Path(__file__).parent / "plate_settings.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                "Please ensure plate_settings.yaml exists in the module directory."
            )
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration from: {config_path}")
        return config
    
    def __init__(self, plate_type: str, i2c_address: Optional[int] = None, 
                 frequency: Optional[int] = None, config_path: Optional[Path] = None):
        """
        Initialize the plate loader controller.
        
        Args:
            plate_type: Type of plate being used (REQUIRED - must be explicitly specified)
                       Choose from: 'shallow_plate', 'deep_well', 'custom_384_well', 'disabled'
            i2c_address: I2C address of PCA9685 (default from config file)
            frequency: PWM frequency in Hz (default from config file)
            config_path: Path to configuration file (default: plate_settings.yaml in module directory)
        
        Raises:
            ValueError: If plate_type is not found in plate_settings.yaml
            FileNotFoundError: If config file is not found
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Extract configuration values
        servo_channels = self.config['servo_channels']
        self.PLATE_LIFT_1 = servo_channels['plate_lift_1']
        self.PLATE_LIFT_2 = servo_channels['plate_lift_2']
        self.LID_SERVO = servo_channels['lid_servo']
        
        servo_limits = self.config['servo_limits']
        self.PLATE_DOWN_ANGLE = servo_limits['plate_down_angle']
        self.PLATE_UP_ANGLE = servo_limits['plate_up_angle']
        self.LID_CLOSED_ANGLE = servo_limits['lid_closed_angle']
        self.LID_OPEN_ANGLE = servo_limits['lid_open_angle']
        
        movement = self.config['movement']
        self.DEFAULT_MOVE_SPEED = movement['default_move_speed']
        self.DEFAULT_MOVE_DELAY = movement['default_move_delay']
        
        self.PLATE_TYPES = self.config['plate_types']
        
        # Use provided values or defaults from config
        pwm_config = self.config['pwm_controller']
        i2c_address = i2c_address if i2c_address is not None else pwm_config['i2c_address']
        frequency = frequency if frequency is not None else pwm_config['frequency']
        
        # Validate plate type (REQUIRED parameter - no default)
        if plate_type not in self.PLATE_TYPES:
            available_types = list(self.PLATE_TYPES.keys())
            raise ValueError(
                f"Invalid plate type '{plate_type}'.\n"
                f"Available plate types: {available_types}\n"
                f"Plate type must be explicitly specified for safety.\n"
                f"Example: PlateLoader(plate_type='shallow_plate')"
            )
        
        self.plate_type = plate_type
        plate_config = self.PLATE_TYPES[plate_type]
        self.plate_safe_angle = plate_config['plate_safe_angle']
        self.lid_safe_angle = plate_config['lid_safe_angle']
        
        logger.info("Initializing Plate Loader...")
        logger.info(f"Plate type: {plate_type} - {plate_config['description']}")
        if self.plate_safe_angle is not None:
            logger.info(f"  Safety limits: Plate >= {self.plate_safe_angle}° when Lid > {self.lid_safe_angle}°")
        
        # Initialize I2C bus
        self.i2c = busio.I2C(board.SCL, board.SDA)
        
        # Initialize PCA9685
        self.pca = PCA9685(self.i2c, address=i2c_address)
        self.pca.frequency = frequency
        
        # Get servo pulse width settings from config
        pulse_config = self.config['servo_pulse_width']
        min_pulse = pulse_config['min_pulse']
        max_pulse = pulse_config['max_pulse']
        
        # Initialize servos (using standard 0-180° range, we translate in software)
        self.plate_lift_1 = servo.Servo(
            self.pca.channels[self.PLATE_LIFT_1],
            min_pulse=min_pulse,
            max_pulse=max_pulse
        )
        
        self.plate_lift_2 = servo.Servo(
            self.pca.channels[self.PLATE_LIFT_2],
            min_pulse=min_pulse,
            max_pulse=max_pulse
        )
        
        self.lid_servo = servo.Servo(
            self.pca.channels[self.LID_SERVO],
            min_pulse=min_pulse,
            max_pulse=max_pulse
        )
        
        # Initialization sequence
        logger.info("Starting initialization sequence...")
        
        # Step 1: Retract plate to down position
        logger.info("Step 1: Retracting plate to down position...")
        self._plate_position = self.PLATE_DOWN_ANGLE
        self._set_plate_servos(self.PLATE_DOWN_ANGLE)  # Move to 90° (down)
        time.sleep(1)
        
        # Step 2: Open lid
        logger.info(f"Step 2: Opening lid to {self.LID_OPEN_ANGLE}°...")
        self.lid_servo.angle = self.LID_OPEN_ANGLE  # Open to 30°
        self._lid_position = self.LID_OPEN_ANGLE
        time.sleep(2)
        
        # Step 3: Move plate to up position
        logger.info(f"Step 3: Moving plate to up position ({self.PLATE_UP_ANGLE}°)...")
        self._set_plate_servos(self.PLATE_UP_ANGLE)  # Move to -90° (up)
        self._plate_position = self.PLATE_UP_ANGLE
        
        logger.info("Plate Loader initialized successfully")
        logger.info(f"  Plate lift servos: channels {self.PLATE_LIFT_1}, {self.PLATE_LIFT_2}")
        logger.info(f"  Lid servo: channel {self.LID_SERVO} at {self.LID_OPEN_ANGLE}°")
    
    def _set_plate_servos(self, angle: float):
        """
        Set both plate lift servos to the same angle (synchronized movement).
        Motor 2 is mirrored to move in the same physical direction as Motor 1.
        
        Args:
            angle: Target angle in degrees (-90 to 90 logical range)
        """
        # Translate logical angle (-90 to 90) to servo angle (0 to 180)
        servo1_angle = angle + 90  # -90->0, 0->90, 90->180
        servo2_angle = 90 - angle  # -90->180, 0->90, 90->0 (mirrored)
        
        self.plate_lift_1.angle = servo1_angle
        self.plate_lift_2.angle = servo2_angle
        self._plate_position = angle
        logger.debug(f"Plate servos set - Motor 1 (Ch3): {servo1_angle}° (logical: {angle}°), Motor 2 (Ch6): {servo2_angle}° (mirrored)")
    
    def _check_plate_movement_safe(self, target_plate_angle: float) -> bool:
        """
        Check if moving the plate to target angle would cause collision with lid.
        
        Args:
            target_plate_angle: Proposed plate angle
            
        Returns:
            True if movement is safe, False if collision would occur
        """
        # Skip check if collision avoidance is disabled
        if self.plate_safe_angle is None:
            return True
        
        # Rule: If lid > lid_safe_angle, plate must be >= plate_safe_angle
        if self._lid_position > self.lid_safe_angle and target_plate_angle < self.plate_safe_angle:
            logger.warning(
                f"COLLISION RISK: Cannot move plate to {target_plate_angle}° "
                f"while lid is at {self._lid_position}°. "
                f"Lid is more closed than {self.lid_safe_angle}°, so plate must stay >= {self.plate_safe_angle}°. "
                f"Open lid first or change plate type (current: '{self.plate_type}')."
            )
            return False
        
        return True
    
    def _check_lid_movement_safe(self, target_lid_angle: float) -> bool:
        """
        Check if moving the lid to target angle would cause collision with plate.
        
        Args:
            target_lid_angle: Proposed lid angle
            
        Returns:
            True if movement is safe, False if collision would occur
        """
        # Skip check if collision avoidance is disabled
        if self.lid_safe_angle is None:
            return True
        
        # Rule: If plate < plate_safe_angle, lid must be <= lid_safe_angle
        if self._plate_position < self.plate_safe_angle and target_lid_angle > self.lid_safe_angle:
            logger.warning(
                f"COLLISION RISK: Cannot move lid to {target_lid_angle}° "
                f"while plate is at {self._plate_position}°. "
                f"Plate is more raised than {self.plate_safe_angle}°, so lid must stay <= {self.lid_safe_angle}°. "
                f"Lower plate first or change plate type (current: '{self.plate_type}')."
            )
            return False
        
        return True
    
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
            target = max(self._plate_position - degrees, self.PLATE_UP_ANGLE)
        
        # Check collision safety
        if not self._check_plate_movement_safe(target):
            logger.error(f"Movement blocked: Cannot raise plate to {target}°")
            return
        
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
            target = min(self._plate_position + degrees, self.PLATE_DOWN_ANGLE)
        
        # Check collision safety
        if not self._check_plate_movement_safe(target):
            logger.error(f"Movement blocked: Cannot lower plate to {target}°")
            return
        
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
    
    def pop_plate(self, smooth: bool = True):
        """
        Pop the plate up to -5 degrees (beyond normal up position).
        This extends the plate further up for easier access.
        
        Args:
            smooth: If True, move smoothly; if False, move directly
        """
        target = -5  # Pop up 5 degrees beyond normal upexit position
        
        # Check collision safety
        if not self._check_plate_movement_safe(target):
            logger.error(f"Movement blocked: Cannot pop plate to {target}°")
            return
        
        logger.info(f"Popping plate from {self._plate_position}° to {target}°")
        
        if smooth:
            self._move_smooth(
                self._plate_position,
                target,
                self._set_plate_servos
            )
        else:
            self._set_plate_servos(target)
        
        logger.info("Plate popped successfully")
    
    def move_plate_to(self, angle: float, smooth: bool = True):
        """
        Move plate to specific angle.
        
        Args:
            angle: Target angle (0-180 degrees)
            smooth: If True, move smoothly; if False, move directly
        """
        # Clamp angle to valid range
        angle = max(self.PLATE_DOWN_ANGLE, min(angle, self.PLATE_UP_ANGLE))
        
        # Check collision safety
        if not self._check_plate_movement_safe(angle):
            logger.error(f"Movement blocked: Cannot move plate to {angle}°")
            return
        
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
        # Check collision safety
        if not self._check_lid_movement_safe(self.LID_OPEN_ANGLE):
            logger.error(f"Movement blocked: Cannot open lid to {self.LID_OPEN_ANGLE}°")
            return
        
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
        # Check collision safety
        if not self._check_lid_movement_safe(self.LID_CLOSED_ANGLE):
            logger.error(f"Movement blocked: Cannot close lid to {self.LID_CLOSED_ANGLE}°")
            return
        
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
        angle = max(self.LID_OPEN_ANGLE, min(angle, self.LID_CLOSED_ANGLE))
        
        # Check collision safety
        if not self._check_lid_movement_safe(angle):
            logger.error(f"Movement blocked: Cannot rotate lid to {angle}°")
            return
        
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
    
    def set_plate_type(self, plate_type: str):
        """
        Change the plate type.
        
        Args:
            plate_type: Name of the plate type ('shallow_plate', 'deep_well', 'disabled')
        """
        if plate_type not in self.PLATE_TYPES:
            raise ValueError(f"Invalid plate type '{plate_type}'. "
                           f"Choose from: {list(self.PLATE_TYPES.keys())}")
        
        self.plate_type = plate_type
        plate_config = self.PLATE_TYPES[plate_type]
        self.plate_safe_angle = plate_config['plate_safe_angle']
        self.lid_safe_angle = plate_config['lid_safe_angle']
        
        logger.info(f"Plate type changed to: {plate_type} - {plate_config['description']}")
        if self.plate_safe_angle is not None:
            logger.info(f"  Safety limits: Plate >= {self.plate_safe_angle}° when Lid > {self.lid_safe_angle}°")
        else:
            logger.warning("  Collision avoidance DISABLED - use with caution!")
    
    def get_collision_info(self) -> dict:
        """
        Get current collision avoidance configuration and status.
        
        Returns:
            Dictionary with plate type info and current safety status
        """
        plate_config = self.PLATE_TYPES[self.plate_type]
        
        info = {
            'plate_type': self.plate_type,
            'description': plate_config['description'],
            'plate_safe_angle': self.plate_safe_angle,
            'lid_safe_angle': self.lid_safe_angle,
            'current_plate_angle': self._plate_position,
            'current_lid_angle': self._lid_position,
            'collision_risk': False,
            'warnings': []
        }
        
        # Check current state for collision risk
        if self.plate_safe_angle is not None:
            if self._plate_position < self.plate_safe_angle and self._lid_position > self.lid_safe_angle:
                info['collision_risk'] = True
                info['warnings'].append(
                    f"WARNING: Current position may be unsafe! "
                    f"Plate at {self._plate_position}° (< {self.plate_safe_angle}°) "
                    f"and lid at {self._lid_position}° (> {self.lid_safe_angle}°)"
                )
        
        return info
    
    def print_collision_info(self):
        """Print collision avoidance information in a readable format."""
        info = self.get_collision_info()
        
        print("\n" + "="*60)
        print("COLLISION AVOIDANCE STATUS")
        print("="*60)
        print(f"Plate Type: {info['plate_type']}")
        print(f"Description: {info['description']}")
        
        if info['plate_safe_angle'] is not None:
            print(f"\nSafety Rules:")
            print(f"  - When plate < {info['plate_safe_angle']}° (raised), lid must be <= {info['lid_safe_angle']}° (open)")
            print(f"  - When lid > {info['lid_safe_angle']}° (closed), plate must be >= {info['plate_safe_angle']}° (lowered)")
        else:
            print(f"\nSafety Rules: DISABLED")
        
        print(f"\nCurrent Positions:")
        print(f"  - Plate: {info['current_plate_angle']}°")
        print(f"  - Lid: {info['current_lid_angle']}°")
        
        if info['collision_risk']:
            print(f"\n[WARNING] COLLISION RISK DETECTED!")
            for warning in info['warnings']:
                print(f"  {warning}")
        else:
            print(f"\n[OK] Current positions are safe")
        
        print(f"\nAvailable Plate Types:")
        for name, plate_config in self.PLATE_TYPES.items():
            marker = "*" if name == self.plate_type else " "
            print(f"  {marker} {name}: {plate_config['description']}")
        print("="*60 + "\n")
    
    def reload_config(self, config_path: Optional[Path] = None):
        """
        Reload configuration from YAML file.
        
        Note: This only updates the plate types and movement parameters.
        Servo channels and PWM settings cannot be changed after initialization.
        
        Args:
            config_path: Path to configuration file (default: use same file as initialization)
        
        Raises:
            RuntimeError: If current plate type is removed from config file
        """
        logger.info("Reloading configuration...")
        self.config = self._load_config(config_path)
        
        # Update plate types
        self.PLATE_TYPES = self.config['plate_types']
        
        # Update movement parameters
        movement = self.config['movement']
        self.DEFAULT_MOVE_SPEED = movement['default_move_speed']
        self.DEFAULT_MOVE_DELAY = movement['default_move_delay']
        
        # Re-apply current plate type (in case it was updated)
        if self.plate_type in self.PLATE_TYPES:
            plate_config = self.PLATE_TYPES[self.plate_type]
            self.plate_safe_angle = plate_config['plate_safe_angle']
            self.lid_safe_angle = plate_config['lid_safe_angle']
            logger.info(f"Plate type '{self.plate_type}' updated")
        else:
            available_types = list(self.PLATE_TYPES.keys())
            error_msg = (
                f"Current plate type '{self.plate_type}' not found in reloaded config.\n"
                f"Available plate types: {available_types}\n"
                f"Please use set_plate_type() to switch to a valid type."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info("Configuration reloaded successfully")
    
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
    
    def release_plate_motors(self):
        """
        Release plate lift motors (stops PWM signals).
        WARNING: Motors will not hold position and can be moved manually!
        """
        logger.info("Releasing plate motors...")
        self.pca.channels[self.PLATE_LIFT_1].duty_cycle = 0
        self.pca.channels[self.PLATE_LIFT_2].duty_cycle = 0
        logger.warning("Plate motors unpowered - position not maintained!")
    
    def release_lid_motor(self):
        """
        Release lid motor (stops PWM signal).
        WARNING: Motor will not hold position and can be moved manually!
        """
        logger.info("Releasing lid motor...")
        self.pca.channels[self.LID_SERVO].duty_cycle = 0
        logger.warning("Lid motor unpowered - position not maintained!")
    
    def power_save_mode(self):
        """
        Enter power save mode - stops PWM signals to all servos.
        WARNING: Servos will not hold position and may drift under load!
        """
        logger.info("Entering power save mode...")
        self.pca.channels[self.PLATE_LIFT_1].duty_cycle = 0
        self.pca.channels[self.PLATE_LIFT_2].duty_cycle = 0
        self.pca.channels[self.LID_SERVO].duty_cycle = 0
        logger.warning("All servos unpowered - position not maintained!")
    
    def power_restore(self):
        """
        Restore power to servos at last known positions.
        Re-applies the last commanded positions.
        """
        logger.info("Restoring servo power...")
        self._set_plate_servos(self._plate_position)
        self.lid_servo.angle = self._lid_position
        logger.info(f"Servos restored: Plate={self._plate_position}°, Lid={self._lid_position}°")
    
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

