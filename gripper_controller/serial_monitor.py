import serial

class SerialMonitor:
    def __init__ (self, port = "COM3", baudrate = 9600):
        self.ser = serial.Serial (port, baudrate, timeout = 1)

    def send (self, cmd):
        """Send command, return one line of response"""
        self.ser.write ((cmd + "\n").encode())
        return self.ser.readline().decode().strip()

    def loop (self):
        """Interactive mode like an Arduino Serial Monitor"""
        while True:
            cmd = input("> ").strip()
            if cmd.lower() in {"exit", "quit"}:
                break
            print(self.send(cmd))
