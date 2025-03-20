import cv2
import socket
import struct
import time
import logging
import threading
import subprocess
from typing import Optional
from camera_utils import find_available_camera
import sys
import os
import logging

def restart_application():
    logging.info("Restarting the entire application gracefully...")
    # Perform any additional cleanup if necessary before restarting.
    python = sys.executable
    os.execl(python, python, *sys.argv)


class VideoSender:
    def __init__(
        self,
        host: str,
        port: int,
        camera_index: Optional[int] = None,
        width: int = 640,
        height: int = 480,
        ffmpeg_quality: int = 5,  # Lower values indicate higher quality for MPEG-4 encoder
        framerate: int = 30,
    ) -> None:
        """
        Initialize the VideoSender with a persistent FFmpeg process for MPEG-4 encoding.
        """
        self.host = host
        self.port = port
        self.width = width
        self.height = height
        self.ffmpeg_quality = ffmpeg_quality
        self.framerate = framerate
        self._stop_event = threading.Event()
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.capture_failure_count = 0  # Track consecutive capture failures

        # Auto-detect camera if index is not provided
        if camera_index is None:
            self.camera_index = find_available_camera()
            if self.camera_index is None:
                raise RuntimeError("No available camera found.")
        else:
            self.camera_index = camera_index

        self._init_camera()
        self._init_socket()
        self._init_ffmpeg()

        # Start a dedicated thread to continuously capture raw frames
        self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        self.capture_thread.start()

        logging.info(f"VideoSender initialized on camera index {self.camera_index}.")

    def _init_camera(self):
        """Initialize the camera capture."""
        self.capture = cv2.VideoCapture(self.camera_index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def _init_socket(self):
        """Initialize the UDP socket."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _init_ffmpeg(self):
        """Initialize the persistent FFmpeg process."""
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # overwrite output
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self.width}x{self.height}",
            "-r", str(self.framerate),
            "-i", "-",  # read raw video from stdin
            "-c:v", "mpeg4",
            "-qscale:v", str(self.ffmpeg_quality),
            "-f", "mpegts",  # use MPEG-TS container for streaming
            "pipe:1"       # output to stdout
        ]
        self.ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=0
        )

    def _capture_frames(self) -> None:
        while not self._stop_event.is_set():
            ret, frame = self.capture.read()
            if ret:
                with self.frame_lock:
                    self.latest_frame = frame
                self.capture_failure_count = 0  # Reset failure count on success
            else:
                self.capture_failure_count += 1
                logging.warning("Failed to capture frame in capture thread. Failure count: %d", 
                                self.capture_failure_count)
                if self.capture_failure_count >= 10:
                    logging.error("Capture failure count reached 10. Restarting application.")
                    self.cleanup()  # Clean up resources before restarting
                    restart_application()  # Gracefully restart the entire app
                    return  # This line won't be reached as os.execl replaces the process.
            time.sleep(0.005)


    def _send_encoded_output(self) -> None:
        """
        Read encoded MPEG-4 output from FFmpeg's stdout in chunks and send them over UDP.
        Each chunk is prefixed with a timestamp and its size.
        """
        while not self._stop_event.is_set():
            try:
                chunk = self.ffmpeg_process.stdout.read(4096)
                if not chunk:
                    break  # FFmpeg process ended
                timestamp = time.time()
                timestamp_data = struct.pack('d', timestamp)
                packet = timestamp_data + struct.pack('i', len(chunk)) + chunk
                self.socket.sendto(packet, (self.host, self.port))
                logging.debug("Encoded chunk sent.")
            except Exception as e:
                logging.error("Error reading from FFmpeg stdout: %s", e)
                break

    def send_frames(self) -> None:
        """
        Continuously write raw frames to FFmpeg's stdin for encoding,
        and simultaneously send the encoded output over UDP.
        """
        logging.info("Starting video transmission using persistent FFmpeg process...")
        # Start thread for reading and sending FFmpeg's encoded output
        ffmpeg_sender_thread = threading.Thread(target=self._send_encoded_output, daemon=True)
        ffmpeg_sender_thread.start()
        try:
            while not self._stop_event.is_set():
                with self.frame_lock:
                    frame = self.latest_frame
                if frame is None:
                    continue
                try:
                    self.ffmpeg_process.stdin.write(frame.tobytes())
                except Exception as e:
                    logging.error("Error writing to FFmpeg stdin: %s", e)
                    break
                time.sleep(0.005)
        except Exception as e:
            logging.error("Error in send_frames: %s", e)
        finally:
            self.cleanup()
            ffmpeg_sender_thread.join(timeout=1)

    def _restart_process(self) -> None:
        """
        Restart the entire VideoSender process.
        This method cleans up current resources and reinitializes them.
        It runs in a separate thread so that the calling capture thread can exit.
        """
        logging.info("Restarting VideoSender process...")
        self.cleanup()
        time.sleep(1)  # Brief pause before reinitialization

        # Clear the stop event and reset failure counter
        self._stop_event.clear()
        self.capture_failure_count = 0

        # Reinitialize camera and FFmpeg, and start a new capture thread.
        self._init_camera()
        self._init_ffmpeg()
        self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
        self.capture_thread.start()
        logging.info("VideoSender process restarted successfully.")

    def stop(self) -> None:
        """Signal the sender to stop capturing and sending frames."""
        self._stop_event.set()

    def cleanup(self) -> None:
        """Release camera, socket, and FFmpeg process resources."""
        self._stop_event.set()
        # Only join capture_thread if current thread is not it
        if self.capture_thread.is_alive() and threading.current_thread() != self.capture_thread:
            self.capture_thread.join(timeout=1)
        if self.capture.isOpened():
            self.capture.release()
        if self.ffmpeg_process.poll() is None:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.terminate()
            except Exception as e:
                logging.error("Error terminating FFmpeg process: %s", e)
        self.socket.close()
        logging.info("VideoSender resources have been released.")
