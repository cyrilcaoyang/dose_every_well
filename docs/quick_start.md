# Quick Start Guide

Get up and running with `dose_every_well` in 5 minutes.

## 1. Installation

```bash
# Install the package
pip install -e .

# Verify installation
python test_platform.py
```

## 2. Connect Your CNC

1. Connect CNC to computer via USB
2. Power on the CNC machine
3. Note the port (or let the software auto-detect)

## 3. Basic Usage

```python
from dose_every_well import CNC_Controller, load_config, find_port

# Load configuration
config = load_config("cnc_settings.yaml", "Genmitsu 4040 PRO")

# Auto-detect CNC port
port = find_port()

# Connect to CNC
controller = CNC_Controller(port, config)

# Read current position
coords = controller.read_coordinates()
print(f"Position: X={coords['X']}, Y={coords['Y']}, Z={coords['Z']}")

# Move to a position (in mm)
controller.move_to_point(10, 20)
controller.execute_movement()

# Move Z axis
controller.move_to_height(5.0)
controller.execute_movement()
```

## 4. Run Demo Scripts

### Simple Connection Test

```bash
python demo/simple_connect_demo.py
```

This connects to the CNC and displays current coordinates.

### Interactive Movement Demo

```bash
python demo/axis_movement_demo.py
```

This tests X, Y, Z movements with safety confirmations.

### Automated Demo

```bash
python demo/axis_movement_demo_auto.py
```

Runs automated movement tests (no user input).

## 5. Find Your Serial Port

### Auto-Detection (Recommended)

```python
from dose_every_well import find_port
port = find_port()  # Automatically finds CNC
```

### Manual Detection

**Windows:**
- Open Device Manager → Ports (COM & LPT)
- Look for COM port (e.g., COM3, COM5)

**Linux/Raspberry Pi:**
```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

**macOS:**
```bash
ls /dev/cu.*
```

## 6. Configure Your Machine

Edit `src/dose_every_well/cnc_settings.yaml`:

```yaml
machines:
  Your Machine Name:
    controller:
      baud_rate: 115200
      x_low_bound: 0
      x_high_bound: 400
      y_low_bound: 0
      y_high_bound: 400
      z_low_bound: 0
      z_high_bound: 75
```

Then use it:

```python
config = load_config("cnc_settings.yaml", "Your Machine Name")
```

## 7. Common Tasks

### Read Coordinates

```python
coords = controller.read_coordinates()
print(f"X: {coords['X']:.2f} mm")
print(f"Y: {coords['Y']:.2f} mm")
print(f"Z: {coords['Z']:.2f} mm")
```

### Move to Absolute Position

```python
# Move to X=50mm, Y=100mm
controller.move_to_point(50, 100)
controller.execute_movement()
```

### Move Z Axis

```python
# Move to Z=10mm
controller.move_to_height(10)
controller.execute_movement()
```

### Test with Simulator

```python
from dose_every_well import CNC_Simulator, load_config

config = load_config("cnc_settings.yaml", "Genmitsu 4040 PRO")
simulator = CNC_Simulator(config)

# Visualize movement
simulator.visualize_movement(50, 100)
```

## Quick Troubleshooting

### "No serial ports found"
- Check USB connection
- Verify CNC is powered on
- Try different USB port

### Permission denied (Linux/Pi)
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### Import errors
```bash
# Activate virtual environment first
source .venv/bin/activate  # Unix/Mac
.venv\Scripts\activate     # Windows

# Reinstall
pip install -e .
```

### CNC not responding
- Check baud rate (usually 115200)
- Try resetting the CNC
- Verify GRBL firmware is running

## Safety Checklist

Before running any movement:

- [ ] Work area is clear of obstacles
- [ ] Tool/dispenser is clear of workpiece
- [ ] Emergency stop is accessible
- [ ] Movement boundaries are configured correctly
- [ ] You understand what the code will do
- [ ] You're monitoring the first run

## Next Steps

- Read the [API Reference](api_reference.md) for detailed documentation
- Check [Platform Notes](platform_notes.md) for OS-specific tips
- Review [Troubleshooting Guide](troubleshooting.md) for common issues
- See demo scripts in `demo/` folder for examples

## Example: Dispense to Well Plate

```python
from dose_every_well import CNC_Controller, load_config, find_port

# Setup
config = load_config("cnc_settings.yaml", "Genmitsu 4040 PRO")
controller = CNC_Controller(find_port(), config)

# Define 96-well plate positions (8 rows x 12 columns)
well_spacing = 9.0  # mm between wells
start_x, start_y = 10.0, 10.0
dispense_height = 5.0

# Visit each well
for row in range(8):  # A-H
    for col in range(12):  # 1-12
        x = start_x + col * well_spacing
        y = start_y + row * well_spacing
        
        # Move to position
        controller.move_to_point(x, y)
        controller.move_to_height(dispense_height)
        controller.execute_movement()
        
        print(f"At well {chr(65+row)}{col+1}: X={x}, Y={y}")
        
        # Add your dispensing logic here
        # ...

print("Dispensing complete!")
```

