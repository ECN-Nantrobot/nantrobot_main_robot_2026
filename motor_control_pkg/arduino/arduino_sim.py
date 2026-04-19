import serial

# Connect to one end of the virtual cable
ser = serial.Serial('/tmp/ttyV1', 115200, timeout=1)

print("Arduino Simulator Started. Waiting for ROS2...")

while True:
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').strip()
        print(f"Virtual Arduino received: {data}")
        
        # Imitate the logic in your .ino file
        # Example: Echo back a confirmation
        ser.write(f"ACK: Received {data}\n".encode('utf-8'))