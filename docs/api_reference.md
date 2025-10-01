# API Reference

Complete API documentation for `dose_every_well`.

## Core Functions

### `load_config(config_path, model_name)`

Load machine configuration from YAML file.

**Parameters:**
- `config_path` (str): Path to YAML config file (relative to package)
- `model_name` (str): Name of machine model in config

**Returns:**
- dict: Configuration dictionary for specified machine

**Example:**
```python
config = load_config("cnc_settings.yaml", "Genmitsu 4040 PRO")
```

**Config Structure:**
```python
{
    'simulator': {
        'min_x': 0,
        'max_x': 200,
        'min_y': 0,
        'max_y': 100,
        'figure_size': [10, 5]
    },
    'controller': {
        'baud_rate': 115200,
        'x_low_bound': 0,
        'x_high_bound': 435,
        'y_low_bound': 0,
        'y_high_bound': 400,
        'z_low_bound': 0,
        'z_high_bound': 75,
        'x_offset': 0,
        'y_offset': 0
    }
}
```

---

### `find_port()`

Automatically detect CNC machine on available serial ports.

**Returns:**
- str: Serial port device path

**Raises:**
- Exception: If no ports found or CNC not detected

**Platform-Specific Returns:**
- Windows: `"COM3"`, `"COM5"`, etc.
- Linux: `"/dev/ttyUSB0"`, `"/dev/ttyACM0"`, etc.
- macOS: `"/dev/cu.usbserial-*"`, etc.

**Example:**
```python
port = find_port()
print(f"CNC found on: {port}")
```

**Behavior:**
1. Lists all available serial ports
2. If only one port exists, returns it immediately
3. If multiple ports, attempts to communicate with each
4. Returns first port that responds to GRBL commands

---

## CNC_Controller Class

Main controller class for CNC communication and movement.

### `__init__(port, config)`

Initialize CNC controller.

**Parameters:**
- `port` (str): Serial port path
- `config` (dict): Configuration dictionary from `load_config()`

**Example:**
```python
config = load_config("cnc_settings.yaml", "Genmitsu 4040 PRO")
controller = CNC_Controller("/dev/ttyUSB0", config)
```

**Initialization:**
- Opens serial connection
- Wakes up GRBL
- Loads movement boundaries
- Prepares command buffer

---

### `read_coordinates()`

Read current machine coordinates.

**Returns:**
- dict: Current position with keys 'X', 'Y', 'Z' (in mm)
- None: If coordinates cannot be read

**Example:**
```python
coords = controller.read_coordinates()
if coords:
    print(f"X: {coords['X']:.2f} mm")
    print(f"Y: {coords['Y']:.2f} mm")
    print(f"Z: {coords['Z']:.2f} mm")
```

**Notes:**
- Sends `?` status query to GRBL
- Parses MPos (machine position) from response
- Returns None if communication fails

---

### `move_to_point(x, y)`

Queue movement to XY coordinates.

**Parameters:**
- `x` (float): X coordinate in mm
- `y` (float): Y coordinate in mm

**Returns:**
- None

**Example:**
```python
# Move to X=50mm, Y=100mm
controller.move_to_point(50, 100)
controller.execute_movement()  # Actually perform the move
```

**Notes:**
- Movements are queued, not executed immediately
- Call `execute_movement()` to perform queued moves
- Coordinates are checked against configured boundaries
- Uses G0 (rapid positioning) command

---

### `move_to_height(z)`

Queue Z-axis movement.

**Parameters:**
- `z` (float): Z coordinate in mm

**Returns:**
- None

**Example:**
```python
# Move to Z=10mm
controller.move_to_height(10)
controller.execute_movement()
```

**Notes:**
- Z movements are queued separately
- Call `execute_movement()` to perform
- Z coordinate checked against boundaries
- Uses G0 (rapid positioning) command

---

### `execute_movement()`

Execute all queued movement commands.

**Returns:**
- None

**Example:**
```python
# Queue multiple movements
controller.move_to_point(10, 20)
controller.move_to_height(5)
controller.move_to_point(30, 40)

# Execute all at once
controller.execute_movement()
```

**Behavior:**
- Sends all buffered G-code commands
- Waits for GRBL to complete each command
- Blocks until all movements finish
- Clears command buffer after execution

---

### `wait_for_movement_completion(ser, buffered_gcode)`

Wait for GRBL to complete movement commands.

**Parameters:**
- `ser`: Serial connection object
- `buffered_gcode` (list): List of G-code commands sent

**Returns:**
- None

**Notes:**
- Internal method, typically not called directly
- Monitors GRBL status until idle
- Ensures movements complete before returning

---

## CNC_Simulator Class

Visualization and testing without hardware.

### `__init__(config)`

Initialize simulator.

**Parameters:**
- `config` (dict): Configuration dictionary from `load_config()`

**Example:**
```python
config = load_config("cnc_settings.yaml", "Genmitsu 4040 PRO")
simulator = CNC_Simulator(config)
```

---

### `visualize_movement(x, y)`

Visualize planned XY movement.

**Parameters:**
- `x` (float): Target X coordinate in mm
- `y` (float): Target Y coordinate in mm

**Returns:**
- None (displays matplotlib plot)

**Example:**
```python
simulator = CNC_Simulator(config)
simulator.visualize_movement(50, 100)
```

**Notes:**
- Opens matplotlib window showing movement
- Displays work area boundaries
- Shows planned path
- Useful for testing before hardware execution

---

## Configuration File Format

The `cnc_settings.yaml` file defines machine parameters:

```yaml
machines:
  Machine Name:
    simulator:
      min_x: 0          # Simulator plot min X
      max_x: 200        # Simulator plot max X
      min_y: 0          # Simulator plot min Y
      max_y: 100        # Simulator plot max Y
      figure_size: [10, 5]  # Plot size in inches
    
    controller:
      baud_rate: 115200      # Serial communication speed
      x_low_bound: 0         # Min X coordinate (mm)
      x_high_bound: 435      # Max X coordinate (mm)
      y_low_bound: 0         # Min Y coordinate (mm)
      y_high_bound: 400      # Max Y coordinate (mm)
      z_low_bound: 0         # Min Z coordinate (mm)
      z_high_bound: 75       # Max Z coordinate (mm)
      x_offset: 0            # X coordinate offset (mm)
      y_offset: 0            # Y coordinate offset (mm)
```

## Pre-configured Machines

### Genmitsu 4040 PRO
- Work area: 400×400×75 mm
- Baud rate: 115200

### Genmitsu 3018-PROVer V2
- Work area: 300×180×45 mm
- Baud rate: 115200

## Error Handling

### Common Exceptions

**Serial Communication Errors:**
```python
try:
    controller = CNC_Controller(port, config)
except Exception as e:
    print(f"Connection failed: {e}")
```

**Coordinate Out of Bounds:**
```python
# Automatic boundary checking
controller.move_to_point(1000, 1000)  # Exceeds boundaries
# Will be clamped or raise error
```

**Port Not Found:**
```python
try:
    port = find_port()
except Exception as e:
    print("No CNC found. Check connection.")
```

## Thread Safety

The controller is **not thread-safe**. For concurrent access:

```python
from threading import Lock

lock = Lock()

def safe_move(controller, x, y):
    with lock:
        controller.move_to_point(x, y)
        controller.execute_movement()
```

## Best Practices

1. **Always check coordinates before moving:**
   ```python
   coords = controller.read_coordinates()
   if coords:
       print(f"Starting at: {coords}")
   ```

2. **Test in simulation first:**
   ```python
   simulator = CNC_Simulator(config)
   simulator.visualize_movement(x, y)
   # If looks good, then use real controller
   ```

3. **Use try-finally for cleanup:**
   ```python
   try:
       controller = CNC_Controller(port, config)
       # Your code here
   finally:
       # Cleanup if needed
       pass
   ```

4. **Validate inputs:**
   ```python
   def safe_move(controller, x, y):
       assert 0 <= x <= 400, "X out of range"
       assert 0 <= y <= 400, "Y out of range"
       controller.move_to_point(x, y)
       controller.execute_movement()
   ```

## Examples

### Example 1: Simple Movement

```python
from dose_every_well import CNC_Controller, load_config, find_port

config = load_config("cnc_settings.yaml", "Genmitsu 4040 PRO")
controller = CNC_Controller(find_port(), config)

# Move in a square
points = [(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)]
for x, y in points:
    controller.move_to_point(x, y)
    controller.execute_movement()
```

### Example 2: Grid Pattern

```python
# Visit points in a grid
for x in range(0, 100, 10):
    for y in range(0, 100, 10):
        controller.move_to_point(x, y)
        controller.execute_movement()
        print(f"At position ({x}, {y})")
```

### Example 3: With Safety Checks

```python
def safe_dispense(controller, x, y, z):
    """Move to position with safety checks"""
    # Check boundaries
    config = controller.config['controller']
    if not (config['x_low_bound'] <= x <= config['x_high_bound']):
        raise ValueError(f"X {x} out of bounds")
    if not (config['y_low_bound'] <= y <= config['y_high_bound']):
        raise ValueError(f"Y {y} out of bounds")
    if not (config['z_low_bound'] <= z <= config['z_high_bound']):
        raise ValueError(f"Z {z} out of bounds")
    
    # Perform movement
    controller.move_to_point(x, y)
    controller.move_to_height(z)
    controller.execute_movement()
```

