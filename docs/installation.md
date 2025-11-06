# Installation Guide

Quick and simple installation instructions for all platforms.

## Quick Install

### Option 1: Using uv (Recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/yourusername/dose_every_well.git
cd dose_every_well
uv venv
uv pip install -e .
```

### Option 2: Using pip

```bash
# Clone repository
git clone https://github.com/yourusername/dose_every_well.git
cd dose_every_well

# Create virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # Unix/Mac
# or
.venv\Scripts\activate     # Windows

# Install package
pip install -e .
```

## Platform-Specific Notes

### Linux/Raspberry Pi

Add your user to the `dialout` group for serial port access:

```bash
sudo usermod -a -G dialout $USER
```

Log out and back in for changes to take effect.

**For Raspberry Pi Hardware (Plate Loader, Solid Doser):**

```bash
# Install with Raspberry Pi hardware dependencies
pip install -e ".[rpi]"

# For Raspberry Pi 5, also install rpi-lgpio (required for GPIO support)
pip install rpi-lgpio
```

Note: Raspberry Pi 5 uses a different GPIO chip that requires `rpi-lgpio` as a compatibility layer for `RPi.GPIO`. Pi 3/4 work with standard `RPi.GPIO`.

### Windows

No additional setup required. Works out of the box.

### macOS

No additional setup required. Most USB devices work without drivers.

## Verify Installation

Test that everything works:

```bash
python test_platform.py
```

Expected output:
```
Total: 4/4 tests passed
🎉 All tests passed! Platform is fully compatible.
```

## Dependencies

Automatically installed:
- Python ≥ 3.8
- pyserial == 3.5
- matplotlib == 3.10.0
- PyYAML == 6.0.2

Optional (for Raspberry Pi hardware):
- adafruit-circuitpython-pca9685
- adafruit-circuitpython-motor
- rpi-lgpio (Raspberry Pi 5 only)

## Troubleshooting

### Permission denied (Linux/Pi)
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### Import errors
```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # Unix/Mac
.venv\Scripts\activate     # Windows

# Reinstall
pip install -e .
```

### Can't find uv
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip instead
pip install -e .
```

## Next Steps

- Read the [Quick Start Guide](quick_start.md)
- Run demo: `python demo/simple_connect_demo.py`
- Check [Troubleshooting](troubleshooting.md) if you have issues
