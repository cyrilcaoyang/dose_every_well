# Troubleshooting Guide

Solutions to common issues when using `dose_every_well`.

## Installation Issues

### "No module named 'setuptools'"

**Solution:**
```bash
pip install --upgrade pip setuptools wheel
pip install -e .
```

### Permission errors during installation (Linux/Pi)

**Solution:**
```bash
# Use --user flag
pip install --user -e .

# Or fix ownership
sudo chown -R $USER:$USER ~/.local
```

### SSL Certificate errors

**Solution:**
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -e .
```

---

## Serial Port Issues

### "No serial ports found"

**Windows:**
1. Open Device Manager → Ports (COM & LPT)
2. Check if CNC appears as COM port
3. If not, install USB-to-Serial driver
4. Try different USB port

**Linux/Raspberry Pi:**
```bash
# List available ports
ls /dev/ttyUSB* /dev/ttyACM*

# Check if device is detected
dmesg | grep tty

# Check USB devices
lsusb
```

**macOS:**
```bash
# List ports
ls /dev/cu.*

# If no ports, check System Information → USB
```

**All Platforms:**
- Verify CNC is powered on
- Try different USB cable
- Check USB port works with other devices

### Permission denied opening port (Linux/Pi)

**Solution:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Verify group membership
groups

# If dialout not listed, log out and back in

# Alternative: Temporary permission (not recommended)
sudo chmod 666 /dev/ttyUSB0
```

### Port exists but can't connect

**Check baud rate:**
```python
# Try different baud rates
for baud in [9600, 19200, 38400, 57600, 115200]:
    try:
        ser = serial.Serial(port, baudrate=baud, timeout=1)
        ser.write(b"?\n")
        response = ser.read_all()
        if response:
            print(f"Works at {baud} baud")
            break
    except:
        pass
```

**Check if port is already in use:**
```bash
# Linux/Mac
lsof | grep ttyUSB

# Kill process using port
kill <PID>
```

---

## Communication Issues

### "Could not read coordinates"

**Causes & Solutions:**

1. **CNC not initialized:**
   - Home the machine first
   - Reset GRBL: Send `Ctrl-X` or `$X`

2. **Wrong baud rate:**
   - Check `cnc_settings.yaml`
   - GRBL usually uses 115200

3. **GRBL not responding:**
   - Power cycle the CNC
   - Check GRBL firmware is installed
   - Use serial terminal to test manually

4. **Cable issue:**
   - Try different USB cable
   - Check for loose connections

**Test manually:**
```bash
# Linux/Mac
screen /dev/ttyUSB0 115200

# Windows: Use PuTTY or Arduino Serial Monitor

# In terminal, type:
?
# Should see status response like: <Idle|MPos:0.000,0.000,0.000|...>
```

### CNC moves erratically

**Check:**
1. Mechanical issues (loose belts, bindings)
2. Power supply adequate
3. Stepper driver configuration
4. GRBL settings (`$$` command)

---

## Movement Issues

### "Movement out of bounds"

**Solution:**
```python
# Check your boundaries
config = load_config("cnc_settings.yaml", "Your Machine")
print(config['controller'])

# Adjust coordinates or update config
```

**Verify physical limits:**
1. Manually jog machine to limits
2. Measure actual work area
3. Update `cnc_settings.yaml` accordingly

### CNC doesn't move

**Checklist:**
- [ ] Machine is homed
- [ ] GRBL is in `Idle` state (not `Alarm`)
- [ ] No physical obstructions
- [ ] Stepper motors enabled
- [ ] Power supply connected

**Reset GRBL alarm:**
```python
import serial
ser = serial.Serial(port, 115200)
ser.write(b"$X\n")  # Kill alarm lock
```

### Movements are too fast/slow

**Adjust feed rate in G-code:**
```python
# Modify cnc_controller.py or send custom G-code
controller.move_to_point(x, y, feed_rate=1000)  # mm/min
```

**Check GRBL settings:**
```
$$  # View all settings
$110=5000  # Set X max rate (mm/min)
$111=5000  # Set Y max rate
$112=500   # Set Z max rate
```

---

## Platform-Specific Issues

### Windows

**COM port number changes:**
- Use `find_port()` for automatic detection
- Or assign fixed COM port in Device Manager

**"Access Denied" on COM port:**
- Close other programs using port (Arduino IDE, etc.)
- Run as administrator (if necessary)

### Linux/Raspberry Pi

**"Permission denied" after adding to dialout:**
```bash
# Verify group membership
groups

# If not showing, log out completely
# SSH users: exit and reconnect
# GUI users: log out and back in
```

**Port disappears randomly:**
- Check USB power supply (Pi needs 3A+)
- Add `usbcore.autosuspend=-1` to `/boot/cmdline.txt`
- Check `dmesg` for errors

**Slow matplotlib (Raspberry Pi):**
```bash
# Use non-GUI backend
export MPLBACKEND=Agg

# Or install lighter backend
pip install matplotlib --no-deps
```

### macOS

**"Device not found" after OS update:**
- Reinstall USB driver
- Check Security & Privacy settings
- Try different USB port (not hub)

**Multiple ports for same device:**
- Use `/dev/cu.*` not `/dev/tty.*`
- The `cu` (call-up) devices work better

---

## Import Errors

### "No module named 'dose_every_well'"

**Solution:**
```bash
# Check if installed
pip list | grep dose

# If not, install
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

### "No module named 'serial'"

**Solution:**
```bash
pip install pyserial
```

### "No module named 'yaml'"

**Solution:**
```bash
pip install PyYAML
```

### Virtual environment not activated

**Solution:**
```bash
# Unix/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Verify
which python  # Unix/Mac
where python  # Windows
```

---

## Configuration Issues

### "Configuration loaded for [wrong machine]"

**Check:**
1. Machine name spelling in YAML
2. YAML indentation (spaces, not tabs)
3. File path to config

**Debug:**
```python
import yaml
with open("src/dose_every_well/cnc_settings.yaml") as f:
    config = yaml.safe_load(f)
    print(config.keys())  # See available machines
```

### Custom machine not recognized

**Verify YAML syntax:**
```bash
# Install yamllint
pip install yamllint

# Check file
yamllint src/dose_every_well/cnc_settings.yaml
```

---

## Performance Issues

### Slow on Raspberry Pi

**Solutions:**
1. Use headless matplotlib:
   ```bash
   export MPLBACKEND=Agg
   ```

2. Disable GUI:
   ```python
   import matplotlib
   matplotlib.use('Agg')
   ```

3. Close other applications

4. Upgrade to Pi 4 or Pi 5

### High CPU usage

- Check for infinite loops in custom code
- Reduce polling frequency
- Use sleep between movements

---

## Testing & Debugging

### Enable debug output

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test serial communication manually

```python
import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)

# Wake up GRBL
ser.write(b"\r\n\r\n")
time.sleep(1)

# Get status
ser.write(b"?\n")
response = ser.read_all()
print(response)

ser.close()
```

### Verify package installation

```bash
python test_platform.py
```

### Check GRBL settings

```python
import serial
ser = serial.Serial(port, 115200)
ser.write(b"$$\n")
time.sleep(1)
print(ser.read_all().decode())
```

---

## Getting Help

If you're still having issues:

1. **Run diagnostic:**
   ```bash
   python test_platform.py
   ```

2. **Check documentation:**
   - [Installation Guide](installation.md)
   - [Platform Notes](platform_notes.md)
   - [API Reference](api_reference.md)

3. **Gather information:**
   - Operating system and version
   - Python version
   - Output of `test_platform.py`
   - Error messages
   - What you've already tried

4. **Open an issue:**
   - GitHub Issues (with information above)
   - Include minimal code to reproduce issue

## Common Error Messages

### `ModuleNotFoundError: No module named 'dose_every_well'`
→ See [Import Errors](#import-errors)

### `serial.serialutil.SerialException: [Errno 13] could not open port`
→ See [Permission denied](#permission-denied-opening-port-linuxpi)

### `Exception: No serial ports found!`
→ See ["No serial ports found"](#no-serial-ports-found)

### `yaml.scanner.ScannerError: mapping values are not allowed here`
→ See [Configuration Issues](#configuration-issues)

### `AttributeError: 'NoneType' object has no attribute 'X'`
→ See ["Could not read coordinates"](#could-not-read-coordinates)

