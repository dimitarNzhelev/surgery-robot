import cv2

class VideoRecorder:
    def __init__(self, output_filename, width, height, fps):
        """
        Initialize the video recorder.
        
        Args:
            output_filename (str): Path to save the recorded video.
            width (int): Frame width.
            height (int): Frame height.
            fps (int): Frames per second.
        """
        self.output_filename = output_filename
        self.width = width
        self.height = height
        self.fps = fps
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 'mp4v' for mp4 format
        self.writer = cv2.VideoWriter(output_filename, fourcc, 90, (width, height))
        if not self.writer.isOpened():
            raise RuntimeError("Failed to open video writer.")

    def record(self, frame):
        """Write a frame to the video file."""
        self.writer.write(frame)

    def stop(self):
        """Release the video writer."""
        self.writer.release()
