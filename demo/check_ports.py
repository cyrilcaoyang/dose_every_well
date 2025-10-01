import serial.tools.list_ports

def list_available_ports():
    """
    List all available serial ports to help find the Arduino
    """
    print("Available serial ports:")
    print("-" * 40)
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("No serial ports found!")
        return
    
    for port in ports:
        print(f"Port: {port.device}")
        print(f"Description: {port.description}")
        print(f"Hardware ID: {port.hwid}")
        
        # Check if it might be an Arduino
        if any(keyword in port.description.lower() for keyword in ['arduino', 'ch340', 'cp210', 'ftdi']):
            print("  -> This might be your Arduino!")
        
        print("-" * 40)

if __name__ == "__main__":
    list_available_ports()
