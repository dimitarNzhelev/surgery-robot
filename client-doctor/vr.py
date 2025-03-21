import cv2
import base64
import time
import logging
import threading

from flask import Flask, request
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

        # Create Flask + SocketIO App
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "some-secret-key"

        self.socketio = SocketIO(self.app, async_mode='threading', cors_allowed_origins='*')

        @self.app.route('/')
        def index():
            return self.render_aframe_page()

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

        @self.socketio.on('start_connection')
        def on_start_connection(data):
            logger.info('[Socket.IO] Received start_connection message: %s', data)
            sid = request.sid
            threading.Thread(target=self.broadcast_frames, args=(sid,), daemon=True).start()

  

    def render_aframe_page(self):
        """
        Returns HTML that:
         - Loads A-Frame and Socket.IO,
         - Creates a <canvas> within A-Frame's asset management,
         - Receives 'video_frame' events and draws them onto the canvas,
         - Applies the canvas as a texture to an <a-plane>.
        """
        html = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>A-Frame VR Stream (Socket.IO)</title>
    <!-- Load A-Frame -->
    <script src="https://aframe.io/releases/1.4.0/aframe.min.js"></script>
    <!-- Load Socket.IO from CDN -->
    <script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
  </head>
  <body>
    <a-scene>
      <a-assets>
        <canvas id="videoCanvas" width="640" height="480"></canvas>
      </a-assets>
      <a-plane id="videoPlane" src="#videoCanvas" 
               position="0 1.6 -2" 
               width="4" 
               height="3">
      </a-plane>
      <a-sky color="#ECECEC"></a-sky>
    </a-scene>
    <script>
      const canvas = document.getElementById('videoCanvas');
      const ctx = canvas.getContext('2d');

      const socket = io({
        transports: ['websocket'],
        forceNew: true,
        reconnection: true,
      });

      socket.emit('start_connection', 'The client is ready to receive video frames.');

      socket.on('connect', () => {
        console.log('[Socket.IO] Connected to VR streaming server.');
      });

      socket.on('disconnect', () => {
        console.log('[Socket.IO] Disconnected from server.');
      });

      function base64ToBlob(base64, mime) {
        const byteChars = atob(base64);
        const byteArrays = [];

        for (let offset = 0; offset < byteChars.length; offset += 512) {
          const slice = byteChars.slice(offset, offset + 512);
          const byteNumbers = new Array(slice.length);
          for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
          }
          byteArrays.push(new Uint8Array(byteNumbers));
        }

        return new Blob(byteArrays, { type: mime });
      }

      socket.on('video_frame', (base64JPEG) => {
        const blob = base64ToBlob(base64JPEG, 'image/jpeg');
        const url = URL.createObjectURL(blob);
        const img = new Image();
        img.crossOrigin = 'anonymous';

        img.onload = function () {
          console.log('[Client] Image loaded');
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          URL.revokeObjectURL(url);

          const videoPlane = document.querySelector('#videoPlane');
          const material = videoPlane.getObject3D('mesh')?.material;
          if (material?.map) {
            material.map.needsUpdate = true;
          }
        };

        img.onerror = function () {
          console.error('[Client] Failed to load image');
        };

        img.src = url;
      });

      document.addEventListener('keydown', (e) => {
        socket.emit('control_message', { type: 'keydown', key: e.key });
      });
    </script>

    </body>
</html>
        """
        return html

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
        self.socketio.run(self.app, host=self.host, port=self.port)

    def stop(self):
        """
        Stop the Socket.IO server.
        """
        logger.info("[Socket.IO] Stopping A-Frame VRStreamingServer.")
        self.socketio.stop()
        