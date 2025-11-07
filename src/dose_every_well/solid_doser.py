#!/usr/bin/env python3
"""
Solid Doser Controller
Controls DC motor via relay and servo via PCA9685.

Hardware:
- Raspberry Pi 5
- Waveshare PCA9685 HAT (I2C default address 0x40)
- 1x Servo Motor (Channel 0): Gate control
- 1x 5V Relay Module (GPIO 17): DC motor ON/OFF control
- 1x DC Motor: Auger/screw feeder

Power:
- Single 5V 5A power supply for Pi, servos, and motor
- Sequential operation to stay within power budget
- Motor reaches steady state before servos move

Simple Usage:
    doser = SolidDoser()
    doser.motor_on()
    doser.set_servo_angle(90)
    doser.motor_off()
    doser.shutdown()
"""

import time
import logging
from typing import Optional

try:
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo
    import board, busio
    import RPi.GPIO as GPIO
except ImportError as e:
    print("Required libraries not installed. On Raspberry Pi, run:")
    print("  pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-motor")
    print("  pip install rpi-lgpio  # Required for Raspberry Pi 5")
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
        GATE_SERVO: Channel 0 Hopper gate/valve servo
        MOTOR_RELAY_PIN: GPIO pin controlling relay for DC motor
    """
    
    # Servo channel assignment (Waveshare PCA9685 HAT)
    # Using channel 0 to avoid conflict with plate_loader (channels 3, 6, 9)
    GATE_SERVO = 0  # First servo channel on HAT
    
    # GPIO pin for relay control
    MOTOR_RELAY_PIN = 17  # BCM GPIO 17 (Physical Pin 11)
    
    # Relay configuration: Active HIGH (relay turns on when GPIO is HIGH)
    # GPIO HIGH → Relay ON → Motor runs
    # GPIO LOW → Relay OFF → Motor stops
    RELAY_NO = True  # True = Normal Open relay with active HIGH trigger
    
    # Servo physical angle limits (servo library angles)
    SERVO_FULLY_EXTENDED = 30   # Pin fully extended (pushed out)
    SERVO_CONTACT_POINT = 65    # Pin makes contact with gate
    SERVO_FULLY_CONTRACTED = 85 # Pin fully contracted (pulled back)
    
    # User-friendly gate position coordinates
    # 0 = contact point, negative = contracted, positive = extended
    GATE_MAX_EXTENSION = 35     # Maximum extension from contact (servo 30°)
    GATE_CONTACT = 0            # Pin touching gate (servo 65°)
    GATE_MAX_CONTRACTION = -20  # Maximum contraction from contact (servo 85°)
    
    # Power management delays
    MOTOR_STARTUP_DELAY = 0.5  # Wait for motor to reach steady state
    SERVO_MOVE_DELAY = 0.5     # Wait between servo movements
    
    def __init__(
        self, 
        i2c_address: int = 0x40, 
        motor_gpio_pin: int = 17, 
        frequency: int = 50
        ):
        """
        Initialize the solid doser controller.
        Args:
            i2c_address: I2C address of PCA9685 (default 0x40 for Waveshare HAT)
            motor_gpio_pin: GPIO pin (BCM) for relay control (default 17)
            frequency: PWM frequency in Hz (default 50 for servos)
        """
        logger.info("Initializing Solid Doser...")
        
        # Store GPIO pin (setup happens in motor_on)
        self.dc_relay_pin = motor_gpio_pin
        
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
        
        # Current positions/states (in user coordinates)
        self._gate_position = self.GATE_MAX_CONTRACTION  # Start contracted (closed)
        self._motor_running = False
        
        # Initialize to safe state
        self.close_gate()
        
        logger.info("Solid Doser initialized successfully")
        logger.info(f"  Gate servo: channel {self.GATE_SERVO}")
        relay_type = "Normal Open (NO)" if self.RELAY_NO else "Normal Closed (NC)"
        logger.info(f"  Motor relay: GPIO {self.dc_relay_pin} ({relay_type})")
        logger.info(f"  I2C address: 0x{i2c_address:02X}")
        logger.info(f"  Gate range: {self.GATE_MAX_EXTENSION} (extended) to {self.GATE_MAX_CONTRACTION} (contracted)")
        logger.info(f"  Contact point: {self.GATE_CONTACT} (servo {self.SERVO_CONTACT_POINT}°)")
        logger.info("  Note: Channels 3, 6, 9 reserved for plate_loader")
    
    def _gate_to_servo_angle(self, gate_position: float) -> float:
        """
        Convert user-friendly gate position to servo angle.
        
        Gate position coordinate system:
        - Positive = extended (pushing gate open)
        - 0 = contact point (pin touching gate)
        - Negative = contracted (pin pulled back, gate closed)
        
        Args:
            gate_position: Position in user coordinates
            
        Returns:
            Servo angle (30-85 degrees)
        """
        # Map: gate position → servo angle
        # gate_position = 35 → servo = 30 (fully extended)
        # gate_position = 0 → servo = 65 (contact)
        # gate_position = -20 → servo = 85 (fully contracted)
        
        # Clamp to valid range
        gate_position = max(self.GATE_MAX_CONTRACTION, min(gate_position, self.GATE_MAX_EXTENSION))
        
        # Linear mapping: servo_angle = contact_point - gate_position
        servo_angle = self.SERVO_CONTACT_POINT - gate_position
        
        return servo_angle
    
    def _servo_to_gate_angle(self, servo_angle: float) -> float:
        """
        Convert servo angle to user-friendly gate position.
        
        Args:
            servo_angle: Servo angle (30-85 degrees)
            
        Returns:
            Gate position in user coordinates
        """
        return self.SERVO_CONTACT_POINT - servo_angle
    
    def motor_on(self):
        """
        Turn DC motor ON via relay.
        Sets up GPIO and turns motor on.
        """
        if not self._motor_running:
            logger.info("Starting motor...")
            # Setup GPIO and turn ON
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            # Active HIGH: HIGH=ON, LOW=OFF
            on_state = GPIO.HIGH if self.RELAY_NO else GPIO.LOW
            GPIO.setup(self.dc_relay_pin, GPIO.OUT, initial=on_state)
            self._motor_running = True
            logger.info(f"Waiting {self.MOTOR_STARTUP_DELAY}s for motor to reach steady state...")
            time.sleep(self.MOTOR_STARTUP_DELAY)
            logger.info("Motor running at steady state")
    
    def motor_off(self):
        """
        Turn DC motor OFF via relay.
        Uses GPIO.cleanup() to reset pin and turn off motor.
        """
        logger.info("Stopping motor...")
        GPIO.cleanup()
        self._motor_running = False
    
    def open_gate(self, gate_position: Optional[float] = None):
        """
        Open the hopper gate by extending the pin to allow solid flow.
        Power-safe: Includes delay after movement.
        
        Args:
            gate_position: Gate position in user coordinates (None = fully extended to 35)
                          Positive values extend the pin (0 to 35)
                          0 = contact point (servo 65°)
        """
        target = gate_position if gate_position is not None else self.GATE_MAX_EXTENSION
        target = max(self.GATE_CONTACT, min(target, self.GATE_MAX_EXTENSION))
        
        servo_angle = self._gate_to_servo_angle(target)
        logger.info(f"Opening gate to position {target} (servo {servo_angle}°)")
        self.gate_servo.angle = servo_angle
        self._gate_position = target
        time.sleep(self.SERVO_MOVE_DELAY)  # Power-safe delay
    
    def close_gate(self):
        """
        Close the hopper gate by contracting the pin to stop solid flow.
        Contracts to position -20 (servo 85°).
        Power-safe: Includes delay after movement.
        """
        target = self.GATE_MAX_CONTRACTION
        servo_angle = self._gate_to_servo_angle(target)
        logger.info(f"Closing gate from position {self._gate_position} to {target} (servo {servo_angle}°)")
        self.gate_servo.angle = servo_angle
        self._gate_position = target
        time.sleep(self.SERVO_MOVE_DELAY)  # Power-safe delay
    
    def set_gate_position(self, gate_position: float):
        """
        Set gate to a specific position for precise flow control.
        Power-safe: Includes delay after movement.
        
        Args:
            gate_position: Target position in user coordinates
                          Range: -20 (fully contracted, servo 85°) to 35 (fully extended, servo 30°)
                          0 = contact point (servo 65°)
        """
        target = max(self.GATE_MAX_CONTRACTION, min(gate_position, self.GATE_MAX_EXTENSION))
        servo_angle = self._gate_to_servo_angle(target)
        logger.info(f"Setting gate to position {target} (servo {servo_angle}°)")
        self.gate_servo.angle = servo_angle
        self._gate_position = target
        time.sleep(self.SERVO_MOVE_DELAY)  # Power-safe delay
    
    def dispense(self, duration: float, gate_position: Optional[float] = None):
        """
        Dispense solid material for specified duration.
        
        Power-safe sequence:
        1. Start motor and wait for steady state
        2. Open gate (low current operation)
        3. Run for specified duration
        4. Close gate (to -20)
        5. Stop motor
        
        Args:
            duration: Dispensing time in seconds
            gate_position: Gate position in user coordinates (None = fully extended to 35)
                          Range: 0 (contact) to 35 (fully extended)
        """
        logger.info(f"Starting dispense: {duration}s")
        
        try:
            # Step 1: Start motor (includes startup delay)
            self.motor_on()
            
            # Step 2: Open gate (motor already at steady state)
            if gate_position is not None:
                self.open_gate(gate_position)
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
        Tests: fully contracted (-20), contact (0), half extension (15), fully extended (35).
        """
        logger.info("Starting solid doser calibration...")
        
        # Test gate
        logger.info("Testing gate servo...")
        self.close_gate()  # Fully contracted (-20, servo 85°)
        time.sleep(1)
        self.set_gate_position(self.GATE_CONTACT)  # Contact point (0, servo 65°)
        time.sleep(1)
        self.set_gate_position(15)  # Half extension (servo 50°)
        time.sleep(1)
        self.open_gate()  # Fully extended (35, servo 30°)
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
            Dictionary with gate position (user coordinates), motor state, and dispensing status
        """
        return {
            "gate_position": self._gate_position,
            "motor_running": self._motor_running,
            "is_dispensing": self._motor_running and self._gate_position > self.GATE_CONTACT
        }
    
    def home(self):
        """
        Return to safe home position (gate closed, motor stopped).
        """
        logger.info("Homing solid doser...")
        self.motor_off()
        time.sleep(0.5)
        self.close_gate()
        logger.info("Solid doser at home position")
    
    def shutdown(self):
        """
        Safely shutdown the controller.
        """
        logger.info("Shutting down Solid Doser...")
        self.home()  # This calls motor_off() which does GPIO.cleanup()
        self.pca.deinit()
        logger.info("Solid Doser shutdown complete")


def main():
    """Example usage of SolidDoser"""
    print("=== Solid Doser Controller ===")
    print("Hardware: Waveshare PCA9685 HAT + GPIO Relay")
    print("Initializing...")
    
    try:
        # Initialize doser
        doser = SolidDoser(i2c_address=0x40, motor_gpio_pin=17)
        
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

