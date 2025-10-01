# Servo Power and Position Maintenance Guide

Complete guide to powering servos and maintaining positions.

## Power Supply Setup

### Components Needed

1. **External 5V Power Supply**
   - Voltage: 5V DC
   - Current: 3-5A minimum (servos draw ~1A each under load)
   - Recommended: 5V 5A or 5V 10A supply

2. **Connections**
   ```
   Power Supply (5V DC)
   ├─ Positive (+) → PCA9685 V+ terminal
   └─ Negative (-) → PCA9685 GND terminal
   
   IMPORTANT: Also connect PCA9685 GND to Raspberry Pi GND
              (Common ground is essential!)
   ```

### Wiring Diagram

```
┌─────────────────┐
│  5V Power Supply│
│   (3-5A)        │
└────┬───────┬────┘
     │(+5V)  │(GND)
     │       │
     ▼       ▼
┌────────────────────────────┐
│      PCA9685 HAT           │
│  V+  GND  [PWM Channels]   │
│   │   │    3  6  9 ...     │
│   │   └──────────────────┐ │
│   └──────────┐           │ │
└──────────────┼───────────┼─┘
               │           │
               │           └─► Raspberry Pi GND (Common Ground)
               │
          ┌────┴─────┐
          │ Servos   │
          │ (3 units)│
          └──────────┘

Each Servo:
  Red wire    → +5V (from PCA9685 channel)
  Black/Brown → GND (from PCA9685 channel)  
  Yellow/White→ Signal (from PCA9685 channel)
```

### Power Supply Options

#### Option 1: USB Power Supply (Recommended for 3 servos)
```bash
# Use a quality 5V USB power supply
- Voltage: 5V
- Current: 5A (2.4A per port on good chargers)
- Connector: USB-A or USB-C with barrel jack adapter
```

**Products:**
- Raspberry Pi Official 5V 5A USB-C Power Supply
- Anker PowerPort 5V 6A multi-port charger
- Mean Well 5V 10A power supply

#### Option 2: Bench Power Supply
```bash
# Adjustable bench supply
- Set to 5.0V
- Current limit: 5A
- Use banana plug to barrel jack adapter
```

#### Option 3: Battery Pack (Portable)
```bash
# For portable/mobile applications
- 5V USB battery pack (10,000mAh+)
- 6V battery (4x AA) with voltage regulator to 5V
- LiPo battery with 5V UBEC/BEC converter
```

### Connection Steps

1. **DO NOT connect power yet**

2. **Connect PCA9685 to Raspberry Pi**
   ```bash
   # PCA9685 sits on GPIO header
   # Uses I2C pins (SDA, SCL) + 3.3V + GND
   ```

3. **Connect servos to PCA9685**
   ```bash
   Channel 3: Plate lift servo 1
   Channel 6: Plate lift servo 2
   Channel 9: Lid servo
   ```

4. **Connect external 5V supply to PCA9685**
   ```bash
   Power Supply (+) → PCA9685 V+ terminal
   Power Supply (-) → PCA9685 GND terminal
   ```

5. **Connect common ground** ⚠️ CRITICAL
   ```bash
   PCA9685 GND → Raspberry Pi GND
   # Use a jumper wire between any GND pin on Pi and PCA9685 GND
   ```

6. **Power on in sequence**
   ```bash
   1. Power on Raspberry Pi
   2. Power on servo power supply
   3. Run your Python script
   ```

## Position Maintenance

### How Servos Maintain Position

**Servos automatically hold position when powered:**

1. **Active Holding**
   - Servo continuously compares actual vs commanded position
   - Makes micro-adjustments to maintain position
   - Resists external forces trying to move it
   - Draws current even when "stationary"

2. **PWM Signal**
   - PCA9685 continuously sends PWM signal to servo
   - Signal tells servo where to be
   - Servo holds that position until signal changes

3. **No Additional Code Needed**
   ```python
   # Once you set a position, it's maintained automatically
   loader.raise_plate()  # Moves and HOLDS at raised position
   time.sleep(60)        # Still holding after 60 seconds!
   ```

### Position Holding Example

```python
from dose_every_well import PlateLoader
import time

loader = PlateLoader()

# Move to position
print("Moving plate to 45 degrees...")
loader.move_plate_to(45, smooth=True)

# Servo now HOLDS this position automatically
print("Holding position for 30 seconds...")
time.sleep(30)

# Position is still maintained!
plate_pos, lid_pos = loader.get_positions()
print(f"Position after 30 seconds: {plate_pos}° (still at 45°)")

# Change position
print("Moving to new position...")
loader.move_plate_to(90, smooth=True)
# Now holds at 90°
```

### Power Management Strategies

#### Strategy 1: Always On (Default)
```python
# Servos powered continuously
loader = PlateLoader()
loader.raise_plate()
# Holds position indefinitely (draws power continuously)
time.sleep(3600)  # Holds for 1 hour
```

**Pros:**
- Maintains exact position
- Resists external forces
- Immediate response

**Cons:**
- Continuous power draw (~100-300mA per servo at idle)
- Servos may heat up over time
- Higher power consumption

#### Strategy 2: Power Save Mode
```python
# Disable servo output when not moving
# (PCA9685 stops sending PWM signal)

def power_save_mode(loader):
    """Enter power save mode - servos can drift"""
    # Stop PWM output to all channels
    loader.pca.channels[3].duty_cycle = 0
    loader.pca.channels[6].duty_cycle = 0
    loader.pca.channels[9].duty_cycle = 0
    print("Servos unpowered - may drift under load")

def power_restore(loader):
    """Restore servo control"""
    # Re-apply last known positions
    loader._set_plate_servos(loader._plate_position)
    loader.lid_servo.angle = loader._lid_position
    print("Servos re-powered at last positions")
```

**Usage:**
```python
loader.raise_plate()
power_save_mode(loader)
time.sleep(60)  # Servos idle, can drift
power_restore(loader)  # Re-establish position
```

**Pros:**
- Reduced power consumption
- Less heat generation

**Cons:**
- Position may drift under load/gravity
- Brief movement when re-powered
- Position not guaranteed

#### Strategy 3: Intermittent Refresh
```python
# Periodically "refresh" position to maintain hold
import threading

def position_refresh_thread(loader, interval=5):
    """Refresh servo positions periodically"""
    while True:
        # Re-apply current positions
        loader._set_plate_servos(loader._plate_position)
        loader.lid_servo.angle = loader._lid_position
        time.sleep(interval)

# Start refresh thread
refresh = threading.Thread(
    target=position_refresh_thread,
    args=(loader,),
    daemon=True
)
refresh.start()
```

### Current Draw Reference

| State | Current per Servo | Total (3 servos) |
|-------|-------------------|------------------|
| Idle (holding) | 100-300mA | 300-900mA |
| Moving (no load) | 300-500mA | 900-1500mA |
| Moving (under load) | 500-1000mA | 1500-3000mA |
| Stalled | 1000-2000mA | 3000-6000mA |

**Recommendation:** Use 5A supply for safety margin.

## Best Practices

### 1. Proper Grounding
```python
# ALWAYS connect common ground between:
# - Raspberry Pi GND
# - PCA9685 GND  
# - Power supply GND

# Without common ground:
# ✗ Servos may jitter
# ✗ Unreliable position
# ✗ Potential damage to Pi or PCA9685
```

### 2. Adequate Power Supply
```python
# Undersized power supply symptoms:
# - Servos move slowly or jerkily
# - Raspberry Pi reboots during servo movement
# - Voltage drop visible with multimeter

# Solution: Use 5A or larger supply
```

### 3. Power Sequencing
```python
# Recommended power-on sequence:
1. Power Raspberry Pi
2. Wait for Pi to boot
3. Power servo supply
4. Run Python script

# Power-off sequence:
1. Stop Python script (calls loader.shutdown())
2. Power off servo supply
3. Power off Raspberry Pi
```

### 4. Mechanical Load
```python
# Servos hold position better when:
# ✓ Mechanical system is balanced
# ✓ Minimal friction in linkages
# ✓ No excessive loads

# If servos "twitch" or "hunt":
# - Reduce mechanical friction
# - Check servo is not overloaded
# - Verify PWM signal is stable
```

## Troubleshooting

### Servos Don't Hold Position

**Cause 1: Insufficient Power**
```bash
# Check voltage under load
# Should stay above 4.8V

Solution: Use larger power supply
```

**Cause 2: No PWM Signal**
```python
# Verify PWM is being sent
import time
from adafruit_pca9685 import PCA9685
import board, busio

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# Set servo position (should hold)
pca.channels[3].duty_cycle = 0x3000
time.sleep(10)  # Should hold for 10 seconds
```

**Cause 3: Servo Overloaded**
```bash
# Symptoms:
# - Servo makes buzzing noise
# - Gets hot
# - Drifts under load

Solution: 
# - Reduce mechanical load
# - Use stronger servo
# - Add mechanical lock/brake
```

### Servos Jitter/Twitch

**Cause 1: Ground Loop**
```bash
# Ensure common ground between Pi and PCA9685
Solution: Add ground wire between Pi GND and PCA9685 GND
```

**Cause 2: Power Supply Noise**
```bash
# Electrical noise from power supply
Solution: Add capacitor (1000µF) across V+ and GND near PCA9685
```

**Cause 3: PWM Frequency**
```python
# Some servos prefer different frequencies
# Try 50Hz (default) or 60Hz

loader.pca.frequency = 50  # Standard
# or
loader.pca.frequency = 60  # Alternative
```

### Raspberry Pi Reboots During Movement

**Cause: Voltage Drop**
```bash
# When servos move, they draw current
# This causes voltage drop on Pi's power line

Solution:
1. Use separate power supplies (Pi and servos)
2. Use larger power supply (10A)
3. Add large capacitor (2200µF+) near Pi
```

## Advanced: Position Holding with Mechanical Lock

For long-term position holding without continuous power:

```python
class PlateLoaderWithLock(PlateLoader):
    """Extended version with mechanical lock support"""
    
    LOCK_SERVO_CHANNEL = 12  # Additional servo for lock
    
    def __init__(self):
        super().__init__()
        self.lock_servo = servo.Servo(
            self.pca.channels[self.LOCK_SERVO_CHANNEL]
        )
    
    def engage_lock(self):
        """Engage mechanical lock to hold position"""
        print("Engaging mechanical lock...")
        self.lock_servo.angle = 90  # Lock engaged
        time.sleep(0.5)
        
        # Can now power down main servos
        self.power_save_mode()
        print("Position locked mechanically")
    
    def release_lock(self):
        """Release mechanical lock"""
        print("Releasing mechanical lock...")
        
        # Power up main servos first
        self.power_restore()
        time.sleep(0.2)
        
        # Then release lock
        self.lock_servo.angle = 0  # Lock released
        print("Lock released")
```

## Code Examples

### Example 1: Long-term Hold
```python
loader = PlateLoader()

# Move to position and hold indefinitely
loader.raise_plate()
loader.open_lid()

print("Holding position...")
try:
    while True:
        time.sleep(1)
        # Position is maintained automatically
except KeyboardInterrupt:
    print("Shutting down...")
    loader.shutdown()
```

### Example 2: Monitor Position
```python
import time

loader = PlateLoader()
loader.move_plate_to(45)

print("Monitoring position for 60 seconds...")
for i in range(60):
    plate_pos, lid_pos = loader.get_positions()
    print(f"[{i}s] Plate: {plate_pos}°, Lid: {lid_pos}°")
    time.sleep(1)
```

### Example 3: With Power Management
```python
def power_aware_operation(loader):
    """Operation with power saving"""
    
    # Active operation
    print("Moving to position...")
    loader.raise_plate()
    loader.open_lid()
    
    # Long idle period
    print("Entering power save (10 minutes)...")
    # Optional: Add mechanical brake here
    time.sleep(600)
    
    # Resume operation
    print("Restoring power...")
    # Servos automatically hold last position
    
    # Continue operations
    loader.close_lid()
    loader.lower_plate()

loader = PlateLoader()
power_aware_operation(loader)
loader.shutdown()
```

## Summary

✅ **Power Supply:**
- Use external 5V 5A supply
- Connect V+ and GND to PCA9685
- Connect common ground to Raspberry Pi

✅ **Position Holding:**
- Servos hold automatically when powered
- No additional code needed
- Continuous power draw (small)

✅ **Best Practices:**
- Adequate power supply
- Common ground
- Proper power sequencing
- Monitor for overloading

For most applications, simply setting a servo position is enough - it will hold that position automatically as long as it's powered! 🎯

