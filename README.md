# Dose Every Well

**Automate liquid and solid powder dispensing into microplates using CNC machines.**

A Python package for precise control of CNC machines designed for laboratory automation and high-throughput dispensing workflows.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

## Features

- 🎯 Precise G-code control of CNC machines via serial communication
- 🔌 Automatic serial port detection across all platforms
- 🔧 Pre-configured for Genmitsu 3018-PROVer V2 and 4040 PRO
- 📊 Built-in simulator for testing movements before execution
- 🌐 Cross-platform: Windows, Linux, Raspberry Pi, and macOS
- 🛡️ Safety boundaries to prevent collisions
- ⚙️ YAML-based configuration for easy machine setup

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
# Simple connection test
python demo/simple_connect_demo.py

# Interactive movement demo
python demo/axis_movement_demo.py
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

- **[Installation Guide](docs/installation.md)** - Platform-specific setup instructions
- **[Quick Start Guide](docs/quick_start.md)** - Get running in 5 minutes
- **[API Reference](docs/api_reference.md)** - Complete API documentation
- **[Platform Notes](docs/platform_notes.md)** - Platform-specific details
- **[Troubleshooting](docs/troubleshooting.md)** - Solutions to common issues
- **[Changelog](docs/changelog.md)** - Version history and migration guide

## Supported Hardware

- **Genmitsu 4040 PRO** (400×400×75mm work area)
- **Genmitsu 3018-PROVer V2** (300×180×45mm work area)
- Any GRBL-compatible CNC machine (requires custom configuration)

## Testing

Verify your setup works correctly:

```bash
python test_platform.py
```

## Project Structure

```
dose_every_well/
├── src/dose_every_well/      # Main package
│   ├── cnc_controller.py     # Core controller
│   ├── cnc_settings.yaml     # Machine configs
│   └── __init__.py
├── demo/                      # Example scripts
│   ├── simple_connect_demo.py
│   ├── axis_movement_demo.py
│   └── axis_movement_demo_auto.py
├── docs/                      # Documentation
│   ├── installation.md
│   ├── quick_start.md
│   ├── api_reference.md
│   ├── platform_notes.md
│   ├── troubleshooting.md
│   └── changelog.md
├── test_platform.py          # Platform compatibility test
└── README.md                 # This file
```

## Safety

⚠️ **Important Safety Practices:**

- Test in simulation before hardware execution
- Verify movement boundaries match your machine
- Keep emergency stop accessible during operation
- Clear work area before automated runs
- Monitor Z-axis movements to prevent crashes

## Example: Dispense to 96-Well Plate

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
