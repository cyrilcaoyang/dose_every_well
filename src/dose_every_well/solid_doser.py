#!/usr/bin/env python3
"""
Solid Doser Controller
Controls solid dosing mechanism using Waveshare PCA9685 HAT and GPIO relay.

Hardware:
- Raspberry Pi 5
- Waveshare PCA9685 HAT (I2C default address 0x40, servo pins 3-8)
- 1x Servo Motor (Channel 0): Hopper gate/valve control
- 1x 5V Relay Module (GPIO): DC motor ON/OFF control
- 1x DC Motor: Auger/screw feeder for solid dispensing

Power:
- Single 5V 5A power supply for Pi, servos, and motor
- Sequential operation to stay within power budget
- Motor reaches steady state before servos move
"""

import time
import logging
from typing import Optional

try:
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo
    import board
    import busio
    import RPi.GPIO as GPIO
except ImportError as e:
    print("Required libraries not installed. On Raspberry Pi, run:")
    print("  pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-motor RPi.GPIO")
    raise e


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SolidDoser:
    """
    Controls solid dosing mechanism with servo gate and relay-controlled DC motor.
    
    Power-safe operation:
    - Motor starts first and reaches steady state (low current)
    - Servos move one at a time to minimize current draw
    - Designed for 5V 5A power supply
    
    Attributes:
        GATE_SERVO: Channel 3 (Pin 3 on HAT) - Hopper gate/valve servo
        MOTOR_RELAY_PIN: GPIO pin controlling relay for DC motor
    """
    
    # Servo channel assignment (Waveshare PCA9685 HAT)
    # Using channel 0 to avoid conflict with plate_loader (channels 3, 6, 9)
    GATE_SERVO = 0  # First servo channel on HAT
    
    # GPIO pin for relay control
    MOTOR_RELAY_PIN = 17  # BCM GPIO 17 (Physical Pin 11)
    
    # Servo angle limits
    GATE_CLOSED_ANGLE = 0      # Gate fully closed
    GATE_OPEN_ANGLE = 90       # Gate fully open
    
    # Power management delays
    MOTOR_STARTUP_DELAY = 0.5  # Wait for motor to reach steady state
    SERVO_MOVE_DELAY = 0.3     # Wait between servo movements
    
    def __init__(self, i2c_address: int = 0x40, motor_gpio_pin: int = 17, frequency: int = 50):
        """
        Initialize the solid doser controller.
        
        Args:
            i2c_address: I2C address of PCA9685 (default 0x40 for Waveshare HAT)
            motor_gpio_pin: GPIO pin (BCM) for relay control (default 17)
            frequency: PWM frequency in Hz (default 50 for servos)
        """
        logger.info("Initializing Solid Doser...")
        
        # Store GPIO pin
        self.MOTOR_RELAY_PIN = motor_gpio_pin
        
        # Initialize GPIO for relay
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.MOTOR_RELAY_PIN, GPIO.OUT)
        GPIO.output(self.MOTOR_RELAY_PIN, GPIO.LOW)  # Start with motor OFF
        
        # Initialize I2C bus
        self.i2c = busio.I2C(board.SCL, board.SDA)
        
        # Initialize PCA9685
        self.pca = PCA9685(self.i2c, address=i2c_address)
        self.pca.frequency = frequency
        
        # Initialize gate servo
        self.gate_servo = servo.Servo(
            self.pca.channels[self.GATE_SERVO],
            min_pulse=500,
            max_pulse=2500
        )
        
        # Current positions/states
        self._gate_position = self.GATE_CLOSED_ANGLE
        self._motor_running = False
        
        # Initialize to safe state
        self.close_gate()
        
        logger.info("Solid Doser initialized successfully")
        logger.info(f"  Gate servo: channel {self.GATE_SERVO}")
        logger.info(f"  Motor relay: GPIO {self.MOTOR_RELAY_PIN}")
        logger.info(f"  I2C address: 0x{i2c_address:02X}")
        logger.info("  Note: Channels 3, 6, 9 reserved for plate_loader")
    
    def motor_on(self):
        """
        Turn DC motor ON via relay.
        Includes startup delay for power-safe operation.
        """
        if not self._motor_running:
            logger.info("Starting motor...")
            GPIO.output(self.MOTOR_RELAY_PIN, GPIO.HIGH)
            self._motor_running = True
            logger.info(f"Waiting {self.MOTOR_STARTUP_DELAY}s for motor to reach steady state...")
            time.sleep(self.MOTOR_STARTUP_DELAY)
            logger.info("Motor running at steady state")
    
    def motor_off(self):
        """
        Turn DC motor OFF via relay.
        """
        if self._motor_running:
            logger.info("Stopping motor...")
            GPIO.output(self.MOTOR_RELAY_PIN, GPIO.LOW)
            self._motor_running = False
    
    def open_gate(self, angle: Optional[float] = None):
        """
        Open the hopper gate to allow solid flow.
        Power-safe: Includes delay after movement.
        
        Args:
            angle: Specific angle to open (None = fully open to GATE_OPEN_ANGLE)
        """
        target = angle if angle is not None else self.GATE_OPEN_ANGLE
        target = max(self.GATE_CLOSED_ANGLE, min(target, self.GATE_OPEN_ANGLE))
        
        logger.info(f"Opening gate to {target}°")
        self.gate_servo.angle = target
        self._gate_position = target
        time.sleep(self.SERVO_MOVE_DELAY)  # Power-safe delay
    
    def close_gate(self):
        """
        Close the hopper gate to stop solid flow.
        Power-safe: Includes delay after movement.
        """
        logger.info(f"Closing gate from {self._gate_position}° to {self.GATE_CLOSED_ANGLE}°")
        self.gate_servo.angle = self.GATE_CLOSED_ANGLE
        self._gate_position = self.GATE_CLOSED_ANGLE
        time.sleep(self.SERVO_MOVE_DELAY)  # Power-safe delay
    
    def set_gate_angle(self, angle: float):
        """
        Set gate to a specific angle for precise flow control.
        Power-safe: Includes delay after movement.
        
        Args:
            angle: Target angle (0-90 degrees)
        """
        angle = max(self.GATE_CLOSED_ANGLE, min(angle, self.GATE_OPEN_ANGLE))
        logger.info(f"Setting gate to {angle}°")
        self.gate_servo.angle = angle
        self._gate_position = angle
        time.sleep(self.SERVO_MOVE_DELAY)  # Power-safe delay
    
    def dispense(self, duration: float, gate_angle: Optional[float] = None):
        """
        Dispense solid material for specified duration.
        
        Power-safe sequence:
        1. Start motor and wait for steady state
        2. Open gate (low current operation)
        3. Run for specified duration
        4. Close gate
        5. Stop motor
        
        Args:
            duration: Dispensing time in seconds
            gate_angle: Gate opening angle (None = fully open)
        """
        logger.info(f"Starting dispense: {duration}s")
        
        try:
            # Step 1: Start motor (includes startup delay)
            self.motor_on()
            
            # Step 2: Open gate (motor already at steady state)
            if gate_angle is not None:
                self.open_gate(gate_angle)
            else:
                self.open_gate()
            
            # Step 3: Dispense for specified duration
            logger.info(f"Dispensing for {duration}s...")
            time.sleep(duration)
            
        finally:
            # Always close gate and stop motor, even if interrupted
            logger.info("Stopping dispense...")
            self.close_gate()
            self.motor_off()
            
        logger.info("Dispense complete")
    
    def purge(self, duration: float = 2.0):
        """
        Run motor to clear any material (gate open, motor running).
        Useful for clearing blockages or residual material.
        
        Args:
            duration: Purge duration in seconds
        """
        logger.info(f"Purging for {duration}s")
        
        try:
            self.motor_on()
            self.open_gate()
            time.sleep(duration)
        finally:
            self.close_gate()
            self.motor_off()
        
        logger.info("Purge complete")
    
    def calibrate(self):
        """
        Calibration routine to test gate servo and motor.
        Runs power-safe sequential operations.
        """
        logger.info("Starting solid doser calibration...")
        
        # Test gate
        logger.info("Testing gate servo...")
        self.close_gate()
        time.sleep(1)
        self.open_gate()
        time.sleep(1)
        self.set_gate_angle(45)  # Half open
        time.sleep(1)
        self.close_gate()
        
        # Test motor
        logger.info("Testing motor (3 seconds)...")
        self.motor_on()
        time.sleep(3)
        self.motor_off()
        
        logger.info("Calibration complete")
    
    def get_status(self) -> dict:
        """
        Get current status of doser components.
        
        Returns:
            Dictionary with gate position, motor state
        """
        return {
            "gate_position": self._gate_position,
            "motor_running": self._motor_running,
            "is_dispensing": self._motor_running and self._gate_position > self.GATE_CLOSED_ANGLE
        }
    
    def home(self):
        """
        Return to safe home position (gate closed, motor stopped).
        """
        logger.info("Homing solid doser...")
        self.motor_off()
        self.close_gate()
        logger.info("Solid doser at home position")
    
    def shutdown(self):
        """
        Safely shutdown the controller.
        """
        logger.info("Shutting down Solid Doser...")
        self.home()
        self.pca.deinit()
        GPIO.cleanup()
        logger.info("Solid Doser shutdown complete")


def main():
    """Example usage of SolidDoser"""
    print("=== Solid Doser Controller ===")
    print("Hardware: Waveshare PCA9685 HAT + GPIO Relay")
    print("Initializing...")
    
    try:
        # Initialize doser
        doser = SolidDoser(i2c_address=0x70, motor_gpio_pin=17)
        
        # Calibration
        print("\n1. Running calibration...")
        doser.calibrate()
        
        # Test dispense
        print("\n2. Testing dispense function...")
        choice = input("Run dispense test (Y/N)? ").strip().upper()
        if choice == 'Y':
            duration = float(input("Duration (seconds): "))
            doser.dispense(duration=duration)
        
        # Show status
        status = doser.get_status()
        print(f"\nFinal Status: {status}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if 'doser' in locals():
            doser.shutdown()


if __name__ == "__main__":
    main()

