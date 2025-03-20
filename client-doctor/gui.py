import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2

class VideoControlGUI:
    def __init__(self, video_receiver, command_sender):
        self.video_receiver = video_receiver
        self.command_sender = command_sender
        self.root = tk.Tk()
        self.root.title("Video Control Interface")
        # Start with a base geometry; grid layout will manage resizing.
        self.root.geometry("1000x800")
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')  # Use a modern theme
        self.pressed_keys = set()

        self.create_widgets()
        self.bind_events()

    def create_widgets(self):
        # Configure grid on the root window
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

        # Video frame in row 0, expands with the window
        self.video_frame = ttk.Frame(self.root)
        self.video_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.video_label = ttk.Label(self.video_frame, background="black")
        self.video_label.pack(fill="both", expand=True)

        # Control frame in row 1; fixed height so buttons remain visible.
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.grid(row=1, column=0, pady=10)

        # Directional buttons arranged in a grid layout within the control frame.
        self.btn_up = ttk.Button(self.control_frame, text="↑", command=lambda: self.command_sender.send_udp_message('u'))
        self.btn_left = ttk.Button(self.control_frame, text="←", command=lambda: self.command_sender.send_udp_message('l'))
        self.btn_down = ttk.Button(self.control_frame, text="↓", command=lambda: self.command_sender.send_udp_message('d'))
        self.btn_right = ttk.Button(self.control_frame, text="→", command=lambda: self.command_sender.send_udp_message('r'))

        self.btn_up.grid(row=0, column=1, padx=5, pady=5)
        self.btn_left.grid(row=1, column=0, padx=5, pady=5)
        self.btn_down.grid(row=1, column=1, padx=5, pady=5)
        self.btn_right.grid(row=1, column=2, padx=5, pady=5)

    def bind_events(self):
        self.root.bind('<KeyPress>', self.handle_key_press)
        self.root.bind('<KeyRelease>', self.handle_key_release)

    def handle_key_press(self, event):
        key = event.keysym.lower()
        self.pressed_keys.add(key)
        self.send_direction_command()

    def handle_key_release(self, event):
        key = event.keysym.lower()
        self.pressed_keys.discard(key)
        self.send_direction_command()

    def send_direction_command(self):
        keys = self.pressed_keys
        if 'w' in keys and 'd' in keys:
            command = 'ur'
        elif 'w' in keys and 'a' in keys:
            command = 'ul'
        elif 's' in keys and 'a' in keys:
            command = 'dl'
        elif 's' in keys and 'd' in keys:
            command = 'dr'
        elif 'w' in keys:
            command = 'u0'
        elif 'a' in keys:
            command = '0l'
        elif 's' in keys:
            command = 'd0'
        elif 'd' in keys:
            command = '0r'
        else:
            return
        self.command_sender.send_udp_message(command)

    def update_image(self):
        try:
            if not self.video_receiver.decoded_frame_queue.empty():
                frame = self.video_receiver.decoded_frame_queue.get()
                cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(cv_image)
                
                # Define new, larger dimensions for the video image
                new_img_width = 800
                new_img_height = 600

                try:
                    resample = Image.Resampling.LANCZOS
                except AttributeError:
                    resample = Image.LANCZOS
                pil_image = pil_image.resize((new_img_width, new_img_height), resample)
                imgtk = ImageTk.PhotoImage(image=pil_image)
                self.video_label.imgtk = imgtk  # Prevent garbage collection
                self.video_label.configure(image=imgtk)

                # Update window geometry: add extra height for control buttons.
                new_window_width = new_img_width + 40  # extra padding
                new_window_height = new_img_height + 150
                self.root.geometry(f"{new_window_width}x{new_window_height}")
        except Exception as e:
            print(f"Error updating image: {e}")
        finally:
            self.root.after(10, self.update_image)

    def run(self):
        self.video_receiver.start()
        self.update_image()
        self.root.mainloop()
