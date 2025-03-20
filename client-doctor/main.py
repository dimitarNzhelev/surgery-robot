import os
import time
from network import VideoStreamReceiver, CommandSender
from gui import VideoControlGUI
from recorder import VideoRecorder
from s3_uploader import upload_file_to_s3

def main():
    # Capture the start time components
    start_year = time.strftime('%Y')
    start_day = time.strftime('%d')
    start_time_str = time.strftime('%H-%M-%S')

    # Initialize VideoStreamReceiver
    video_receiver = VideoStreamReceiver(host='0.0.0.0', port=1189)

    # Create a temporary filename for the recorder
    temp_filename = "recording_temp.mp4"
    recorder = VideoRecorder(temp_filename, video_receiver.width, video_receiver.height, video_receiver.framerate)
    video_receiver.recorder = recorder

    print("Recorder has started, writing to:", temp_filename)

    command_sender = CommandSender(message_ip="10.8.0.3", message_port=12345)
    gui = VideoControlGUI(video_receiver, command_sender)
    gui.run()

    # Once the GUI is closed, stop everything
    video_receiver.stop()
    recorder.stop()

    time.sleep(1)  # Optional small delay

    # Now determine the end time
    end_time_str = time.strftime('%H-%M-%S')

    # Generate the final filename: {year}-{day}-{time-start}-{time-end}.mp4
    final_filename = f"{start_year}-{start_day}-{start_time_str}-{end_time_str}.mp4"

    # Rename the temp file to the final filename
    os.rename(temp_filename, final_filename)
    print("Recording saved as:", final_filename)

    # Upload the final file to S3
    # upload_file_to_s3(final_filename, "surgery-robot-recordings", f"{final_filename}")
    # print("Video uploaded to S3.")

if __name__ == "__main__":
    main()