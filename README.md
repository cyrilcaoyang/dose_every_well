# Dose Every Well

**Automate liquid and solid powder dispensing into microplates using CNC machines.**

A Python package for precise control of CNC machines designed for laboratory automation and high-throughput dispensing workflows.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

## Features

### CNC Control
- 🎯 Precise G-code control of CNC machines via serial communication
- 🔌 Automatic serial port detection across all platforms
- 🔧 Pre-configured for Genmitsu 3018-PROVer V2 and 4040 PRO
- 📊 Built-in simulator for testing movements before execution
- 🌐 Cross-platform: Windows, Linux, Raspberry Pi, and macOS
- 🛡️ Safety boundaries to prevent collisions
- ⚙️ YAML-based configuration for easy machine setup

### Raspberry Pi Hardware Support
- 🤖 **Motorized Plate Loader** - Automated well plate loading with synchronized servo lift and lid control
- 💊 **Solid Powder Doser** - Precise solid material dispensing with servo gate and DC motor auger
- ⚡ **Power-Safe Operation** - Sequential control designed for 5V 5A single-supply operation
- 🔌 **Waveshare PCA9685 HAT** - I2C servo control with relay-based motor switching

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/dose_every_well.git
cd dose_every_well
pip install -e .
```

### Basic Usage

```python
from dose_every_well import CNC_Controller, load_config, find_port

# Load configuration and connect
config = load_config("cnc_settings.yaml", "Genmitsu 4040 PRO")
controller = CNC_Controller(find_port(), config)

# Read position
coords = controller.read_coordinates()
print(f"Position: X={coords['X']}, Y={coords['Y']}, Z={coords['Z']}")

# Move to position
controller.move_to_point(10, 20)  # X=10mm, Y=20mm
controller.execute_movement()
```

### Run Demos

```bash
# CNC control demos
python demo/simple_connect_demo.py
python demo/axis_movement_demo.py

# Raspberry Pi hardware demos (requires hardware)
python demo/plate_loader_demo.py
python demo/solid_doser_demo.py
```

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Windows 7/10/11 | ✅ | Works out of box |
| Linux (Ubuntu/Debian) | ✅ | Requires dialout group |
| Raspberry Pi 3/4/5 | ✅ | Tested on Pi 5 |
| macOS (Intel/M1/M2) | ✅ | Full support |

## Documentation

📚 **[Complete Documentation](docs/)**

### General
- **[Installation Guide](docs/installation.md)** - Platform-specific setup instructions
- **[Quick Start Guide](docs/quick_start.md)** - Get running in 5 minutes
- **[API Reference](docs/api_reference.md)** - Complete API documentation
- **[Troubleshooting](docs/troubleshooting.md)** - Solutions to common issues

### Raspberry Pi Hardware
- **[Wiring Guide](docs/wiring_guide.md)** 🔌 - Complete hardware setup with diagrams
- **[Plate Loader Guide](docs/plate_loader.md)** - Motorized plate loader documentation
- **[Solid Doser Guide](docs/solid_doser.md)** - Solid powder dosing documentation
- **[Servo Power Guide](docs/servo_power_guide.md)** - Power management and optimization

## Supported Hardware

### CNC Machines
- **Genmitsu 4040 PRO** (400×400×75mm work area)
- **Genmitsu 3018-PROVer V2** (300×180×45mm work area)
- Any GRBL-compatible CNC machine (requires custom configuration)

### Raspberry Pi Hardware (Optional)
**Complete system for automated solid/liquid dispensing:**

| Component | Purpose | Channels |
|-----------|---------|----------|
| **Waveshare PCA9685 HAT** | I2C servo driver (0x40) | 16 channels |
| **4× Servo Motors** | Gate, lifts, lid control | Ch 0, 3, 6, 9 |
| **5V Relay Module** | DC motor ON/OFF | GPIO 17 |
| **DC Motor** | Auger/screw feeder | Via relay |
| **5V 5A Power Supply** | Single plug powers all | USB-C + distribution |

📖 **See [Wiring Guide](docs/wiring_guide.md) for complete setup instructions**

## Testing

Verify your setup works correctly:

```bash
python test_platform.py
```

## Project Structure

```
dose_every_well/
├── src/dose_every_well/       # Main package
│   ├── cnc_controller.py      # Core CNC controller
│   ├── plate_loader.py        # Raspberry Pi plate loader (3 servos)
│   ├── solid_doser.py         # Raspberry Pi solid doser (servo + motor)
│   ├── cnc_settings.yaml      # Machine configs
│   └── __init__.py
├── demo/                       # Example scripts
│   ├── simple_connect_demo.py
│   ├── axis_movement_demo.py
│   ├── plate_loader_demo.py
│   └── solid_doser_demo.py
├── docs/                       # Documentation
│   ├── wiring_guide.md        # 🔌 Hardware setup (START HERE!)
│   ├── solid_doser.md
│   ├── plate_loader.md
│   ├── installation.md
│   └── troubleshooting.md
├── test_platform.py           # Platform compatibility test
└── README.md                  # This file
```

## Safety

⚠️ **Important Safety Practices:**

- Test in simulation before hardware execution
- Verify movement boundaries match your machine
- Keep emergency stop accessible during operation
- Clear work area before automated runs
- Monitor Z-axis movements to prevent crashes

## Usage Examples

### Example 1: CNC-Only Liquid Dispensing

```python
from dose_every_well import CNC_Controller, load_config, find_port

# Setup
config = load_config("cnc_settings.yaml", "Genmitsu 4040 PRO")
controller = CNC_Controller(find_port(), config)

# 96-well plate parameters
well_spacing = 9.0  # mm
start_x, start_y = 10.0, 10.0
dispense_height = 5.0

# Visit each well
for row in range(8):  # A-H
    for col in range(12):  # 1-12
        x = start_x + col * well_spacing
        y = start_y + row * well_spacing
        
        controller.move_to_point(x, y)
        controller.move_to_height(dispense_height)
        controller.execute_movement()
        
        print(f"Dispensing to well {chr(65+row)}{col+1}")
```

### Example 2: Complete Solid Dosing Workflow (Raspberry Pi)

```python
from dose_every_well import CNC_Controller, PlateLoader, SolidDoser, load_config, find_port
import time

# Initialize all controllers
cnc = CNC_Controller(find_port(), load_config("cnc_settings.yaml", "Genmitsu 4040 PRO"))
plate_loader = PlateLoader(i2c_address=0x40)
solid_doser = SolidDoser(i2c_address=0x40, motor_gpio_pin=17)

try:
    # 1. Load plate onto balance
    print("Loading plate...")
    plate_loader.load_sequence()
    
    # 2. Dispense solid into each well
    well_spacing = 9.0  # mm
    start_x, start_y = 10.0, 10.0
    
    for row in range(8):
        for col in range(12):
            well = f"{chr(65+row)}{col+1}"
            print(f"Dispensing to well {well}...")
            
            # Move CNC to well position
            x = start_x + col * well_spacing
            y = start_y + row * well_spacing
            cnc.move_to_point(x, y)
            cnc.move_to_height(5.0)
            cnc.execute_movement()
            
            # Dispense solid material (motor + gate servo)
            solid_doser.dispense(duration=2.0)
            
            # Move up
            cnc.move_to_height(20.0)
            cnc.execute_movement()
    
    # 3. Unload plate
    print("Unloading plate...")
    plate_loader.unload_sequence()
    
finally:
    solid_doser.shutdown()
    plate_loader.shutdown()
    cnc.disconnect()
```

### Example 3: Solid Doser Only (No CNC)

```python
from dose_every_well import SolidDoser

doser = SolidDoser(i2c_address=0x40, motor_gpio_pin=17)

try:
    # Simple dispense for 5 seconds
    doser.dispense(duration=5.0)
    
    # Precise low-flow dispense (30° gate opening)
    doser.dispense(duration=3.0, gate_angle=30)
    
finally:
    doser.shutdown()
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `python test_platform.py` to verify
5. Submit a pull request

For major changes, open an issue first to discuss.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Yang Cao**
- Email: yangcyril.cao@utoronto.ca
- GitHub: [@yourusername](https://github.com/yourusername)

## Citation

If you use this package in your research, please cite:

```bibtex
@software{dose_every_well,
  author = {Cao, Yang},
  title = {Dose Every Well: CNC-based Automated Dispensing},
  year = {2025},
  url = {https://github.com/yourusername/dose_every_well}
}
```

## Acknowledgments

Built for laboratory automation workflows with a focus on microplate dispensing applications. Uses GRBL firmware for CNC control.

---

**Need help?** Check the [documentation](docs/) or open an issue on GitHub.
