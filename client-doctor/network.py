import socket
import struct
import threading
import queue
import time
import cv2
import numpy as np
import subprocess

class VideoStreamReceiver:
    def __init__(self, host='0.0.0.0', port=1189, width=640, height=480, framerate=30):
        """
        Initialize the VideoStreamReceiver to decode MPEG-TS compressed frames.
        """
        self.host = host
        self.port = port
        self.width = width
        self.height = height
        self.framerate = framerate

        # Queue for holding received MPEG-TS chunks.
        self.mpeg_queue = queue.Queue()
        # Queue for decoded frames (raw BGR frames).
        self.decoded_frame_queue = queue.Queue(maxsize=2)
        self._running = True

        # Start persistent FFmpeg process to decode MPEG-TS stream into raw frames.
        ffmpeg_cmd = [
            "ffmpeg",
            "-loglevel", "quiet",
            "-f", "mpegts",
            "-i", "pipe:0",               # Read MPEG-TS stream from stdin.
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self.width}x{self.height}",
            "pipe:1"                      # Output raw video frames to stdout.
        ]
        self.ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=0
        )
        self.recorder = None

    def start(self):
        """
        Start threads:
          - UDP receiver thread to get MPEG-TS chunks.
          - FFmpeg feed thread to write chunks to FFmpeg's stdin.
          - FFmpeg reader thread to decode raw frames from FFmpeg's stdout.
        """
        threading.Thread(target=self.receive_video, daemon=True).start()
        threading.Thread(target=self._feed_ffmpeg, daemon=True).start()
        threading.Thread(target=self._read_ffmpeg, daemon=True).start()

    def stop(self):
        """Stop the receiver and clean up resources."""
        self._running = False
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.terminate()
            except Exception as e:
                print(f"Error terminating FFmpeg process: {e}")

    def receive_video(self):
        """
        Listen for UDP packets containing MPEG-TS chunks.
        Each packet has a header:
          - 8 bytes: timestamp (double)
          - 4 bytes: chunk size (int)
        Followed by the MPEG-TS data.
        """
        buffSize = 65535
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))
        print('Waiting for MPEG-TS video frames...')
        try:
            print(self._running)
            while self._running:
                packet, _ = sock.recvfrom(buffSize)
                # print(f"Received UDP packet: {len(packet)} bytes")
                if len(packet) < 12:
                    continue
                timestamp, size = struct.unpack('di', packet[:12])
                data = packet[12:]
                if len(data) != size:
                    continue
                self.mpeg_queue.put(data)
        except Exception as e:
            print(f"Video receive error: {e}")
        finally:
            sock.close()

    def _feed_ffmpeg(self):
        """
        Continuously read MPEG-TS chunks from the queue and write them to FFmpeg's stdin.
        """
        while self._running:
            try:
                data = self.mpeg_queue.get(timeout=0.1)
                # print(f"Received MPEG-TS chunk: {len(data)} bytes")
            except queue.Empty:
                continue
            try:
                if self.ffmpeg_process.stdin:
                    self.ffmpeg_process.stdin.write(data)
                    self.ffmpeg_process.stdin.flush()  # Ensure data is sent immediately
            except Exception as e:
                print(f"FFmpeg stdin write error: {e}")
                break

    def _read_exactly(self, num_bytes):
        """
        Utility to read exactly num_bytes from FFmpeg's stdout.
        """
        data = b''
        while len(data) < num_bytes:
            chunk = self.ffmpeg_process.stdout.read(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _read_ffmpeg(self):
        """
        Read raw video frames from FFmpeg's stdout.
        Each frame has a fixed size: width * height * 3 bytes (BGR24).
        """
        frame_size = self.width * self.height * 3
        while self._running:
            try:
                raw_frame = self._read_exactly(frame_size)
                if raw_frame is None or len(raw_frame) != frame_size:
                    continue
                frame = np.frombuffer(raw_frame, dtype=np.uint8)
                frame = frame.reshape((self.height, self.width, 3))
                if self.recorder:
                    self.recorder.record(frame)
                if self.decoded_frame_queue.full():
                    try:
                        self.decoded_frame_queue.get_nowait()  # Remove oldest frame.
                    except queue.Empty:
                        pass
                self.decoded_frame_queue.put(frame)
            except Exception as e:
                print(f"FFmpeg stdout read error: {e}")
                break

class CommandSender:
    def __init__(self, message_ip="10.8.0.3", message_port=12345):
        self.message_ip = message_ip
        self.message_port = message_port

    def send_udp_message(self, command):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"Sending command: {command}")
        try:
            sock.sendto(command.encode(), (self.message_ip, self.message_port))
        except Exception as e:
            print(f"Error sending message: {e}")
        finally:
            sock.close()
