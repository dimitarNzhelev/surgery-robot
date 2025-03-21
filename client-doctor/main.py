import os
import time
import pytz
import datetime
from network import VideoStreamReceiver, CommandSender
from gui import VideoControlGUI
from recorder import VideoRecorder
from s3_uploader import upload_file_to_s3

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

    command_sender = CommandSender(message_ip="10.8.0.3", message_port=12345)
    gui = VideoControlGUI(video_receiver, command_sender)
    gui.run()

    video_receiver.stop()
    recorder.stop()

    time.sleep(1) 

    end_dt = datetime.datetime.now(tz)
    end_time_str = end_dt.strftime('%H-%M-%S')

    final_filename = f"{start_year}-{start_month}-{start_day}__{start_time_str}__{end_time_str}.mp4"

    os.rename(temp_filename, final_filename)
    print("Recording saved as:", final_filename)
    upload_file_to_s3(final_filename, "surgery-robot-recordings", f"{final_filename}")
    print("Video uploaded to S3.")

    os.remove(final_filename)
    print("Local file removed.")

if __name__ == "__main__":
    main()