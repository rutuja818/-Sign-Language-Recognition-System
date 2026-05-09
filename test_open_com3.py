import serial, time
import serial.tools.list_ports
print("Ports:", [p.device + " - " + p.description for p in serial.tools.list_ports.comports()])
port = 'COM3'   # change if serial.tools.list_ports showed another COM
print("Trying", port)
try:
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(1)
    print("OPEN ✓", ser.name, "is_open:", ser.is_open)
    ser.write(b'Hello\n')
    print("Write OK")
    ser.close()
except Exception as e:
    print("Exception:", type(e).__name__, e)
