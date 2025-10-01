# Dose Every Well Demo Scripts

This folder contains demo scripts for testing the dose_every_well driver and demonstrating axis movement capabilities.

## Files

- **`axis_movement_demo.py`** - Interactive demo with user confirmation for Z-axis movements
- **`axis_movement_demo_auto.py`** - Fully automated demo (no user input required)

## What the Demo Does

The demo scripts will:

1. **Load your CNC configuration** from `cnc_settings.yaml`
2. **Find and connect** to your CNC machine automatically
3. **Test movement** of each axis (X, Y, Z) with different step values:
   - 10 steps (10 mm)
   - 20 steps (20 mm) 
   - 50 steps (50 mm)
4. **Print coordinates** before and after each movement
5. **Execute G-code** commands to move the machine

## Prerequisites

1. **Virtual environment activated**: Make sure you're using the `venv` (not conda)
2. **Dependencies installed**: Run `pip install -e .` from the project root
3. **CNC machine connected**: Ensure your CNC is powered on and connected via USB
4. **Configuration file**: Verify `src/dose_every_well/cnc_settings.yaml` exists and is correct

## Running the Demo

### Option 1: Interactive Demo (Recommended for first run)

**Unix/Linux/Mac/Raspberry Pi:**
```bash
# From the project root directory
python demo/axis_movement_demo.py
```

**Windows:**
```bash
# From the project root directory
python demo\axis_movement_demo.py
```

This version will pause before Z-axis movements for safety confirmation.

### Option 2: Automated Demo

**Unix/Linux/Mac/Raspberry Pi:**
```bash
# From the project root directory
python demo/axis_movement_demo_auto.py
```

**Windows:**
```bash
# From the project root directory
python demo\axis_movement_demo_auto.py
```

This version runs completely automatically without user input.

### Option 3: Simple Connection Test

**Unix/Linux/Mac/Raspberry Pi:**
```bash
python demo/simple_connect_demo.py
```

**Windows:**
```bash
python demo\simple_connect_demo.py
```

This version just connects and reads coordinates (no movement).

## Safety Notes

⚠️ **IMPORTANT SAFETY WARNINGS:**

- **Ensure your tool is clear** of any workpiece before running
- **Check your machine boundaries** in the configuration file
- **Start with small movements** to verify everything works correctly
- **Have an emergency stop** ready in case of unexpected behavior
- **Z-axis movements** can cause tool crashes - be especially careful

## Expected Output

The demo will show output similar to:
```
=== Liquid CNC Axis Movement Demo ===
Loading configuration...
Configuration loaded successfully!
Finding CNC port...
CNC found on port: COM3
CNC controller initialized successfully!

Testing movement with step size: 1.0 mm
==================================================

==================== TESTING 10 STEPS ====================

--- Moving X-axis by 10 steps (10.0 mm) ---
Before X-axis movement - Current coordinates: X=0.00, Y=0.00, Z=0.00
Executing: G0 X10.0
After X-axis movement - Current coordinates: X=10.00, Y=0.00, Z=0.00

--- Moving Y-axis by 10 steps (10.0 mm) ---
...
```

## Troubleshooting

### Common Issues

1. **"No serial ports found"**
   - **Windows**: Check Device Manager → Ports (COM & LPT)
   - **Linux/Pi**: Run `ls /dev/ttyUSB* /dev/ttyACM*` to list available ports
   - **All platforms**: Check USB connection and verify CNC is powered on

2. **Permission denied (Linux/Raspberry Pi)**
   ```bash
   # Add your user to the dialout group
   sudo usermod -a -G dialout $USER
   # Log out and back in for the change to take effect
   ```

3. **"Configuration loaded for Genmitsu 4040 PRO"**
   - Verify machine name matches your config file
   - Check YAML syntax in `cnc_settings.yaml`

4. **Import errors**
   - Ensure virtual environment is activated
     - Unix/Mac: `source .venv/bin/activate`
     - Windows: `.venv\Scripts\activate`
   - Run `pip install -e .` from project root
   - Check Python path includes `src` directory

5. **Movement errors**
   - Verify machine is homed
   - Check coordinate boundaries in config
   - Ensure tool is clear of obstacles

6. **Raspberry Pi specific**
   - If matplotlib is slow, set: `export MPLBACKEND=Agg`
   - Ensure you have enough free memory (close other apps)

## Customization

You can modify the demo by changing:
- **Step values**: Edit the `step_values` list in the script
- **Step size**: Change the `step_size` variable (default: 1.0 mm)
- **Machine model**: Update the machine name in `load_config()` call
- **Movement delays**: Adjust `time.sleep()` values for your machine speed

## Support

If you encounter issues:
1. Check the error messages carefully
2. Verify your CNC configuration
3. Test with smaller step values first
4. Ensure your machine is properly calibrated and homed
