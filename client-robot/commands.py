
import serial
import serial.tools.list_ports
import time

def messageToSequence(message):
    print(f"Received message: {message}")
    if message == "r4":
        return "sequence1"
    elif message == "r5":
        return "sequence2"
    elif message == "l4":
        return "sequence3"
    elif message == "l5":
        return "sequence4"
    else:
        return "stop"
    


def find_arduino_serial_port(baud_rate=9600, timeout=2):
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "Arduino" in port.manufacturer:
            return port.device
    return None

def set_both_servos(ser, angle1, angle2):
    angle1 = max(0, min(180, angle1))
    angle2 = max(0, min(180, angle2))
    command = f"S:{angle1},{angle2}\n"
    ser.write(command.encode('utf-8'))
    print(f"Sent to Arduino: {command.strip()}")