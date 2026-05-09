
import serial, time, serial.tools.list_ports

def find_port():
    ports = list(serial.tools.list_ports.comports())
    if len(ports) == 0:
        return None
    # prefer ones that say Arduino or CH340, else pick first
    for p in ports:
        if 'arduino' in (p.description or '').lower() or 'ch340' in (p.description or '').lower():
            return p.device
    return ports[0].device

port = find_port()
if not port:
    print("No serial ports found. Plug in Arduino and run: python -m serial.tools.list_ports")
    raise SystemExit

baud = 9600
print("Using", port)
ser = serial.Serial(port, baud, timeout=1)
time.sleep(2)  # allow Arduino auto-reset
messages = ["DEPOSIT 500", "BALANCE 1500", "CLEAR"]

for m in messages:
    print("Sending:", m)
    ser.write((m + "\n").encode('utf-8'))  # must end with '\n'
    time.sleep(1)

ser.close()
print("Done")
