import logging
import threading
import time
from video_sender import VideoSender
from udp_receiver import UdpReceiver

def setup_logging() -> None:
    """Configure logging format and level."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main() -> None:
    """Main entry point for starting video transmission and UDP message listening."""
    setup_logging()

    # Configuration
    HOST = '10.8.0.2'  # Target host IP (e.g., Raspberry Pi)
    PORT = 1189
    listen_ip = "0.0.0.0"
    listen_port = 12345

    try:
        video_sender = VideoSender(HOST, PORT)
    except RuntimeError as e:
        logging.error(e)
        return

    udp_receiver = UdpReceiver(listen_ip, listen_port)

    video_thread = threading.Thread(target=video_sender.send_frames, daemon=True)
    video_thread.start()
    logging.info("VideoSender thread started.")

    udp_thread = threading.Thread(target=udp_receiver.run, daemon=True)
    udp_thread.start()
    logging.info("UdpReceiver thread started.")

    try:
        while True:
            time.sleep(1)  # Keep the main thread alive.
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received, stopping services...")
        video_sender.stop()
        udp_receiver.stop()

        video_thread.join()
        udp_thread.join()
        logging.info("Shutdown complete.")

if __name__ == "__main__":
    main()
