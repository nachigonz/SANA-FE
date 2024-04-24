#GUI
import tkinter as tk
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
import customtkinter
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog
import pickle
import matplotlib.pyplot as plt
from tensorflow.keras import layers, models, utils

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

np.set_printoptions(threshold=np.inf)
def dvs_gesture_loader(path):
    A = list()
    B = list()
    
    with open(path,'rb') as pickle_file:  
        A,B = pickle.load(pickle_file)

    return A, B

(x_train,y_train),(x_test,y_test) = dvs_gesture_loader('dvs_gesture32x32_1chNoPol100ms.pickle')
model = models.load_model('dvs_gesture.h5', compile=False)
gestures = ["clap", "rwave", "lwave", "rcw", "rccw", "lcw", "lccw", "roll", "drums", "guitar", "other"]

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

        self.output_label = tk.Label(self.home_frame, text="*OUTPUT DATA*", font=("Helvetica", 12),foreground="white",background="#2b2b2b")
        self.output_label.grid(row=1, column=0, columnspan=2, pady=20)

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
        bt_init.configure(text = "INITIALIZE SIM")
        bt_init.grid(pady = 3, row=2, column=2)

        self.canvas = ttk.Label(self.home_frame, width = 600)
        self.canvas.grid(row=1, column=2, columnspan=1, pady=20,padx=20)
        self.img = ImageTk.PhotoImage(Image.open("hm.png"))
        self.canvas.config(image=self.img)
        self.canvas.image = self.img

        ##### FILE INPUTS #####
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
            self.frame_counter = 0

            diff = cv2.absdiff(frame, self.prev_frame)
            threshold = 30
            _, thresholded = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

            self.photo2 = ImageTk.PhotoImage(image=Image.fromarray(thresholded))
            self.video2_label.config(image=self.photo2)
            self.video2_label.image = self.photo2

        self.home_button()

        architecture = "arch/loihi.yaml" #self.arch_input.get(0)
        snn = "snn/dvs_gesture_apr20.net" #self.snn_input.get(0)
        spikes = False
        voltages = False
        self.sanafe_demo = sim.run_from_gui(architecture, snn,
            spike_trace=spikes, potential_trace=voltages)
        print("initialized demo simulator")

        # for test in range(10,20):
        #     counter = 0
        #     found = False
        #     self.sanafe_demo.init()
        #     project_dir = os.path.dirname(os.path.abspath(__file__))
        #     run_dir=os.path.join(project_dir, "runs")
        #     parsed_filename = os.path.join(run_dir,
        #                            os.path.basename(architecture) + ".parsed")
        #     sim.parse_file(architecture, parsed_filename)
        #     self.sanafe_demo.set_arch(parsed_filename)
        #     self.sanafe_demo.set_net("snn/dvs_gesture_apr20.net")
        #     for y in range(32):
        #         for x in range(32):
        #             f = (32*y) + x
        #             bias = x_test[test][y][x]
        #             p = "bias=" + str(bias)
        #             self.sanafe_demo.update_neuron(0, f, ["reset_potential"], 1)
        #             self.sanafe_demo.update_neuron(0, f, [p], 1)
            
        #     for _ in range(128):
        #         outputs = []
        #         self.sanafe_demo.run_timesteps(1)
        #         res = self.sanafe_demo.get_status(5)
        #         # print(_, end=':')
        #         # print(res)
        #         for i in range(len(res)):
        #             if(res[i] == 2):
        #                 print("5.", end="")
        #                 print(i, end=", ")
        #                 print(_)
        #                 outputs.append(i)

        #                 if(i == y_test[test] and not found):
        #                     counter+=1
        #                     found = True
        #         # print(outputs)
        #         # print(self.sanafe_demo.run_summary())
        #     print(y_test[test])

        # print(counter)

        self.running = False
        self.arch_file = None
        self.snn_file = None
        self.update()

    def upload_arch(self):
        filename = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a File",
                                          filetypes = (("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
        self.arch_file = filename
        self.arch_label.configure(text="File Opened: "+filename)

    def upload_snn(self):
        filename = filedialog.askopenfilename(initialdir = "/",
                                          title = "Select a File",
                                          filetypes = (("Text files",
                                                        "*.txt*"),
                                                       ("all files",
                                                        "*.*")))
        self.snn_file = filename
        self.snn_label.configure(text="File Opened: "+filename)

    def init_button(self):
        architecture = "arch/loihi.yaml" #self.arch_file
        snn = "snn/example.net" #self.snn_file
        spikes = False
        voltages = False

        hm_plotter.reset()
        self.img = ImageTk.PhotoImage(Image.open("hm.png"))
        self.canvas.config(image=self.img)
        self.canvas.image = self.img

        if self.sanafe is None:
            self.sanafe = sim.run_from_gui(architecture, snn,
                spike_trace=spikes, potential_trace=voltages)
        else:
            self.sanafe.init()
            project_dir = os.path.dirname(os.path.abspath(__file__))
            run_dir=os.path.join(project_dir, "runs")
            parsed_filename = os.path.join(run_dir,
                                   os.path.basename(architecture) + ".parsed")
            sim.parse_file(architecture, parsed_filename)
            self.sanafe.set_arch(parsed_filename)
            self.sanafe.set_net(snn)

        print("initialized simulator")

    def run_button(self):
        # hm_plotter.reset()
        # self.img = ImageTk.PhotoImage(Image.open("hm.png"))
        # self.canvas.config(image=self.img)
        # self.canvas.image = self.img
        timesteps = int(self.timestep_entry.get())
        if self.sanafe is not None:
            self.sanafe.run_timesteps(timesteps)
            tile_spikes = self.sanafe.run_summary()
            
            state = np.array([[0]*8 for x in range(4)])
            for i in range(1, timesteps):
                for y in range(4):
                    for x in range(8):
                        state[y][x] += tile_spikes[i][(8*y) + x]

            hm_plotter.add(state)
            hm_plotter.update_img()
            self.img = ImageTk.PhotoImage(Image.open("hm.png"))
            self.canvas.config(image=self.img)
            self.canvas.image = self.img

            st = "Power: " + str(self.sanafe.get_power())
            self.output_label.config(text=st)
            print("run success")
        else:
            print("run error")
        # p = HMPlotter(8,4)

    def demo_button(self):
        if self.current is not None:
            self.running = True
            self.current.pack_forget()
            self.current = self.demo_frame
            self.current.pack(in_=self.view_panel, side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)
        else:
            self.running = True
            self.current = self.demo_frame
            self.current.pack(in_=self.view_panel, side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)

    def home_button(self):
        if self.current is not None:
            self.running = False
            self.current.pack_forget()
            self.current = self.home_frame
            self.current.pack(in_=self.view_panel, side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)
        else:
            self.running = False
            self.current = self.home_frame
            self.current.pack(in_=self.view_panel, side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)
            

    def consume_frames(self):
        for i in range(len(self.frame_list)):
            if(i!=0):
                self.frame_list[0] += self.frame_list[i]
                
        gestures = ["clap", "rwave", "lwave", "rcw", "rccw", "lcw", "lccw", "roll", "drums", "guitar", "other"]
        g_counts = [0,0,0,0,0,0,0,0,0,0,0]
        frame = self.frame_list[0]
        max = np.amax(frame)
        if(max != 0): frame = np.divide(frame, max)
        frame = np.multiply(frame, 255)
        frame = frame[np.newaxis, ..., np.newaxis]
        predict = model.predict(frame)
        print(predict)
        for i in range(len(predict[0])):
            if(predict[0][i] > .5):
                self.demo_label.config(text=("GESTURE PREDICTION: " + gestures[i]))
                print(gestures[i])
                break

        # self.sanafe_demo.init()
        # project_dir = os.path.dirname(os.path.abspath(__file__))
        # run_dir=os.path.join(project_dir, "runs")
        # parsed_filename = os.path.join(run_dir,
        #                         os.path.basename("arch/loihi.yaml") + ".parsed")
        # sim.parse_file("arch/loihi.yaml", parsed_filename)
        # self.sanafe_demo.set_arch(parsed_filename)
        # self.sanafe_demo.set_net("snn/dvs_gesture_apr20.net")

        # for y in range(32):
        #     for x in range(32):
        #         f = (32*y) + x
        #         bias = frame[y][x]
        #         p = "bias=" + str(bias)
        #         self.sanafe_demo.update_neuron(0, f, [p], 1)

        # for _ in range(128):
        #     self.sanafe_demo.run_timesteps(1)
        #     res = self.sanafe_demo.get_status(5)
        #     for i in range(len(res)):
        #         if(res[i] == 2):
        #             g_counts[i] += 1

        # print(g_counts)
        # ret = g_counts[0]
        # idx = 0
        # for i in range(len(g_counts)):
        #     if(g_counts[i] > ret):
        #         ret = g_counts[i]
        #         idx = i
        # print(gestures[idx])
        self.frame_list = []

    def update(self):
        if self.running:
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
                resized = cv2.resize(thresholded, (32, 32))
                flattened = resized.flatten()

                self.frame_list.append(resized)
                if(len(self.frame_list) >= 100): self.consume_frames()

                end = time.time()
                #print("Send to Sim Time:")
                #print(end-start)
                # print(self.sanafe_demo.get_status(5))
                # self.demo_label.configure(text = self.sanafe_demo.get_status(5))

                self.photo2 = ImageTk.PhotoImage(image=Image.fromarray(cv2.resize(resized, (640,640))))
                self.video2_label.config(image=self.photo2)
                self.video2_label.image = self.photo2

                self.prev_frame = frame.copy()
                
        self.video1_label.after(5, self.update) # 20 FPS

if __name__ == "__main__":
    app = SANAFEApp()
    app.mainloop()
