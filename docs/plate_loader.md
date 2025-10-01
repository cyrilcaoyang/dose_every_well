# Plate Loader Module

Control motorized well plate loading system with synchronized servo motors.

## Hardware Requirements

- **Raspberry Pi 5** (or Pi 3/4)
- **PCA9685 16-channel PWM HAT**
- **3x 5V Servo Motors**:
  - Channel 3: Plate lift motor 1
  - Channel 6: Plate lift motor 2 (synchronized with channel 3)
  - Channel 9: Lid open/close motor
- **Power supply** for servos (5V, adequate amperage)

## Installation

### On Raspberry Pi

```bash
# Install with Raspberry Pi dependencies
pip install -e ".[rpi]"

# Or install dependencies manually
pip install adafruit-circuitpython-pca9685 adafruit-circuitpython-motor
```

### Enable I2C

```bash
# Enable I2C interface
sudo raspi-config
# → Interface Options → I2C → Enable

# Verify I2C is enabled
ls /dev/i2c-*

# Install i2c-tools (optional, for debugging)
sudo apt install i2c-tools
i2cdetect -y 1  # Should show device at 0x40
```

## Quick Start

### Basic Usage

```python
from dose_every_well import PlateLoader

# Initialize
loader = PlateLoader()

# Raise plate
loader.raise_plate(smooth=True)

# Open lid
loader.open_lid(smooth=True)

# Close lid
loader.close_lid(smooth=True)

# Lower plate
loader.lower_plate(smooth=True)

# Shutdown
loader.shutdown()
```

### Load/Unload Sequences

```python
# Full loading sequence
loader.load_sequence()
# 1. Opens lid
# 2. Raises plate
# 3. Waits for user to insert plate
# 4. Lowers plate
# 5. Closes lid

# Full unloading sequence
loader.unload_sequence()
# 1. Opens lid
# 2. Raises plate
# 3. Waits for user to remove plate
# 4. Lowers plate
# 5. Closes lid
```

## Demo Script

Run the interactive demo:

```bash
python demo/plate_loader_demo.py
```

Features:
- Interactive menu control
- Manual servo positioning
- Full load/unload sequences
- Calibration routine
- Position monitoring

## API Reference

### PlateLoader Class

#### Initialization

```python
loader = PlateLoader(i2c_address=0x40, frequency=50)
```

**Parameters:**
- `i2c_address`: PCA9685 I2C address (default: 0x40)
- `frequency`: PWM frequency in Hz (default: 50 for servos)

#### Plate Control

**`raise_plate(degrees=None, smooth=True)`**

Raise the well plate.

- `degrees`: Amount to raise (None = full raise)
- `smooth`: Smooth movement if True

**`lower_plate(degrees=None, smooth=True)`**

Lower the well plate.

- `degrees`: Amount to lower (None = full lower)
- `smooth`: Smooth movement if True

**`move_plate_to(angle, smooth=True)`**

Move plate to specific angle (0-90°).

#### Lid Control

**`open_lid(smooth=True)`**

Open the lid to full open position.

**`close_lid(smooth=True)`**

Close the lid to closed position.

**`rotate_lid(angle, smooth=True)`**

Rotate lid to specific angle (0-90°).

#### Sequences

**`load_sequence()`**

Execute complete plate loading sequence.

**`unload_sequence()`**

Execute complete plate unloading sequence.

**`calibrate()`**

Run calibration routine to test servo ranges.

**`home()`**

Return all servos to home position (plate down, lid closed).

#### Status

**`get_positions()`**

Returns: `(plate_angle, lid_angle)` tuple

**`shutdown()`**

Safely shutdown the controller.

## Configuration

### Servo Angle Limits

Adjust in `plate_loader.py` if needed:

```python
class PlateLoader:
    # Plate positions
    PLATE_DOWN_ANGLE = 0      # Fully lowered
    PLATE_UP_ANGLE = 90       # Fully raised
    
    # Lid positions
    LID_CLOSED_ANGLE = 0      # Closed
    LID_OPEN_ANGLE = 90       # Open
    
    # Movement speed
    DEFAULT_MOVE_SPEED = 20   # Degrees per step
    DEFAULT_MOVE_DELAY = 0.05 # Seconds between steps
```

### Servo Pulse Width

Adjust pulse width for your specific servos:

```python
servo.Servo(
    channel,
    min_pulse=500,   # Microseconds
    max_pulse=2500   # Microseconds
)
```

## Hardware Setup

### Wiring

```
PCA9685 HAT → Raspberry Pi 5
└─ Connects via GPIO header (I2C pins)

Servo Motors → PCA9685 Channels:
├─ Channel 3: Plate lift motor 1 (Yellow/White=Signal, Red=5V, Brown/Black=GND)
├─ Channel 6: Plate lift motor 2 (synchronized)
└─ Channel 9: Lid motor

Power Supply:
└─ 5V to PCA9685 V+ and GND (separate from Pi if high current)
```

### Power Considerations

- **Each servo**: ~500-1000mA under load
- **Total**: Up to 3A for all servos
- **Recommendation**: Use external 5V power supply
- **Connect grounds**: Pi GND, PCA9685 GND, and power supply GND

### I2C Address

Default PCA9685 address: `0x40`

Change address with solder jumpers if needed:
- A0: +0x01
- A1: +0x02
- A2: +0x04
- A3: +0x08
- A4: +0x10
- A5: +0x20

## Troubleshooting

### I2C Not Detected

```bash
# Check I2C is enabled
ls /dev/i2c-*

# Scan for devices
i2cdetect -y 1

# Should show device at 0x40
```

If not detected:
- Enable I2C in raspi-config
- Check HAT is seated properly
- Verify power connections

### Servos Not Moving

1. **Check power supply**
   - Adequate voltage (5V)
   - Sufficient current (3A+)

2. **Check connections**
   - Signal wires on correct channels
   - Power and ground connected

3. **Test individual channel**
   ```python
   from adafruit_pca9685 import PCA9685
   import board
   import busio
   
   i2c = busio.I2C(board.SCL, board.SDA)
   pca = PCA9685(i2c)
   pca.frequency = 50
   
   # Test channel 3
   pca.channels[3].duty_cycle = 0x3000
   ```

### Jerky Movement

- Increase `DEFAULT_MOVE_DELAY`
- Decrease `DEFAULT_MOVE_SPEED`
- Check power supply stability

### Import Errors

```bash
# Install Raspberry Pi dependencies
pip install -e ".[rpi]"

# Or individually
pip install adafruit-circuitpython-pca9685
pip install adafruit-circuitpython-motor
```

## Safety

⚠️ **Important Safety Notes:**

- Test movements slowly first
- Ensure no fingers/objects in mechanism
- Use appropriate power supply
- Don't exceed servo angle limits
- Monitor for overheating
- Have emergency stop accessible

## Examples

### Example 1: Simple Load/Unload

```python
from dose_every_well import PlateLoader

loader = PlateLoader()

# Load a plate
print("Loading plate...")
loader.open_lid()
time.sleep(1)
loader.raise_plate()
input("Insert plate, then press Enter")
loader.lower_plate()
loader.close_lid()

# Unload the plate
print("Unloading plate...")
loader.open_lid()
loader.raise_plate()
input("Remove plate, then press Enter")
loader.lower_plate()
loader.close_lid()

loader.shutdown()
```

### Example 2: Partial Movements

```python
# Raise plate by 45 degrees
loader.raise_plate(degrees=45)

# Open lid halfway
loader.rotate_lid(angle=45)

# Check positions
plate_angle, lid_angle = loader.get_positions()
print(f"Plate: {plate_angle}°, Lid: {lid_angle}°")
```

### Example 3: Custom Sequence

```python
def custom_sequence(loader):
    """Custom loading sequence with delays"""
    print("Opening lid slowly...")
    loader.rotate_lid(30)
    time.sleep(0.5)
    loader.rotate_lid(60)
    time.sleep(0.5)
    loader.open_lid()
    
    print("Raising plate...")
    loader.raise_plate()
    
    input("Place plate and press Enter")
    
    print("Lowering plate slowly...")
    loader.lower_plate()
    
    print("Closing lid...")
    loader.close_lid()
```

## Integration with CNC

Combine with CNC controller for automated dispensing:

```python
from dose_every_well import CNC_Controller, PlateLoader, load_config, find_port

# Initialize both systems
cnc_config = load_config("cnc_settings.yaml", "Genmitsu 4040 PRO")
cnc = CNC_Controller(find_port(), cnc_config)
loader = PlateLoader()

# Load plate
loader.load_sequence()

# Dispense to wells
for row in range(8):
    for col in range(12):
        x = 10 + col * 9
        y = 10 + row * 9
        cnc.move_to_point(x, y)
        cnc.execute_movement()
        # Dispense here

# Unload plate
loader.unload_sequence()

# Cleanup
loader.shutdown()
```

