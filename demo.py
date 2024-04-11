#GUI
import tkinter as tk
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import customtkinter
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog

#IMG PROCESSING
import cv2
import numpy as np
from plotter import HMPlotter

#SYSTEM FUNCTIONS
import os
import sim
import time

#FILE TRACKING
import ntpath
from pydispatch import dispatcher
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

hm_plotter = HMPlotter(name="Tile Spike Heatmap",width=8,height=4)

class SANAFEApp(TkinterDnD.Tk):

    frames = {}
    current = None
    bg = "black"

    def __init__(self):
        super().__init__()
        self.sanafe = None

        # customtkinter.set_appearance_mode("System")
        # customtkinter.set_default_color_theme("blue")

        self.title("SANA-FE Demo")
        self.configure(background="#2b2b2b")
        self.geometry("1600x1100")

        self.cap = cv2.VideoCapture(0)  # 0 corresponds to the default camera

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_container = customtkinter.CTkFrame(self, corner_radius=8, fg_color=self.bg)
        main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.selection_panel = customtkinter.CTkFrame(main_container, width=280, corner_radius=8, fg_color=self.bg)
        self.selection_panel.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=18, pady=10)

        self.view_panel = customtkinter.CTkFrame(main_container, corner_radius=8, fg_color="#212121")
        self.view_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.view_panel.configure(border_width = 1)
        self.view_panel.configure(border_color = "#323232")

        bt_demo_frame = customtkinter.CTkButton(self.selection_panel, command= self.demo_button)
        bt_demo_frame.configure(height = 40)
        bt_demo_frame.configure(text = "DEMO")
        bt_demo_frame.grid(pady = 3, row=1, column=0)
        bt_home_frame = customtkinter.CTkButton(self.selection_panel, command= self.home_button)
        bt_home_frame.configure(height = 40)
        bt_home_frame.configure(text = "HOME")
        bt_home_frame.grid(pady = 3, row=0, column=0)

        self.home_frame = customtkinter.CTkFrame(self, bg_color="black", width=1600, height=1100)
        self.home_frame.configure(corner_radius = 8)
        self.home_frame.configure(border_width = 2)
        self.home_frame.configure(border_color = "#323232")
        self.home_frame.padx = 8
        # self.home_frame.grid(row=0, column=0)
        self.home_frame.columnconfigure(0, weight=1)
        self.home_frame.rowconfigure(0, weight=1)

        title_label2 = tk.Label(self.home_frame, text="SANA-FE", font=("Helvetica", 24),foreground="white",background="#2b2b2b", width= 1600)
        title_label2.grid(row=0, column=0, columnspan=3, pady=20)

        title_label2 = tk.Label(self.home_frame, text="*OUTPUT DATA*", font=("Helvetica", 12),foreground="white",background="#2b2b2b")
        title_label2.grid(row=1, column=0, columnspan=2, pady=20)

        #set params
        self.timestep_entry_label = tk.Label(self.home_frame, text="Timesteps")
        self.timestep_entry_label.grid(row=2, column=0, sticky="e")
        #tk.Label(master, text="Last Name").grid(row=1)

        self.timestep_entry = tk.Entry(self.home_frame)
        self.timestep_entry.grid(row=2, column=1)
        #e2 = tk.Entry(master)

        #RUN BUTTON
        bt_run = customtkinter.CTkButton(self.home_frame, command= self.run_button)
        bt_run.configure(height = 80)
        bt_run.configure(text = "RUN TIMESTEPS")
        bt_run.grid(pady = 3, row=3, column=2)

        bt_init = customtkinter.CTkButton(self.home_frame, command= self.init_button)
        bt_init.configure(height = 80)
        bt_init.configure(text = "LOAD FILES")
        bt_init.grid(pady = 3, row=2, column=2)

        self.canvas = ttk.Label(self.home_frame, width = 600)
        self.canvas.grid(row=1, column=2, columnspan=1, pady=20,padx=20)
        self.img = ImageTk.PhotoImage(Image.open("hm.png"))
        self.canvas.config(image=self.img)
        self.canvas.image = self.img

        ##### FILE INPUTS #####
        # self.arch_input = tk.Listbox(self.home_frame)
        # self.arch_input.insert(1, "drag arch file here")
        # self.arch_input.drop_target_register(DND_FILES)
        # self.arch_input.dnd_bind('<<Drop>>', self.drop_arch)
        self.arch_label = Label(self.home_frame, 
                            text = "Architecture File",
                            width = 50, height = 4, 
                            fg = "blue")
        self.arch_label.grid(row=3, column=0, columnspan=1, pady=20,padx=20, sticky="e")
        self.arch_input = customtkinter.CTkButton(self.home_frame, command= self.upload_arch)
        self.arch_input.configure(height = 80)
        self.arch_input.configure(text = "UPLOAD ARCH")
        self.arch_input.grid(pady = 3, row=2, column=2)
        self.arch_input.grid(row=4, column=0, columnspan=1, pady=20,padx=20, sticky="e")
        # self.snn_input = tk.Listbox(self.home_frame)
        # self.snn_input.insert(1, "drag snn file here")
        # self.snn_input.drop_target_register(DND_FILES)
        # self.snn_input.dnd_bind('<<Drop>>', self.drop_snn)
        self.snn_label = Label(self.home_frame, 
                            text = "SNN File",
                            width = 50, height = 4, 
                            fg = "blue")
        self.snn_label.grid(row=3, column=1, columnspan=1, pady=20,padx=20, sticky="e")
        self.snn_input = customtkinter.CTkButton(self.home_frame, command= self.upload_snn)
        self.snn_input.configure(height = 80)
        self.snn_input.configure(text = "UPLOAD SNN")
        self.snn_input.grid(pady = 3, row=2, column=2)
        self.snn_input.grid(row=4, column=1, columnspan=1, pady=20,padx=20)

        self.demo_frame = customtkinter.CTkFrame(self, bg_color="black", width=1600, height=1100)
        self.demo_frame.configure(corner_radius = 8)
        self.demo_frame.configure(border_width = 2)
        self.demo_frame.configure(border_color = "#323232")
        self.demo_frame.padx = 8
        # self.demo_frame.grid(row=0, column=0)
        self.demo_frame.columnconfigure(2, weight=1)
        self.demo_frame.rowconfigure(2, weight=1)

        # TITLE
        title_label = tk.Label(self.demo_frame, text="Gesture Demo", font=("Helvetica", 24),foreground="white",background="#2b2b2b")
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        #VIDEO 1
        self.video1_label = ttk.Label(self.demo_frame, width= 660)
        self.video1_label.grid(row=1, column=0)

        #VIDEO 2
        self.video2_label = ttk.Label(self.demo_frame, width= 660)
        self.video2_label.grid(row=1, column=1)

        #OUTPUT
        self.demo_label = tk.Label(self.demo_frame, text="Gesture Output", font=("Helvetica", 40),foreground="white",background="#2b2b2b")
        self.demo_label.grid(row=2, column=0, columnspan=2, pady=20)
        self.frame_list = []

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame,  cv2.COLOR_BGR2GRAY)
            frame = cv2.GaussianBlur(frame, (5, 5), 0)
            frame = cv2.resize(frame, (640, 640))

            self.prev_frame = frame.copy()

            diff = cv2.absdiff(frame, self.prev_frame)
            threshold = 30
            _, thresholded = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

            self.photo2 = ImageTk.PhotoImage(image=Image.fromarray(thresholded))
            self.video2_label.config(image=self.photo2)
            self.video2_label.image = self.photo2

        self.home_button()

        architecture = "arch/loihi.yaml" #self.arch_input.get(0)
        snn = "snn/dvs_gesture_32x32.net" #self.snn_input.get(0)
        spikes = False
        voltages = False
        self.sanafe_demo = sim.run_from_gui(architecture, snn,
            spike_trace=spikes, potential_trace=voltages)
        print("initialized demo simulator")

        self.update()

    def upload_arch(self):
        filename = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a File",
                                          filetypes = (("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
        self.arch_label.configure(text="File Opened: "+filename)
        pass

    def upload_snn(self):
        filename = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a File",
                                          filetypes = (("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
        self.snn_label.configure(text="File Opened: "+filename)
        pass

    def init_button(self):
        architecture = "arch/loihi.yaml" #self.arch_input.get(0)
        snn = "snn/dvs_gesture_32x32.net" #self.snn_input.get(0)
        spikes = False
        voltages = False

        hm_plotter.reset()
        self.img = ImageTk.PhotoImage(Image.open("hm.png"))
        self.canvas.config(image=self.img)
        self.canvas.image = self.img

        self.sanafe = sim.run_from_gui(architecture, snn,
            spike_trace=spikes, potential_trace=voltages)

        print("initialized simulator")
        pass

    def run_button(self):
        # hm_plotter.reset()
        # self.img = ImageTk.PhotoImage(Image.open("hm.png"))
        # self.canvas.config(image=self.img)
        # self.canvas.image = self.img
        timesteps = int(self.timestep_entry.get())
        if self.sanafe is not None:
            self.sanafe.run_timesteps(timesteps)
            self.sanafe.run_summary()
            print("run success")
        else:
            print("run error")
        
       # p = HMPlotter(8,4)
        pass

    def demo_button(self):
        if self.current is not None:
            self.current.pack_forget()
            self.current = self.demo_frame
            self.current.pack(in_=self.view_panel, side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)
        else:
            self.current = self.demo_frame
            self.current.pack(in_=self.view_panel, side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)

    def home_button(self):
        if self.current is not None:
            self.current.pack_forget()
            self.current = self.home_frame
            self.current.pack(in_=self.view_panel, side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)
        else:
            self.current = self.home_frame
            self.current.pack(in_=self.view_panel, side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)
            

    def drop_arch(self, event):
        if event.data:
            print('Dropped arch data:\n', event.data)
            #print_event_info(event)
            if event.widget == self.arch_input:
                files = self.arch_input.tk.splitlist(event.data)
                for f in files:
                    if os.path.exists(f):
                        print('Dropped file: "%s"' % f)
                        self.arch_input.insert('end', f)
                    else:
                        print('Not dropping file "%s": file does not exist.' % f)
            else:
                print('Error: reported event.widget not known')
        return event.action

    def drop_snn(self, event):
        if event.data:
            print('Dropped ssn data:\n', event.data)
            #print_event_info(event)
            if event.widget == self.snn_input:
                files = self.snn_input.tk.splitlist(event.data)
                for f in files:
                    if os.path.exists(f):
                        print('Dropped file: "%s"' % f)
                        self.snn_input.insert('end', f)
                    else:
                        print('Not dropping file "%s": file does not exist.' % f)
            else:
                print('Error: reported event.widget not known')
        return event.action

    def consume_frames(self):
        outputs = []
        for frame in self.frame_list:
            for f in range(len(frame)):
                b = 0 
                if frame[f] != 0:
                    b = 1
                    self.sanafe_demo.update_neuron(0, f, ["input_spike=10.0"], 1)
            self.sanafe_demo.run_timesteps(1)

            res = self.sanafe_demo.get_status(5)
            for i in range(len(res)):
                if(res[i] == 2): outputs.append(i)

        print(outputs)
        self.frame_list = []

    def update(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.GaussianBlur(frame, (5, 5), 0)
            frame = cv2.resize(frame, (640, 640))
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.video1_label.config(image=self.photo)
            self.video1_label.image = self.photo

            diff = cv2.absdiff(frame, self.prev_frame)
            threshold = 30
            _, thresholded = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

            start = time.time()
            flattened = cv2.resize(thresholded, (32, 32))
            #flattened = flattened.mean(axis=(1,3))
            flattened = flattened.flatten()
            # for f in range(len(flattened)):
            #     b = 0 
            #     if flattened[f] != 0: b = 1
            #     self.sanafe_demo.update_neuron(0, f, ["input_spike=5.0"], 1)

            self.frame_list.append(flattened)
            if(len(self.frame_list) >= 50): self.consume_frames()

            end = time.time()
            #self.sanafe_demo.run_timesteps(1)
            #self.sanafe_demo.run_summary()
            complete = time.time()
            print("Send to Sim Time:")
            print(end-start)
            print("Total Timestep:")
            print(complete-start)
            # print(self.sanafe_demo.get_status(5))
            # self.demo_label.configure(text = self.sanafe_demo.get_status(5))

            self.photo2 = ImageTk.PhotoImage(image=Image.fromarray(thresholded))
            self.video2_label.config(image=self.photo2)
            self.video2_label.image = self.photo2

            self.prev_frame = frame.copy()
            
        self.video1_label.after(100, self.update)

MYHANDLER_SENDER = 'myhandler_sender'
MYHANDLER_SIGNAL = 'myhandler_signal'
TEST_FILE = 'spikes.csv'
TEST_DIR = '/Documents/SANA-FE/'
THRESHOLD_TIME = 0.01

class FileUpdateHandler(FileSystemEventHandler):
    ''' handle events from the spike file '''
    def __init__(self, app):
        self.app = app
        self.start_time = time.time()

    def on_modified(self, event):
        now_time = time.time()
        # filter out multiple modified events occuring for a single file operation
        # if (now_time - self.start_time) < THRESHOLD_TIME:
        #     print('repeated event, not triggering')
        #     return
        changed_file = ntpath.basename(event.src_path)
        if changed_file == TEST_FILE:
            print('changed file: {}'.format(changed_file))
            print('event type: {}'.format(event.event_type))
            with open(changed_file, 'r') as f:
                lines = f.readlines()
                last_line = ""
                l = []
                if len(lines)>1:
                    last_line = lines[-1]
                    l = list(map(int, last_line.split(',')))
                    l = np.reshape(np.array(l), (4,8)) #TODO: generalize
                    hm_plotter.add(l)
                    hm_plotter.update_img()
                elif len(lines)==1:
                    last_line = lines[0]
                    l = list(map(int, last_line.split(',')))
                    l = np.reshape(np.array(l), (4,8)) #TODO: generalize
                    hm_plotter.add(l)
                    hm_plotter.update_img()
                app.img = ImageTk.PhotoImage(Image.open("hm.png"))
                app.canvas.config(image=app.img)
                app.canvas.image = app.img
                print(hm_plotter.state)
            message = '{} changed'.format(changed_file)
            dispatcher.send(message=message, signal=MYHANDLER_SIGNAL, sender=MYHANDLER_SENDER)
        self.start_time = now_time

def dispatcher_receive(message):
    print('received dispatch: {}'.format(message))
    # read in the altered file

if __name__ == "__main__":
    app = SANAFEApp()

    #event_handler = FileUpdateHandler(app=app)
    #dispatcher.connect(dispatcher_receive, signal=MYHANDLER_SIGNAL, sender=MYHANDLER_SENDER)
    #observer = Observer()
    #observer.schedule(event_handler, path=TEST_DIR, recursive=False)
    #observer.start()

    app.mainloop()
    
    observer.stop()
