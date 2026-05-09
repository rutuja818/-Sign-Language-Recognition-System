
import serial
import serial.tools.list_ports
import time, sys, traceback

ports = list(serial.tools.list_ports.comports())
if not ports:
    print("No serial ports found.")
    sys.exit(0)

print("Detected ports:")
for p in ports:
    print(f"  {p.device}  -  {p.description}")

for p in ports:
    port = p.device
    print("\n--- Testing", port, "---")
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)   # allow Arduino to reset and ready up
        print("Opened:", ser.name, "is_open:", ser.is_open)
        try:
            print("Writing test bytes...")
            ser.write(b'Hello\n')
            print("Write OK")
        except Exception as w:
            print("Write Exception:", type(w).__name__, repr(w))
            traceback.print_exc()
        ser.close()
        print("Closed port.")
    except Exception as e:
        print("Open Exception:", type(e).__name__, repr(e))
        traceback.print_exc()
