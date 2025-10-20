# Complete Wiring Guide

This guide shows how to wire the Raspberry Pi 5, Waveshare PCA9685 HAT, servos, relay module, and DC motor for the automated dispensing system.

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│              Complete System Diagram                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  5V 5A Power Supply                                      │
│      │                                                    │
│      ├──→ Raspberry Pi 5 (USB-C)                        │
│      │                                                    │
│      └──→ Power Distribution                             │
│           │                                               │
│           ├──→ PCA9685 V+ (servos)                      │
│           ├──→ Relay VCC (5V)                           │
│           └──→ Motor + (via relay)                      │
│                                                           │
│  Common Ground: All GND connected together               │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Component List

### Required Hardware

| Component | Quantity | Notes |
|-----------|----------|-------|
| Raspberry Pi 5 | 1 | Main controller |
| Waveshare PCA9685 HAT | 1 | I2C servo driver (0x40) |
| 5V Servo Motors | 4 | Gate (Ch0) + 2×Lift (Ch3,6) + Lid (Ch9) |
| 5V Relay Module | 1 | Single channel, GPIO 17 |
| DC Motor (6-12V) | 1 | Auger/feeder motor |
| 5V 5A Power Supply | 1 | Single plug for everything |
| Jumper Wires | ~20 | Male-female, various lengths |
| (Optional) 100µF Capacitor | 1 | Motor noise filtering |

### Tools Needed

- Small Phillips screwdriver (for screw terminals)
- Wire strippers
- Multimeter (for testing)

## Step-by-Step Wiring

### Step 1: Mount the Waveshare PCA9685 HAT

```
1. Power OFF Raspberry Pi
2. Align HAT with 40-pin GPIO header
3. Gently press down until fully seated
4. Verify all 40 pins are connected
```

**Automatic Connections via GPIO Header:**
- 3.3V (Pin 1) → HAT VCC (logic power)
- GND (Pin 6, 9, 14, etc.) → HAT GND
- GPIO 2/SDA (Pin 3) → HAT SDA (I2C data)
- GPIO 3/SCL (Pin 5) → HAT SCL (I2C clock)

### Step 2: Connect Servos to PCA9685 HAT

Each servo has 3 wires (standard color coding):
- **Brown/Black** = Ground (GND)
- **Red** = Power (5V)
- **Orange/Yellow/White** = Signal (PWM)

**Servo Connections:**

```
Servo #1 (Solid Doser Gate):
  ├─ Brown  → Channel 0 GND
  ├─ Red    → Channel 0 5V
  └─ Orange → Channel 0 Signal

Servo #2 (Plate Lift 1):
  ├─ Brown  → Channel 3 GND
  ├─ Red    → Channel 3 5V
  └─ Orange → Channel 3 Signal

Servo #3 (Plate Lift 2):
  ├─ Brown  → Channel 6 GND
  ├─ Red    → Channel 6 5V
  └─ Orange → Channel 6 Signal

Servo #4 (Plate Lid):
  ├─ Brown  → Channel 9 GND
  ├─ Red    → Channel 9 5V
  └─ Orange → Channel 9 Signal
```

**Channel Summary:**
```
┌─────────────────────────────────────┐
│   Waveshare PCA9685 HAT Channels    │
├─────────────────────────────────────┤
│ Ch0:  ✅ Solid Doser Gate          │
│ Ch1:  ⬜ Available                 │
│ Ch2:  ⬜ Available                 │
│ Ch3:  ✅ Plate Loader Lift 1       │
│ Ch4:  ⬜ Available                 │
│ Ch5:  ⬜ Available                 │
│ Ch6:  ✅ Plate Loader Lift 2       │
│ Ch7:  ⬜ Available                 │
│ Ch8:  ⬜ Available                 │
│ Ch9:  ✅ Plate Loader Lid          │
│ Ch10-15: ⬜ Available              │
└─────────────────────────────────────┘
```

### Step 3: Connect 5V Relay Module

The relay module has 6 connections:

#### Control Side (connects to Pi):
```
Relay Module          Raspberry Pi 5
─────────────────────────────────────
VCC (power)      →    5V (Pin 2 or 4)
GND (ground)     →    GND (Pin 6)
IN (signal)      →    GPIO 17 (Pin 11)
```

#### Power Side (switches motor power):
```
Relay Terminal      Connection
───────────────────────────────
COM (common)    →   +5V from power supply
NO (normally open) → Motor + (red wire)
NC (normally closed)  [leave empty]
```

**Physical Layout:**
```
┌────────────────────────────┐
│    5V Relay Module         │
├────────────────────────────┤
│                            │
│  Control Side:             │
│  [VCC] [GND] [IN]         │
│    │     │     │           │
│    │     │     └─ GPIO 17  │
│    │     └─────── GND      │
│    └─────────────── 5V     │
│                            │
│  Power Side:               │
│  [COM] [NO] [NC]          │
│    │     │    └─ empty    │
│    │     └───── Motor +   │
│    └────────────── +5V    │
│                            │
└────────────────────────────┘
```

### Step 4: Connect DC Motor

```
DC Motor          Connection
─────────────────────────────────────
Motor + (red)    → Relay NO terminal
Motor - (black)  → Power supply GND
```

**Optional: Add noise filtering capacitor**
```
Across motor terminals:
Motor + ───┤├─── Motor -
        100µF
       (16V+)
```

### Step 5: Power Supply Connections

**5V 5A Power Supply Distribution:**

```
Power Supply
    │
    ├─ +5V ──┬─→ Raspberry Pi 5 (USB-C port)
    │        │
    │        ├─→ PCA9685 V+ terminal (servo power)
    │        │
    │        ├─→ Relay VCC
    │        │
    │        └─→ Relay COM (motor switching)
    │
    └─ GND ──┬─→ Pi GND (via GPIO header to HAT)
             │
             ├─→ PCA9685 GND (via GPIO header)
             │
             ├─→ Relay GND
             │
             └─→ Motor -
```

## Complete Wiring Diagram

```
                    5V 5A Power Supply
                         │
                    ┌────┴────┐
                    │         │
                   +5V       GND
                    │         │
        ┌───────────┼─────────┼──────────────┐
        │           │         │              │
        │           │         │              │
  Raspberry Pi 5    │         │         DC Motor -
  (USB-C)           │         │
        │           │         │
    GPIO Header     │         │
        │           │         │
  ┌─────┴─────┐     │         │
  │ PCA9685   │     │         │
  │    HAT    │     │         │
  └─────┬─────┘     │         │
        │           │         │
   Servo Power ←────┘         │
   (V+ terminal)              │
        │                     │
    ┌───┴───┐                 │
    │Servos │                 │
    │Ch0,3, │                 │
    │ 6, 9  │                 │
    └───┬───┘                 │
        │                     │
      (All servos             │
       GND to HAT)            │
                              │
  ┌──────────────┐           │
  │ Relay Module │           │
  ├──────────────┤           │
  │ VCC ←────────┼───────────┘
  │ GND ←────────┼─────────────────┐
  │ IN ← GPIO 17 │                 │
  │              │                 │
  │ COM ←────────┼─── +5V         │
  │ NO  ─────────┼─→ Motor +      │
  └──────────────┘                 │
                                   │
         Common Ground ←───────────┘
```

## Raspberry Pi 5 Pinout Reference

```
┌─────────────────────────────────────┐
│  Raspberry Pi 5 GPIO Header (Top)   │
├─────────────────────────────────────┤
│                                      │
│  Pin 1  (3.3V)    →  HAT VCC (auto) │
│  Pin 2  (5V)      →  Relay VCC      │
│  Pin 3  (GPIO 2)  →  HAT SDA (auto) │
│  Pin 4  (5V)      →  [available]    │
│  Pin 5  (GPIO 3)  →  HAT SCL (auto) │
│  Pin 6  (GND)     →  Common GND     │
│  ...                                 │
│  Pin 11 (GPIO 17) →  Relay IN       │
│  ...                                 │
│  Pin 39 (GND)     →  [available]    │
│  Pin 40 (GPIO 21) →  [available]    │
│                                      │
└─────────────────────────────────────┘
```

**Key Connections:**
- **Pin 1** (3.3V) - Powers HAT logic (automatic via header)
- **Pin 2** (5V) - Relay VCC
- **Pin 3** (GPIO 2/SDA) - I2C data to HAT (automatic)
- **Pin 5** (GPIO 3/SCL) - I2C clock to HAT (automatic)
- **Pin 6** (GND) - Common ground
- **Pin 11** (GPIO 17) - Relay control signal

## Testing Procedure

### Pre-Power Checklist

Before powering on:

- [ ] HAT fully seated on GPIO header
- [ ] All servos connected to correct channels (0, 3, 6, 9)
- [ ] Relay VCC, GND, IN connected correctly
- [ ] Motor polarity correct (+ to relay NO, - to GND)
- [ ] All grounds connected together
- [ ] No loose wires or shorts
- [ ] Power supply is 5V (measure with multimeter!)
- [ ] Power supply off before making connections

### Step-by-Step Testing

#### Test 1: I2C Communication

```bash
# Power on Pi (without motor running)
sudo i2cdetect -y 1

# Should show:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# ...
# 40: 40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

✅ **Pass:** Device appears at 0x40  
❌ **Fail:** Check HAT seating, I2C enabled

#### Test 2: Individual Servo Test

```bash
# Test each servo one at a time
python3 << EOF
from dose_every_well import SolidDoser
doser = SolidDoser()
doser.open_gate()  # Channel 0 should move
doser.close_gate()
doser.shutdown()
EOF
```

Repeat for plate loader servos (channels 3, 6, 9).

#### Test 3: Relay Test

```bash
# Test relay clicking
python3 << EOF
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.HIGH)  # Should hear click
time.sleep(2)
GPIO.output(17, GPIO.LOW)   # Should hear click
GPIO.cleanup()
EOF
```

✅ **Pass:** Two audible clicks, relay LED lights  
❌ **Fail:** Check VCC, GND, GPIO 17 connections

#### Test 4: Motor Test (Careful!)

```bash
# Brief motor test
python3 << EOF
from dose_every_well import SolidDoser
import time
doser = SolidDoser()
doser.motor_on()
time.sleep(2)  # Motor should spin
doser.motor_off()
doser.shutdown()
EOF
```

✅ **Pass:** Motor spins smoothly  
❌ **Fail:** Check relay COM, NO, motor connections

#### Test 5: Full System Test

```bash
# Run calibration
cd demo
python3 solid_doser_demo.py
# Select "Recalibrate" option
```

## Troubleshooting

### No I2C Device Detected

**Symptoms:** `i2cdetect` shows nothing at 0x40

**Solutions:**
1. Check HAT is fully seated (all 40 pins)
2. Enable I2C: `sudo raspi-config` → Interface Options → I2C
3. Reboot: `sudo reboot`
4. Check for bent pins on GPIO header

### Servo Jitters or Doesn't Move

**Symptoms:** Servo vibrates, moves erratically, or doesn't move

**Solutions:**
1. Check power supply is 5V and adequate current (5A)
2. Verify servo is plugged into correct channel
3. Check servo connections (GND, 5V, Signal)
4. Test servo on different channel to isolate hardware issue
5. Check PCA9685 V+ terminal has 5V

### Relay Doesn't Click

**Symptoms:** No audible click, LED doesn't light

**Solutions:**
1. Verify VCC connected to 5V
2. Check GND connection
3. Test GPIO 17: `gpio readall` shows correct state
4. Try different GPIO pin in code
5. Test relay with 5V directly to confirm it works

### Motor Doesn't Spin

**Symptoms:** No motor movement when relay clicks

**Solutions:**
1. Check motor connections (+ to relay NO, - to GND)
2. Verify relay COM connected to +5V
3. Test motor directly with 5V to confirm it works
4. Check motor voltage rating matches supply
5. Motor may be stalled - check for mechanical blockage

### Pi Reboots / Brownout

**Symptoms:** Pi randomly reboots, screen flickers

**Solutions:**
1. **Upgrade power supply to 5V 10A**
2. Reduce number of simultaneous servo movements
3. Add delays between operations
4. Check all power connections are tight
5. Add 1000µF capacitor across motor terminals

### Servos Move at Wrong Times

**Symptoms:** Plate loader servos move during dispensing

**Solutions:**
1. Verify code uses correct channels:
   - Solid doser: Channel 0
   - Plate loader: Channels 3, 6, 9
2. Check for channel conflicts in code
3. Ensure proper initialization order

## Safety Notes

⚠️ **Important Safety Guidelines:**

1. **Always power off** before wiring
2. **Double-check polarity** (especially relay and motor)
3. **Use adequate power supply** (5A minimum, 10A recommended)
4. **Keep wires organized** to prevent shorts
5. **Monitor first tests** closely
6. **Emergency stop:** Ctrl+C in terminal or power switch
7. **Never force connectors** - they should plug in easily
8. **Avoid running motor stalled** - can overheat/damage
9. **Check for hot components** during testing
10. **Keep away from water/liquids**

## Maintenance

### Weekly Checks

- [ ] Verify all connections are tight
- [ ] Check for worn/frayed wires
- [ ] Clean dust from connectors
- [ ] Test emergency stop procedure

### Monthly Checks

- [ ] Re-run calibration
- [ ] Check servo movement smoothness
- [ ] Verify motor runs quietly
- [ ] Inspect HAT for loose pins
- [ ] Test backup/recovery procedures

## Additional Resources

- [Waveshare PCA9685 HAT Wiki](https://www.waveshare.com/wiki/Servo_Driver_HAT)
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)
- [Solid Doser Documentation](solid_doser.md)
- [Plate Loader Documentation](plate_loader.md)

## Getting Help

If you encounter issues not covered here:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Run diagnostic: `sudo i2cdetect -y 1`, `gpio readall`
3. Take photos of your wiring
4. Note exact error messages
5. Open an issue on GitHub with details

---

**Setup Complete!** Once wired and tested, proceed to the [Quick Start Guide](quick_start.md) for software usage.

