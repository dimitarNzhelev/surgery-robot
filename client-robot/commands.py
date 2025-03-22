import serial
import serial.tools.list_ports
import time
import RPi.GPIO as GPIO

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
    

in1, in2, in3, in4 = 17, 18, 27, 22
step_sleep = 0.002
step_sequence = [
    [1,0,0,1],
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
]
motor_pins = [in1, in2, in3, in4]
motor_step_counter = 0

GPIO.setmode(GPIO.BCM)
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def move_stepper(steps=4096, direction=False):
    global motor_step_counter
    # Moves the stepper in the desired direction for given steps
    for _ in range(steps):
        for pin in range(4):
            GPIO.output(motor_pins[pin], step_sequence[motor_step_counter][pin])
        motor_step_counter = (motor_step_counter - 1) % 8 if direction else (motor_step_counter + 1) % 8
        time.sleep(step_sleep)
    for pin in motor_pins:
        GPIO.output(pin, GPIO.LOW)

def cleanup_gpio():
    for pin in motor_pins:
        GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()

def run_sequence3(ser):
    # This replicates the servo + stepper logic from your snippet
    set_both_servos(ser, 70, 70)
    time.sleep(0.2)
    move_stepper(2048, False)
    time.sleep(0.5)
    set_both_servos(ser, 60, 90)
    time.sleep(0.2)
    set_both_servos(ser, 60, 100)
    time.sleep(0.2)
    set_both_servos(ser, 60, 80)
    time.sleep(0.2)
    set_both_servos(ser, 60, 90)
    time.sleep(0.2)
    set_both_servos(ser, 60, 100)
    time.sleep(0.2)
    set_both_servos(ser, 60, 80)
    time.sleep(0.2)
    set_both_servos(ser, 60, 90)
    time.sleep(2)
    set_both_servos(ser, 10, 0)
    time.sleep(2)
    set_both_servos(ser, 70, 115)
    time.sleep(2)
    set_both_servos(ser, 70, 70)
    time.sleep(2)
    move_stepper(2048, True)
    time.sleep(0.5)
    set_both_servos(ser, 60, 90)
    time.sleep(0.2)
    set_both_servos(ser, 60, 100)
    time.sleep(0.2)
    set_both_servos(ser, 60, 80)
    time.sleep(0.2)
    set_both_servos(ser, 60, 90)
    time.sleep(0.2)
    set_both_servos(ser, 60, 100)
    time.sleep(0.2)
    set_both_servos(ser, 60, 80)
    time.sleep(0.2)
    set_both_servos(ser, 60, 90)
    time.sleep(2)
    set_both_servos(ser, 10, 0)
    time.sleep(1)
    set_both_servos(ser, 70, 115)
    time.sleep(1.5)
    set_both_servos(ser, 70, 70)
    time.sleep(2)

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