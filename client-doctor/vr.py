import cv2
import base64
import time
import logging
import threading
from network import CommandSender

from flask import Flask, request, send_file
from flask_socketio import SocketIO, emit

# Configure the logger for this module.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class VRStreamingServer:
    def __init__(self, video_receiver, host='0.0.0.0', port=5000):
        """
        A Socket.IO–based VR Streaming Server using A-Frame.

        Args:
            video_receiver (VideoStreamReceiver): 
                Has .decoded_frame_queue (Queue) with frames, 
                plus a ._running bool controlling frame flow.
            host (str): Host to bind the Flask server to.
            port (int): Port to listen on.
        """
        self.video_receiver = video_receiver
        self.host = host
        self.port = port
        self.command_sender = CommandSender()

        # Create Flask + SocketIO App
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "some-secret-key"

        self.socketio = SocketIO(self.app, async_mode='threading', cors_allowed_origins='*')

        @self.app.route('/')
        def index():
            return send_file('vr.html')

        # Socket.IO events
        @self.socketio.on('connect')
        def on_connect():
            logger.info('[Socket.IO] Client connected.')

        @self.socketio.on('disconnect') 
        def on_disconnect():
            logger.info('[Socket.IO] Client disconnected.')

        @self.socketio.on('control_message')
        def on_control_message(data):
            logger.info('[Socket.IO] Received control message: %s', data)
            self.command_sender.send_udp_message(data)


        @self.socketio.on('start_connection')
        def on_start_connection(data):
            logger.info('[Socket.IO] Received start_connection message: %s', data)
            sid = request.sid
            threading.Thread(target=self.broadcast_frames, args=(sid,), daemon=True).start()

  
    def broadcast_frames(self, sid):
        """
        Continuously read frames from video_receiver.decoded_frame_queue,
        encode them as JPEG then base64, and emit to all Socket.IO clients.
        """
        with self.app.app_context():
          print("[Socket.IO] Broadcasting video frames...")
          frame_count = 0
          while self.video_receiver._running:
              try:
                  # Attempt to get a frame from the queue.
                  frame = self.video_receiver.decoded_frame_queue.get(timeout=0.1)
                  logger.debug("Frame received from queue.")
              except Exception as e:
                  # Log that no frame was available (at debug level to avoid spamming).
                  logger.debug("No frame available in queue: %s", e)
                  self.socketio.sleep(0.1)
                  continue

              success, jpeg = cv2.imencode('.jpg', frame)
              if not success:
                  logger.warning("Failed to encode frame to JPEG.")
                  continue
              
              encoded = base64.b64encode(jpeg.tobytes()).decode('utf-8')
              frame_count += 1
              self.socketio.emit('video_frame', encoded, to=sid, callback=(lambda: print("Frame sent.")))
              self.socketio.sleep(0.03)
    
    def run(self):
        """
        Start the Socket.IO server. This should be run on a separate thread if the main thread is busy.
        """
        logger.info("[Socket.IO] A-Frame VRStreamingServer running on %s:%s", self.host, self.port)
        self.socketio.run(self.app, host=self.host, port=self.port, ssl_context=('localhost+2.pem', 'localhost+2-key.pem'))

    def stop(self):
        """
        Stop the Socket.IO server.
        """
        logger.info("[Socket.IO] Stopping A-Frame VRStreamingServer.")
        self.socketio.stop()
        