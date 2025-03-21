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
        self.root.geometry("1000x800")
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')  
        self.pressed_keys = set()

        self.create_widgets()
       # self.bind_events()

    def create_widgets(self):

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

        self.video_frame = ttk.Frame(self.root)
        self.video_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.video_label = ttk.Label(self.video_frame, background="black")
        self.video_label.pack(fill="both", expand=True)

        self.control_frame = ttk.Frame(self.root)
        self.control_frame.grid(row=1, column=0, pady=10)
        self.btn1 = ttk.Button(self.control_frame, text="Left",
                               command=lambda: self.command_sender.send_udp_message('1l'))
        self.btn2 = ttk.Button(self.control_frame, text="Right",
                               command=lambda: self.command_sender.send_udp_message('1r'))
        self.btn3 = ttk.Button(self.control_frame, text="Up-1",
                               command=lambda: self.command_sender.send_udp_message('1u'))
        self.btn4 = ttk.Button(self.control_frame, text="Down-1",
                               command=lambda: self.command_sender.send_udp_message('1d'))
        self.btn1.grid(row=0, column=0, padx=5, pady=5)
        self.btn2.grid(row=0, column=1, padx=5, pady=5)
        self.btn3.grid(row=0, column=2, padx=5, pady=5)
        self.btn4.grid(row=0, column=3, padx=5, pady=5)

        self.btn5 = ttk.Button(self.control_frame, text="Up-2",
                               command=lambda: self.command_sender.send_udp_message('2u'))
        self.btn6 = ttk.Button(self.control_frame, text="Down-2",
                               command=lambda: self.command_sender.send_udp_message('2d'))
        self.btn7 = ttk.Button(self.control_frame, text="Up-3",
                               command=lambda: self.command_sender.send_udp_message('3u'))
        self.btn8 = ttk.Button(self.control_frame, text="Down-3",
                               command=lambda: self.command_sender.send_udp_message('3d'))
        self.btn5.grid(row=1, column=0, padx=5, pady=5)
        self.btn6.grid(row=1, column=1, padx=5, pady=5)
        self.btn7.grid(row=1, column=2, padx=5, pady=5)
        self.btn8.grid(row=1, column=3, padx=5, pady=5)
        self.btn9 = ttk.Button(self.control_frame, text="Comb",
                               command=lambda: self.command_sender.send_udp_message('3c'))
        self.btn9.grid(row=2, column=1, columnspan=2, padx=5, pady=5)
    def update_image(self):
        try:
            if not self.video_receiver.decoded_frame_queue.empty():
                frame = self.video_receiver.decoded_frame_queue.get()
                cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(cv_image)
                
                new_img_width = 800
                new_img_height = 600

                try:
                    resample = Image.Resampling.LANCZOS
                except AttributeError:
                    resample = Image.LANCZOS
                pil_image = pil_image.resize((new_img_width, new_img_height), resample)
                imgtk = ImageTk.PhotoImage(image=pil_image)
                self.video_label.imgtk = imgtk  
                self.video_label.configure(image=imgtk)
                new_window_width = new_img_width + 40 
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
