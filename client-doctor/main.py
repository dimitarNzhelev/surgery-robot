from network import VideoStreamReceiver, CommandSender
from gui import VideoControlGUI

def main():
    video_receiver = VideoStreamReceiver(host='0.0.0.0', port=1189)
    command_sender = CommandSender(message_ip="10.8.0.3", message_port=12345)
    gui = VideoControlGUI(video_receiver, command_sender)
    gui.run()

if __name__ == "__main__":
    main()
