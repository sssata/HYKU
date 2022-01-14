import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import time
from pprint import pprint

import threading

import serial
import serial.tools.list_ports

PID = 0x802F
VID = 0x2886


import ctypes

user = ctypes.windll.user32


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_ulong),
        ("top", ctypes.c_ulong),
        ("right", ctypes.c_ulong),
        ("bottom", ctypes.c_ulong),
    ]

    def dump(self):
        return self


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", ctypes.c_ulong),
    ]


def get_monitors():
    retval = []
    CBFUNC = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(RECT),
        ctypes.c_double,
    )

    def cb(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = lprcMonitor.contents
        # print "cb: %s %s %s %s %s %s %s %s" % (hMonitor, type(hMonitor), hdcMonitor, type(hdcMonitor), lprcMonitor, type(lprcMonitor), dwData, type(dwData))
        data = [hMonitor]
        data.append(r.dump())
        retval.append(data)
        return 1

    cbfunc = CBFUNC(cb)
    temp = user.EnumDisplayMonitors(0, 0, cbfunc, 0)
    # print temp
    return retval


def monitor_areas():
    retval = []
    monitors = get_monitors()
    for hMonitor, extents in monitors:
        data = [hMonitor]
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        mi.rcMonitor = RECT()
        mi.rcWork = RECT()
        res = user.GetMonitorInfoA(hMonitor, ctypes.byref(mi))
        data.append(mi.rcMonitor)
        data.append(mi.rcWork)
        retval.append(data)
    return retval


class TabletArea(tk.Canvas):

    CANVAS_HEIGHT = 150
    CANVAS_WIDTH = 300

    def __init__(self, master, *args, **kwargs):
        tk.Canvas.__init__(self, master, *args, **kwargs)
        self.configure(highlightthickness=0)

        self.canvas = tk.Canvas(self, bg="cyan", width=500, height=200)
        self.x_size = tk.StringVar(master, 80, name="x_size_tablet")
        self.y_size = tk.StringVar(master, 60, name="y_size_tablet")
        self.x_origin = tk.StringVar(master, 40, name="x_origin_tablet")
        self.y_origin = tk.StringVar(master, 0, name="y_origin_tablet")
        self.x_max_size = 120
        self.x_max_size_offset = 0
        self.y_max_size = 90
        self.y_max_size_offset = 0

        self.screen_area = tk.Canvas(self, height=self.CANVAS_HEIGHT, width=self.CANVAS_WIDTH, bg="SystemButtonFace", borderwidth=0)
        self.screen_area.grid(column=0, row=0, columnspan=2)

        validateCallback = self.register(self.validateDigit)

        self.x_size_frame = tk.LabelFrame(self, text="Width")
        self.x_size_frame.grid(column=0, row=1)
        self.x_size_entry = tk.Entry(self.x_size_frame, textvariable=self.x_size, validate ="key", validatecommand = (validateCallback, '%P'))
        self.x_size_entry.grid(column=0, row=0)

        self.y_size_frame = tk.LabelFrame(self, text="Height")
        self.y_size_frame.grid(column=1, row=1)
        self.y_size_entry = tk.Entry(self.y_size_frame, textvariable=self.y_size, validate ="key", validatecommand = (validateCallback, '%P'))
        self.y_size_entry.grid(column=0, row=0)

        self.x_origin_frame = tk.LabelFrame(self, text="X Offset")
        self.x_origin_frame.grid(column=0, row=2)
        self.x_origin_entry = tk.Entry(self.x_origin_frame, textvariable=self.x_origin, validate ="key", validatecommand = (validateCallback, '%P'))
        self.x_origin_entry.grid(column=0, row=0)

        self.y_origin_frame = tk.LabelFrame(self, text="Y Offset")
        self.y_origin_frame.grid(column=1, row=2)
        self.y_origin_entry = tk.Entry(self.y_origin_frame, textvariable=self.y_origin, validate ="key", validatecommand = (validateCallback, '%P'))
        self.y_origin_entry.grid(column=0, row=0)

        self.lock_ratio_frame = tk.LabelFrame(self, text= "Lock Aspect Ratio")
        self.lock_ratio_frame.grid(column=0, row=3)
        self.lock_ratio_var = tk.IntVar(master, 0, name="lock_ratio")
        self.lock_ratio_button = tk.Checkbutton(self.lock_ratio_frame, variable=self.lock_ratio_var)
        self.lock_ratio_button.grid(column=0, row=0)

        self.x_size.trace_add("write", self.updateScreenArea)
        self.y_size.trace_add("write", self.updateScreenArea)
        self.x_origin.trace_add("write", self.updateScreenArea)
        self.y_origin.trace_add("write", self.updateScreenArea)
        self.lock_ratio_var.trace_add("write", self.updateLock)

        self.updateScreenArea(0,0,0)

    def updateLock(self, a, b, c):
        print(self.lock_ratio_var.get())
        if self.lock_ratio_var.get() == 1:
            self.y_size_entry.configure(state=tk.DISABLED)
            
            self.y_size.set(self.getHeight())

        else:
            self.y_size_entry.configure(state=tk.NORMAL)
    
    def getHeight(self):
        return float(self.master.screen_map_frame.y_size.get())/float(self.master.screen_map_frame.x_size.get())*float(self.x_size.get())



    def updateScreenArea(self, boi, a, b):

        if self.lock_ratio_var.get() == 1:
            
            self.y_size.set(self.getHeight())

        self.screen_area.delete("all")
        self.screen_area.create_rectangle(self.getX0(), self.getY0(), self.getX1(), self.getY1(), fill="red", width=0, outline="green")
        self.screen_area.create_rectangle(self.getX0_area(), self.getY0_area(), self.getX1_area(), self.getY1_area(), fill="yellow", width=0, outline="green")
        print(self.getX0_area(), self.getY0_area(), self.getX1_area(), self.getY1_area())
        self.update()
        return

    def validateDigit(self, input: str):

        if input.isdigit() or input:
            return True
                            
        elif input is "":
            return True

        else:
            return False

    ## The following is an absolute fucking mess
    def getX0(self):
        calcWidth = float(self.x_max_size)/self.y_max_size*self.CANVAS_HEIGHT
        #print("calcWidth", calcWidth)
        if calcWidth < self.CANVAS_WIDTH:
            return (self.CANVAS_WIDTH - calcWidth)/2

        return 0

    def getX1(self):
        calcWidth = float(self.x_max_size)/self.y_max_size*self.CANVAS_HEIGHT
        if calcWidth < self.CANVAS_WIDTH:
            #print(self.CANVAS_WIDTH - calcWidth - self.getX0())
            return calcWidth + self.getX0()
        return self.CANVAS_WIDTH

    def getY0(self):
        calcHeight = float(self.y_max_size)/self.x_max_size*self.CANVAS_WIDTH
        #print("calcHeight", calcHeight)
        if calcHeight < self.CANVAS_HEIGHT:
            return (self.CANVAS_HEIGHT - calcHeight)/2

        return 0

    def getY1(self):
        calcHeight = float(self.y_max_size)/self.x_max_size*self.CANVAS_WIDTH
        if calcHeight < self.CANVAS_HEIGHT:
            print(calcHeight + self.getY0())
            return calcHeight + self.getY0()
        return self.CANVAS_HEIGHT


    def getX0_area(self):
        calcWidth = (float(self.getX1()) - self.getX0())/self.x_max_size * float(self.x_size.get())
        return (float(self.getX1()) - self.getX0())/self.x_max_size * (float(self.x_origin.get()) + self.x_max_size_offset) + self.getX0()


    def getX1_area(self):
        calcWidth = (float(self.getX1()) - self.getX0())/self.x_max_size * float(self.x_size.get())
        return calcWidth + self.getX0_area()

    def getY0_area(self):
        calcHeight = (float(self.getX1()) - self.getX0())/self.x_max_size * float(self.y_size.get())

        return (float(self.getX1()) - self.getX0())/self.x_max_size * (float(self.y_origin.get()) + self.y_max_size_offset) + self.getY0()


    def getY1_area(self):
        calcHeight = (float(self.getX1()) - self.getX0())/self.x_max_size * float(self.y_size.get())
        return calcHeight + self.getY0_area()


class ScreenMapFrame(tk.Frame):

    CANVAS_HEIGHT = 150
    CANVAS_WIDTH = 300

    def __init__(self, master, x_max_size, y_max_size, *args, **kwargs):

        tk.Frame.__init__(self, master, *args, **kwargs)
        

        self.x_size = tk.StringVar(master, x_max_size, name="x_size")
        self.y_size = tk.StringVar(master, y_max_size, name="y_size")
        self.x_origin = tk.StringVar(master, 0, name="x_origin")
        self.y_origin = tk.StringVar(master, 0, name="y_origin")
        self.x_max_size = x_max_size
        self.y_max_size = y_max_size

        self.screen_area = tk.Canvas(self, height=self.CANVAS_HEIGHT, width=self.CANVAS_WIDTH, bg="SystemButtonFace", borderwidth=0)
        self.screen_area.grid(column=0, row=0, columnspan=2)

        reg = self.register(self.validateDigit)

        self.x_size_frame = tk.LabelFrame(self, text="Width")
        self.x_size_frame.grid(column=0, row=1)
        x_size_entry = tk.Entry(self.x_size_frame, textvariable=self.x_size, validate ="key", validatecommand = (reg, '%P'))
        x_size_entry.grid(column=0, row=0)
        
        self.y_size_frame = tk.LabelFrame(self, text="Height")
        self.y_size_frame.grid(column=1, row=1)
        y_size_entry = tk.Entry(self.y_size_frame, textvariable=self.y_size, validate ="key", validatecommand = (reg, '%P'))
        y_size_entry.grid(column=0, row=0)

        self.x_origin_frame = tk.LabelFrame(self, text="X Offset")
        self.x_origin_frame.grid(column=0, row=2)
        y_origin_entry = tk.Entry(self.x_origin_frame, textvariable=self.x_origin, validate ="key", validatecommand = (reg, '%P'))
        y_origin_entry.grid(column=0, row=0)

        self.y_origin_frame = tk.LabelFrame(self, text="Y Offset")
        self.y_origin_frame.grid(column=1, row=2)
        x_origin_entry = tk.Entry(self.y_origin_frame, textvariable=self.y_origin, validate ="key", validatecommand = (reg, '%P'))
        x_origin_entry.grid(column=0, row=0)

        self.x_size.trace_add("write", self.updateScreenArea)
        self.y_size.trace_add("write", self.updateScreenArea)
        self.x_origin.trace_add("write", self.updateScreenArea)
        self.y_origin.trace_add("write", self.updateScreenArea)

        self.updateScreenArea(0,0,0)

    def updateScreenArea(self, boi, a, b):

        self.screen_area.delete("all")
        self.screen_area.create_rectangle(self.getX0(), self.getY0(), self.getX1(), self.getY1(), fill="red", width=0, outline="green")
        self.screen_area.create_rectangle(self.getX0_area(), self.getY0_area(), self.getX1_area(), self.getY1_area(), fill="yellow", width=0, outline="green")
        try:
            self.master.tablet_area.updateScreenArea(0,0,0)
        except AttributeError:
            pass
        self.update()
        return
    
    def validateDigit(self, input: str):

        if input.isdigit():
            return True
                            
        elif input is "":
            return True

        else:
            return False


    ## The following is an absolute fucking mess
    def getX0(self):
        calcWidth = float(self.x_max_size)/self.y_max_size*self.CANVAS_HEIGHT
        #print("calcWidth", calcWidth)
        if calcWidth < self.CANVAS_WIDTH:
            return (self.CANVAS_WIDTH - calcWidth)/2

        return 0

    def getX1(self):
        calcWidth = float(self.x_max_size)/self.y_max_size*self.CANVAS_HEIGHT
        if calcWidth < self.CANVAS_WIDTH:
            #print(self.CANVAS_WIDTH - calcWidth - self.getX0())
            return calcWidth + self.getX0()
        return self.CANVAS_WIDTH

    def getY0(self):
        calcHeight = float(self.y_max_size)/self.x_max_size*self.CANVAS_WIDTH
        #print("calcHeight", calcHeight)
        if calcHeight < self.CANVAS_HEIGHT:
            return (self.CANVAS_HEIGHT - calcHeight)/2

        return 0

    def getY1(self):
        calcHeight = float(self.y_max_size)/self.x_max_size*self.CANVAS_WIDTH
        if calcHeight < self.CANVAS_HEIGHT:
            print(calcHeight + self.getY0())
            return calcHeight + self.getY0()
        return self.CANVAS_HEIGHT


    def getX0_area(self):
        calcWidth = (float(self.getX1()) - self.getX0())/self.x_max_size * int(self.x_size.get())
        return (float(self.getX1()) - self.getX0())/self.x_max_size * int(self.x_origin.get()) + self.getX0()


    def getX1_area(self):
        calcWidth = (float(self.getX1()) - self.getX0())/self.x_max_size * int(self.x_size.get())
        return calcWidth + self.getX0_area()

    def getY0_area(self):
        calcHeight = (float(self.getX1()) - self.getX0())/self.x_max_size * int(self.y_size.get())
        return (float(self.getX1()) - self.getX0())/self.x_max_size * int(self.y_origin.get()) + self.getY0()


    def getY1_area(self):
        calcHeight = (float(self.getX1()) - self.getX0())/self.x_max_size * int(self.y_size.get())
        return calcHeight + self.getY0_area()



class Application(ttk.Frame):

    com_port = None
    SCREEN_CANVAS_HEIGHT = 150
    TABLET_CANVAS_HEIGHT = 150
    aspectRatio = None

    def __init__(self, root: tk.Tk, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)

        self.grid(padx=10, pady=10)

        self.grid_configure(ipadx=10, ipady=10)

        # Init widgets
        label = ttk.Label(self, text="Hello World!").grid(column=0, row=0)

        try:
            monitor_area_list = monitor_areas()
        except:
            monitor_area_list = [[0, RECT(0, 0, 1920, 1080), RECT(0, 0, 1920, 1080)]]

        screenWidth = monitor_area_list[0][1].right - monitor_area_list[0][1].left
        screenHeight = monitor_area_list[0][1].bottom - monitor_area_list[0][1].top
        print(screenHeight)
        print(screenWidth)

        self.screen_map_frame = ScreenMapFrame(
            self,
            y_max_size=screenHeight,
            x_max_size=screenWidth,
        )
        self.screen_map_frame.grid(column=0, row=1)

        self.tablet_area = TabletArea(self)
        self.tablet_area.grid(column=0, row=2)

        uploadButton = ttk.Button(self, text="Upload", command=self.uploadSettings).grid(
            column=1, row=3
        )

        self.startPortListener(pid=PID, vid=VID)

    def uploadSettings(self):
        comPort = self.get_serial_port_with_pid_vid(PID, VID)
        writeString = "<D"
        try:
            writeString += f'{float(self.tablet_area.x_origin.get()):.2f}'+ " "
            new_y_origin = -(float(self.tablet_area.y_origin.get()) + float(self.tablet_area.y_size.get()) - self.tablet_area.y_max_size/2.0)
            writeString += f'{new_y_origin:.2f}'+ " "
            writeString += f'{float(self.tablet_area.x_size.get()):.2f}' + " "
            writeString += f'{float(self.tablet_area.y_size.get()):.2f}'
            writeString += ">"
        except Exception as e:
            messagebox.showerror(title = "yes", message="bruh")
        try:
            with serial.Serial(comPort, 19200, timeout=0.5) as ser:
                print(writeString.encode("ASCII"))
                ser.write(writeString.encode("ASCII"))

        except Exception as e:
            messagebox.showerror(title = "yes", message=repr(e))
        


    def startPortListener(self, pid, vid):
        portListenerThread = threading.Thread(target=self.portListener, args=(pid, vid))

    def portListener(self, pid, vid):
        """Sets the com port variable given the target pid and vid"""
        while True:
            self.com_port = self.get_serial_port_with_pid_vid(pid, vid)
            time.sleep(0.5)

    def get_serial_port_with_pid_vid(self, pid, vid):
        """Return the port name of the correct PID, VID"""
        port_list = serial.tools.list_ports.comports()
        for port in port_list:
            if port.pid == pid and port.vid == vid:
                return port.name

        return None


root = tk.Tk()
root.configure()

app = Application(root)
root.mainloop()
