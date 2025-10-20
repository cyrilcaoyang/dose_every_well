# Solid Doser Controller

The `SolidDoser` class provides control over a solid material dispensing mechanism using a Waveshare PCA9685 HAT for servo control and a GPIO-controlled relay for DC motor on/off control.

## Hardware Setup

### Required Components

1. **Waveshare PCA9685 HAT**
   - 16-channel PWM controller
   - I2C default address: 0x40 (configurable via A0-A4 jumpers)
   - Servo pins labeled 3-8

2. **Servo Motor** (Gate Control)
   - Connected to Channel 0 on HAT
   - Controls hopper gate/valve
   - 0° = fully closed, 90° = fully open
   - **Note:** Channels 3, 6, 9 reserved for plate_loader

3. **5V Relay Module**
   - Connected to GPIO 17 (BCM) / Physical Pin 11
   - Controls DC motor ON/OFF
   - VCC: 5V from Pi
   - GND: Common ground
   - IN: GPIO 17

4. **DC Motor** (Auger/Feeder)
   - Connected via relay
   - Simple ON/OFF control (no speed control)

5. **5V 5A Power Supply** (Single plug)
   - Powers Raspberry Pi 5 via USB-C
   - Powers servos via PCA9685
   - Powers DC motor via relay
   - Powers relay module

### Wiring Diagram

```
5V 5A Power Supply
    │
    ├─→ Pi 5 USB-C port (powers Pi)
    │
    └─→ Distribution (from Pi or supply)
         │
         ├─→ PCA9685 V+ (servo power)
         │
         ├─→ Relay VCC (5V)
         │
         └─→ Motor + (via relay COM → NO)
         
Common Ground:
    Power Supply GND ──┬── Pi GND
                       ├── PCA9685 GND
                       ├── Relay GND
                       └── Motor -

Raspberry Pi 5 Connections:
    GPIO 2 (Pin 3)  → PCA9685 SDA
    GPIO 3 (Pin 5)  → PCA9685 SCL
    GPIO 17 (Pin 11) → Relay IN
    GND (Pin 6)     → Common ground
```

### Physical Connections

**Waveshare PCA9685 HAT:**
- Mounts on Pi GPIO header
- Servo → Channel 0 on HAT (first servo connector)
- I2C: Auto-connected via GPIO header
- **Channel allocation:**
  - Channel 0: Solid doser gate servo
  - Channels 1-2: Available for expansion
  - Channels 3, 6, 9: Reserved for plate_loader (lift servos + lid)

**Relay Module:**
- VCC → 5V (Pi Pin 2 or 4)
- GND → GND (Pi Pin 6)
- IN → GPIO 17 (Pi Pin 11)
- COM → +5V from power
- NO → Motor +
- Motor - → GND

## Installation

```bash
# Install required Raspberry Pi libraries
pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-motor RPi.GPIO

# Enable I2C on Raspberry Pi
sudo raspi-config
# Navigate to: Interfacing Options -> I2C -> Yes
sudo reboot
```

## Basic Usage

```python
from dose_every_well import SolidDoser

# Initialize the doser
doser = SolidDoser(i2c_address=0x40, motor_gpio_pin=17)  # 0x40 is Waveshare default

# Simple dispense (3 seconds)
doser.dispense(duration=3.0)

# Dispense with partial gate opening
doser.dispense(duration=5.0, gate_angle=45)

# Cleanup
doser.shutdown()
```

## Power-Safe Operation

The module is designed for **sequential operation** to work within a 5V 5A power budget:

1. **Motor starts first** → Reaches steady state (low current)
2. **Servos move one at a time** → Minimizes current spikes
3. **Built-in delays** → Ensures operations complete before next step

### Power Budget

```
Raspberry Pi 5:      ~2.5-3A (typical)
DC Motor (steady):   ~0.5-1A
1 Servo moving:      ~0.5A
Relay:               ~15mA
--------------------------------
Total:               ~4-4.5A ✅ (within 5A limit)
```

## API Reference

### Initialization

```python
SolidDoser(i2c_address=0x40, motor_gpio_pin=17, frequency=50)
```

**Parameters:**
- `i2c_address` (int): I2C address of PCA9685 (default 0x40 for Waveshare)
- `motor_gpio_pin` (int): GPIO pin (BCM) for relay control (default 17)
- `frequency` (int): PWM frequency in Hz (default 50 for servos)

### Motor Control

#### `motor_on()`
Turn DC motor ON via relay. Includes automatic startup delay.

#### `motor_off()`
Turn DC motor OFF via relay.

### Gate Control

#### `open_gate(angle=None)`
Open the hopper gate.

**Parameters:**
- `angle` (float, optional): Specific angle (None = fully open to 90°)

#### `close_gate()`
Close the hopper gate to 0°.

#### `set_gate_angle(angle)`
Set gate to specific angle for precise flow control.

**Parameters:**
- `angle` (float): Target angle (0-90 degrees)

### High-Level Operations

#### `dispense(duration, gate_angle=None)`
Execute complete dispense sequence.

**Parameters:**
- `duration` (float): Dispensing time in seconds
- `gate_angle` (float, optional): Gate angle (None = fully open)

**Process:**
1. Start motor → wait for steady state
2. Open gate
3. Dispense for duration
4. Close gate
5. Stop motor

**Example:**
```python
# Standard dispense (5 seconds)
doser.dispense(duration=5.0)

# Precise low-flow dispense
doser.dispense(duration=3.0, gate_angle=30)
```

#### `purge(duration=2.0)`
Run motor with gate open to clear material.

**Parameters:**
- `duration` (float): Purge duration in seconds

### Status and Maintenance

#### `get_status()`
Get current status.

**Returns:**
```python
{
    "gate_position": 90,      # Current angle
    "motor_running": True,    # Motor state
    "is_dispensing": True     # Active dispensing
}
```

#### `calibrate()`
Run calibration routine to test all components.

#### `home()`
Return to safe home position (gate closed, motor stopped).

#### `shutdown()`
Safely shutdown the controller. **Always call this when done!**

## Usage Examples

### Example 1: Basic Dispensing

```python
from dose_every_well import SolidDoser

doser = SolidDoser()

try:
    # Dispense for 5 seconds
    doser.dispense(duration=5.0)
    
finally:
    doser.shutdown()
```

### Example 2: Multiple Dispenses

```python
from dose_every_well import SolidDoser
import time

doser = SolidDoser()

try:
    # Dispense into multiple wells
    for well in range(96):
        print(f"Dispensing into well {well + 1}")
        doser.dispense(duration=2.0, gate_angle=60)
        time.sleep(0.5)  # Brief pause between wells
    
finally:
    doser.shutdown()
```

### Example 3: Integration with CNC and Plate Loader

```python
from dose_every_well import CNC_Controller, PlateLoader, SolidDoser, load_config, find_port
import time

# Initialize all controllers
cnc = CNC_Controller(find_port(), load_config("cnc_settings.yaml", "Genmitsu 4040 PRO"))
plate_loader = PlateLoader(i2c_address=0x40)  # Waveshare default
solid_doser = SolidDoser(i2c_address=0x40)    # Waveshare default

try:
    # Load plate
    plate_loader.load_sequence()
    
    # Dispense into each well
    well_spacing = 9.0  # mm
    for row in range(8):
        for col in range(12):
            # Move to well position
            x = 10.0 + col * well_spacing
            y = 10.0 + row * well_spacing
            cnc.move_to_point(x, y)
            cnc.execute_movement()
            
            # Dispense
            solid_doser.dispense(duration=2.0)
            
            # Brief pause
            time.sleep(0.5)
    
    # Unload plate
    plate_loader.unload_sequence()
    
finally:
    solid_doser.shutdown()
    plate_loader.shutdown()
    cnc.disconnect()
```

### Example 4: Testing Different Flow Rates

```python
from dose_every_well import SolidDoser

doser = SolidDoser()

try:
    # Test different gate angles
    for angle in [20, 40, 60, 80, 90]:
        print(f"Testing gate angle: {angle}°")
        doser.dispense(duration=3.0, gate_angle=angle)
        # Weigh or measure output here
        time.sleep(2)
    
finally:
    doser.shutdown()
```

## Demo Script

Run the interactive demo:

```bash
cd demo
python3 solid_doser_demo.py
```

The demo includes:
1. Basic controls (gate & motor)
2. Automated dispense sequences
3. Gate flow control
4. Purge function
5. Interactive manual mode

## Troubleshooting

### Motor doesn't turn on

1. **Check relay LED** - Should light when GPIO 17 is HIGH
2. **Verify power supply** - Must be connected and adequate current
3. **Check relay wiring**:
   - VCC → 5V
   - GND → Ground
   - IN → GPIO 17
4. **Test relay manually**:
   ```python
   import RPi.GPIO as GPIO
   GPIO.setmode(GPIO.BCM)
   GPIO.setup(17, GPIO.OUT)
   GPIO.output(17, GPIO.HIGH)  # Relay should click
   ```

### Servo doesn't move

1. **Verify I2C connection**:
   ```bash
   sudo i2cdetect -y 1
   # Should show device at 0x40 (Waveshare default)
   # Or 0x70 if jumpers are configured differently
   ```
2. **Check servo is on Channel 0** (first servo connector on HAT)
3. **Verify servo power** - PCA9685 V+ connected to 5V

### System brownout / Pi reboots

- **Power supply insufficient** - Upgrade to 5V 10A supply
- **Too many simultaneous operations** - Code should prevent this
- **Motor stall** - Check for blockages

### I2C errors

```bash
# Reset I2C bus
sudo modprobe -r i2c_bcm2835
sudo modprobe i2c_bcm2835

# Check device
sudo i2cdetect -y 1
```

## Configuration Constants

You can adjust these in the code:

```python
# Servo angles
GATE_CLOSED_ANGLE = 0      # Fully closed
GATE_OPEN_ANGLE = 90       # Fully open

# Power-safe delays
MOTOR_STARTUP_DELAY = 0.5  # Motor steady state wait
SERVO_MOVE_DELAY = 0.3     # Servo movement completion
```

## Safety Considerations

1. **Always call `shutdown()`** when done
2. **Monitor first dispenses** to verify proper operation
3. **Start with low gate angles** (20-30°) when testing
4. **Keep emergency stop accessible**
5. **Use adequate power supply** (5A minimum, 10A recommended)

## Related Documentation

- [Plate Loader Guide](plate_loader.md)
- [CNC Controller API](api_reference.md)
- [Troubleshooting Guide](troubleshooting.md)

