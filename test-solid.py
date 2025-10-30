#!/usr/bin/env python3
"""
Solid Doser Controller (Adafruit-free)
Drives PCA9685 directly via I2C using smbus2. Works on Python 3.13+.

Hardware:
- Raspberry Pi 5
- Waveshare PCA9685 HAT (I2C default address 0x40)
- Servo on channel 0
- 5V relay on GPIO17
"""

import time
import logging
from typing import Optional

import RPi.GPIO as GPIO
from smbus2 import SMBus

# -------- Minimal PCA9685 driver (no Adafruit) --------
class PCA9685Lite:
    _MODE1      = 0x00
    _MODE2      = 0x01
    _PRESCALE   = 0xFE
    _LED0_ON_L  = 0x06

    _RESTART    = 0x80
    _SLEEP      = 0x10
    _AI         = 0x20  # Auto-increment
    _OUTDRV     = 0x04

    def __init__(self, bus: int = 1, address: int = 0x40, frequency: int = 50):
        self.bus_no = bus
        self.address = address
        self.bus = SMBus(bus)
        # MODE2: totem pole, MODE1: auto-increment
        self._write8(self._MODE2, self._OUTDRV)
        self._write8(self._MODE1, self._AI)
        self.set_pwm_freq(frequency)

    def _write8(self, reg: int, val: int):
        self.bus.write_byte_data(self.address, reg, val & 0xFF)

    def _read8(self, reg: int) -> int:
        return self.bus.read_byte_data(self.address, reg)

    def set_pwm_freq(self, freq_hz: int):
        """Set PWM frequency; typical for servos is ~50Hz."""
        # prescale = round(25MHz / (4096 * freq)) - 1
        prescale = int(round(25000000.0 / (4096.0 * freq_hz)) - 1)
        oldmode = self._read8(self._MODE1)
        sleep = (oldmode & ~self._RESTART) | self._SLEEP
        self._write8(self._MODE1, sleep)           # go to sleep
        self._write8(self._PRESCALE, prescale)     # set prescale
        self._write8(self._MODE1, oldmode)         # wake
        time.sleep(0.005)
        self._write8(self._MODE1, oldmode | self._RESTART | self._AI)

    def set_pwm(self, channel: int, on: int, off: int):
        """Set 12-bit on/off counts for a channel (0..4095)."""
        base = self._LED0_ON_L + 4 * channel
        self._write8(base + 0, on & 0xFF)
        self._write8(base + 1, (on >> 8) & 0x0F)
        self._write8(base + 2, off & 0xFF)
        self._write8(base + 3, (off >> 8) & 0x0F)

    def set_pwm_us(self, channel: int, pulse_us: float, freq_hz: int):
        """Convenience: set PWM by microseconds at given frequency."""
        period_us = 1_000_000.0 / freq_hz
        # 12-bit resolution across the period
        ticks = int(round((pulse_us / period_us) * 4096.0))
        ticks = max(0, min(4095, ticks))
        self.set_pwm(channel, 0, ticks)

    def deinit(self):
        try:
            self.bus.close()
        except Exception:
            pass

# -------- Tiny servo helper (angle -> pulse width) --------
class ServoLite:
    def __init__(self, pca: PCA9685Lite, channel: int, freq_hz: int = 50,
                 min_pulse: int = 500, max_pulse: int = 2500):
        self.pca = pca
        self.channel = channel
        self.freq_hz = freq_hz
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        self._angle = None

    @property
    def angle(self) -> Optional[float]:
        return self._angle

    @angle.setter
    def angle(self, degrees: float):
        # clamp 0..180
        degrees = max(0.0, min(180.0, float(degrees)))
        # linear map to pulse width
        pulse = self.min_pulse + (self.max_pulse - self.min_pulse) * (degrees / 180.0)
        self.pca.set_pwm_us(self.channel, pulse, self.freq_hz)
        self._angle = degrees

# -------- Your original controller, lightly adapted --------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SolidDoser:
    # Servo channel assignment
    GATE_SERVO = 0

    # GPIO pin for relay control
    MOTOR_RELAY_PIN = 17  # BCM

    # Relay trigger type
    LOW_LEVEL_TRIGGER = True  # LOW=ON

    # Servo limits / mapping
    SERVO_FULLY_EXTENDED = 30
    SERVO_CONTACT_POINT  = 65
    SERVO_FULLY_CONTRACTED = 85

    GATE_MAX_EXTENSION   = 35
    GATE_CONTACT         = 0
    GATE_MAX_CONTRACTION = -20

    MOTOR_STARTUP_DELAY = 0.5
    SERVO_MOVE_DELAY    = 0.3

    def __init__(self, i2c_address: int = 0x40, motor_gpio_pin: int = 17, frequency: int = 50):
        logger.info("Initializing Solid Doser (no Adafruit deps)...")

        # GPIO setup
        self.MOTOR_RELAY_PIN = motor_gpio_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.MOTOR_RELAY_PIN, GPIO.OUT)
        initial_state = GPIO.HIGH if self.LOW_LEVEL_TRIGGER else GPIO.LOW
        GPIO.output(self.MOTOR_RELAY_PIN, initial_state)

        # PCA9685 + servo
        self.pca = PCA9685Lite(bus=1, address=i2c_address, frequency=frequency)
        self.pca_frequency = frequency
        self.gate_servo = ServoLite(self.pca, self.GATE_SERVO, freq_hz=frequency,
                                    min_pulse=500, max_pulse=2500)

        # internal state
        self._gate_position = self.GATE_MAX_CONTRACTION
        self._motor_running = False

        self.close_gate()

        logger.info("Solid Doser initialized")
        logger.info(f"  Gate servo channel: {self.GATE_SERVO}")
        relay_type = "Low-level trigger" if self.LOW_LEVEL_TRIGGER else "High-level trigger"
        logger.info(f"  Motor relay: GPIO {self.MOTOR_RELAY_PIN} ({relay_type})")
        logger.info(f"  I2C address: 0x{i2c_address:02X}")

    def _gate_to_servo_angle(self, gate_position: float) -> float:
        gate_position = max(self.GATE_MAX_CONTRACTION, min(gate_position, self.GATE_MAX_EXTENSION))
        return self.SERVO_CONTACT_POINT - gate_position

    def _servo_to_gate_angle(self, servo_angle: float) -> float:
        return self.SERVO_CONTACT_POINT - servo_angle

    def motor_on(self):
        if not self._motor_running:
            logger.info("Starting motor...")
            on_state = GPIO.LOW if self.LOW_LEVEL_TRIGGER else GPIO.HIGH
            GPIO.output(self.MOTOR_RELAY_PIN, on_state)
            self._motor_running = True
            logger.info(f"Waiting {self.MOTOR_STARTUP_DELAY}s for motor steady state...")
            time.sleep(self.MOTOR_STARTUP_DELAY)

    def motor_off(self):
        if self._motor_running:
            logger.info("Stopping motor...")
            off_state = GPIO.HIGH if self.LOW_LEVEL_TRIGGER else GPIO.LOW
            GPIO.output(self.MOTOR_RELAY_PIN, off_state)
            self._motor_running = False

    def open_gate(self, gate_position: Optional[float] = None):
        target = gate_position if gate_position is not None else self.GATE_MAX_EXTENSION
        target = max(self.GATE_CONTACT, min(target, self.GATE_MAX_EXTENSION))
        servo_angle = self._gate_to_servo_angle(target)
        logger.info(f"Opening gate to {target} (servo {servo_angle}°)")
        self.gate_servo.angle = servo_angle
        self._gate_position = target
        time.sleep(self.SERVO_MOVE_DELAY)

    def close_gate(self):
        target = self.GATE_MAX_CONTRACTION
        servo_angle = self._gate_to_servo_angle(target)
        logger.info(f"Closing gate to {target} (servo {servo_angle}°)")
        self.gate_servo.angle = servo_angle
        self._gate_position = target
        time.sleep(self.SERVO_MOVE_DELAY)

    def set_gate_position(self, gate_position: float):
        target = max(self.GATE_MAX_CONTRACTION, min(gate_position, self.GATE_MAX_EXTENSION))
        servo_angle = self._gate_to_servo_angle(target)
        logger.info(f"Setting gate to {target} (servo {servo_angle}°)")
        self.gate_servo.angle = servo_angle
        self._gate_position = target
        time.sleep(self.SERVO_MOVE_DELAY)

    def dispense(self, duration: float, gate_position: Optional[float] = None):
        logger.info(f"Starting dispense: {duration}s")
        try:
            self.motor_on()
            if gate_position is not None:
                self.open_gate(gate_position)
            else:
                self.open_gate()
            logger.info(f"Dispensing for {duration}s...")
            time.sleep(duration)
        finally:
            logger.info("Stopping dispense...")
            self.close_gate()
            self.motor_off()
        logger.info("Dispense complete")

    def purge(self, duration: float = 2.0):
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
        logger.info("Starting solid doser calibration...")
        self.close_gate()
        time.sleep(1)
        self.set_gate_position(self.GATE_CONTACT)
        time.sleep(1)
        self.set_gate_position(15)
        time.sleep(1)
        self.open_gate()
        time.sleep(1)
        self.close_gate()
        logger.info("Testing motor (3 seconds)...")
        self.motor_on()
        time.sleep(3)
        self.motor_off()
        logger.info("Calibration complete")

    def get_status(self) -> dict:
        return {
            "gate_position": self._gate_position,
            "motor_running": self._motor_running,
            "is_dispensing": self._motor_running and self._gate_position > self.GATE_CONTACT
        }

    def home(self):
        logger.info("Homing solid doser...")
        self.motor_off()
        self.close_gate()
        logger.info("Home position reached")

    def shutdown(self):
        logger.info("Shutting down Solid Doser...")
        self.home()
        try:
            self.pca.deinit()
        finally:
            GPIO.cleanup()
        logger.info("Shutdown complete")

def main():
    print("=== Solid Doser Controller ===")
    print("Hardware: Waveshare PCA9685 HAT + GPIO Relay")
    print("Initializing...")

    try:
        # Use Waveshare default address 0x40
        doser = SolidDoser(i2c_address=0x40, motor_gpio_pin=17)

        print("\n1. Running calibration...")
        doser.calibrate()

        print("\n2. Testing dispense function...")
        choice = input("Run dispense test (Y/N)? ").strip().upper()
        if choice == 'Y':
            duration = float(input("Duration (seconds): "))
            doser.dispense(duration=duration)

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
