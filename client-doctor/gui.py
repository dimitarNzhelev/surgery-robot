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

        # Create 9 buttons with the desired grid layout:
        # First row: Button1, Button2, Button3, Button4
        self.btn1 = ttk.Button(self.control_frame, text="Button1",
                               command=lambda: self.command_sender.send_udp_message('button1'))
        self.btn2 = ttk.Button(self.control_frame, text="Button2",
                               command=lambda: self.command_sender.send_udp_message('button2'))
        self.btn3 = ttk.Button(self.control_frame, text="Button3",
                               command=lambda: self.command_sender.send_udp_message('button3'))
        self.btn4 = ttk.Button(self.control_frame, text="Button4",
                               command=lambda: self.command_sender.send_udp_message('button4'))
        self.btn1.grid(row=0, column=0, padx=5, pady=5)
        self.btn2.grid(row=0, column=1, padx=5, pady=5)
        self.btn3.grid(row=0, column=2, padx=5, pady=5)
        self.btn4.grid(row=0, column=3, padx=5, pady=5)

        # Second row: Button5, Button6, Button7, Button8
        self.btn5 = ttk.Button(self.control_frame, text="Button5",
                               command=lambda: self.command_sender.send_udp_message('button5'))
        self.btn6 = ttk.Button(self.control_frame, text="Button6",
                               command=lambda: self.command_sender.send_udp_message('button6'))
        self.btn7 = ttk.Button(self.control_frame, text="Button7",
                               command=lambda: self.command_sender.send_udp_message('button7'))
        self.btn8 = ttk.Button(self.control_frame, text="Button8",
                               command=lambda: self.command_sender.send_udp_message('button8'))
        self.btn5.grid(row=1, column=0, padx=5, pady=5)
        self.btn6.grid(row=1, column=1, padx=5, pady=5)
        self.btn7.grid(row=1, column=2, padx=5, pady=5)
        self.btn8.grid(row=1, column=3, padx=5, pady=5)

        # Third row: Button9 (centered)
        self.btn9 = ttk.Button(self.control_frame, text="Button9",
                               command=lambda: self.command_sender.send_udp_message('button9'))
        # Place button9 in row 2 spanning columns 1 and 2 so that it's centered.
        self.btn9.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

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
            command = 'u'
        elif 'a' in keys:
            command = 'l'
        elif 's' in keys:
            command = 'd'
        elif 'd' in keys:
            command = 'r'
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
