import socket
import logging
import threading
import time
import commands  # Import functions from command.py

class UdpReceiver:
    def __init__(self, listen_ip: str, listen_port: int) -> None:
        """
        Initialize the UDP receiver and establish a persistent connection to the Arduino.
        
        Args:
            listen_ip (str): IP address to bind the listener.
            listen_port (int): Port number for incoming messages.
        """
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self._stop_event = threading.Event()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.listen_ip, self.listen_port))
        logging.info(f"UDP receiver bound to {self.listen_ip}:{self.listen_port}")

        # Establish a persistent connection to Arduino
        arduino_port = commands.find_arduino_serial_port()
        if arduino_port:
            try:
                self.arduino_ser = commands.serial.Serial(arduino_port, 9600, timeout=1)
                self.arduino_ser.reset_input_buffer()
                logging.info(f"Arduino connected on {arduino_port}")
            except Exception as e:
                logging.error(f"Failed to connect to Arduino on {arduino_port}: {e}")
                self.arduino_ser = None
        else:
            logging.error("Arduino not found. Servo commands will not be executed.")
            self.arduino_ser = None

        # Lock to prevent concurrent servo sequence executions
        self.command_lock = threading.Lock()

    def run(self) -> None:
        """Listen for UDP messages until stopped."""
        logging.info("UDP receiver is listening for messages...")
        try:
            while not self._stop_event.is_set():
                self.socket.settimeout(1.0)  # Timeout to check for stop signal
                try:
                    data, addr = self.socket.recvfrom(1024)
                except socket.timeout:
                    continue
                try:
                    message = data.decode().strip()
                    logging.info(f"Received message: {message} from {addr}")
                    # Process the message asynchronously to keep the listener responsive.
                    threading.Thread(target=self.process_message, args=(message,), daemon=True).start()
                except UnicodeDecodeError as decode_error:
                    logging.error(f"Failed to decode message from {addr}: {decode_error}")
        except Exception as e:
            logging.error(f"Error in UDP receiver: {e}")
        finally:
            self.cleanup()

    def process_message(self, message: str) -> None:
        """
        Process the received message by mapping it to a servo command sequence.
        
        Args:
            message (str): The received command message.
        """
        sequence = commands.messageToSequence(message)
        if sequence == "stop":
            logging.info("Received 'stop' or unrecognized command; no action taken.")
            return

        # Define servo sequences based on the command.
        if sequence == "sequence1":
            servo1 = [70, 40, 70, 70, 10, 70]
            servo2 = [70, 70, 50, 90, 0, 90]
            sleep_times = [2, 2, 2, 2, 1, 2]

        if sequence == "sequence2":
            servo1 = [110, 110, 110, 110, 110, 70]
            servo2 = [140, 125, 155, 125, 140, 70]
            sleep_times = [2, 0.2, 0.2, 0.2, 2, 2]

        elif sequence in ["sequence3", "sequence4"]:
            logging.info(f"{sequence} is not implemented; command ignored.")
            return
        else:
            logging.info("Unknown sequence; no action taken.")
            return

        # Execute the servo sequence if an Arduino connection is available.
        if self.arduino_ser is None:
            logging.error("No Arduino connection available; cannot execute servo sequence.")
            return

        # Use a lock to ensure only one servo sequence runs at a time.
        if not self.command_lock.acquire(blocking=False):
            logging.warning("Another servo command sequence is currently running; ignoring new command.")
            return

        try:
            logging.info(f"Executing {sequence}...")
            for i in range(len(servo1)):
                commands.set_both_servos(self.arduino_ser, servo1[i], servo2[i])
                time.sleep(sleep_times[i])
            logging.info(f"{sequence} execution completed.")
        except Exception as e:
            logging.error(f"Error executing {sequence}: {e}")
        finally:
            self.command_lock.release()

    def stop(self) -> None:
        """Signal the receiver to stop listening."""
        self._stop_event.set()

    def cleanup(self) -> None:
        """Close the UDP socket."""
        self.socket.close()
        logging.info("UDP receiver socket closed.")
