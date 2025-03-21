import os
import time
import pytz
import datetime
import threading
import sys
from network import VideoStreamReceiver
from recorder import VideoRecorder
from s3_uploader import upload_file_to_s3
from vr import VRStreamingServer

def main():
    os.environ['TZ'] = 'Europe/Sofia'
    time.tzset()

    tz = pytz.timezone('Europe/Sofia')
    start_dt = datetime.datetime.now(tz)
    start_year = start_dt.strftime('%Y')
    start_month = start_dt.strftime('%m')
    start_day = start_dt.strftime('%d')
    start_time_str = start_dt.strftime('%H-%M-%S')

    video_receiver = VideoStreamReceiver(host='0.0.0.0', port=1189)
    
    temp_filename = "recording_temp.mp4"
    recorder = VideoRecorder(temp_filename, video_receiver.width, video_receiver.height, video_receiver.framerate)
    video_receiver.recorder = recorder
    print("Recorder has started, writing to:", temp_filename)

    video_receiver.start()

    vr_server = VRStreamingServer(video_receiver, host='0.0.0.0', port=5000)
    server_thread = threading.Thread(target=vr_server.run, daemon=True)
    server_thread.start()
    print("VR Socket.IO Server started on port 5000.")

    shutdown_flag = [False]

    def watch_for_q():
        while True:
            char = sys.stdin.read(1)
            if char.lower() == 'q':
                shutdown_flag[0] = True
                break

    input_thread = threading.Thread(target=watch_for_q, daemon=True)
    input_thread.start()

    # Keep the main thread alive until a keyboard interrupt is received.
    try:
        while not shutdown_flag[0]:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Shutting down.")
        server_thread.join()

    # Clean up
    video_receiver.stop()
    recorder.stop()

    # Save and upload the recorded video.
    end_dt = datetime.datetime.now(tz)
    end_time_str = end_dt.strftime('%H-%M-%S')
    final_filename = f"{start_year}-{start_month}-{start_day}__{start_time_str}__{end_time_str}.mp4"
    os.rename(temp_filename, final_filename)
    print("Recording saved as:", final_filename)

    upload_file_to_s3(final_filename, "surgery-robot-recordings", final_filename)
    print("Video uploaded to S3.")

    os.remove(final_filename)
    print("Local file removed.")

if __name__ == "__main__":
    main()
