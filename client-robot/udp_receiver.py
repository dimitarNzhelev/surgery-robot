import socket
import logging
import threading

class UdpReceiver:
    def __init__(self, listen_ip: str, listen_port: int) -> None:
        """
        Initialize the UDP receiver.
        
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
                    message = data.decode()
                    logging.info(f"Received message: {message} from {addr}")
                except UnicodeDecodeError as decode_error:
                    logging.error(f"Failed to decode message from {addr}: {decode_error}")
        except Exception as e:
            logging.error(f"Error in UDP receiver: {e}")
        finally:
            self.cleanup()

    def stop(self) -> None:
        """Signal the receiver to stop listening."""
        self._stop_event.set()

    def cleanup(self) -> None:
        """Close the UDP socket."""
        self.socket.close()
        logging.info("UDP receiver socket closed.")
