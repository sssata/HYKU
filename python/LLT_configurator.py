import os
import sys
import threading
import time
import tkinter as tk
from pprint import pprint
from tkinter import messagebox, ttk

import serial
import serial.tools.list_ports

PID = 0x802F
VID = 0x2886


import ctypes

BG_COLOR = "#b3b3b3"
AREA_COLOR = "#a3ebff"
AREA_BORDER_COLOR = "#0083c9"

FRAME_BG_COLOR = "SystemButtonFace"
FRAME_BG_COLOR = "#EBEBF0"


user = ctypes.windll.user32


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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


class TabletArea(tk.LabelFrame):

    CANVAS_HEIGHT = 120
    CANVAS_WIDTH = 300

    def __init__(self, master, *args, **kwargs):
        tk.LabelFrame.__init__(self, master, *args, **kwargs)
        self.configure(text="Tablet Area", bg=master["bg"])

        self.x_size = tk.StringVar(master, 80, name="x_size_tablet")
        self.y_size = tk.StringVar(master, 60, name="y_size_tablet")
        self.x_origin = tk.StringVar(master, 40, name="x_origin_tablet")
        self.y_origin = tk.StringVar(master, 0, name="y_origin_tablet")
        self.x_max_size = 120
        self.x_max_size_offset = 0
        self.y_max_size = 90
        self.y_max_size_offset = 0

        self.screen_area = tk.Canvas(
            self,
            height=self.CANVAS_HEIGHT,
            width=self.CANVAS_WIDTH,
            bg=master["bg"],
            borderwidth=0,
            highlightthickness=1,
        )
        self.screen_area.grid(column=0, row=0, columnspan=2, padx=0, pady=5)

        validateCallback = self.register(self.validateDigit)

        self.x_size_frame = tk.LabelFrame(self, text="Width", bg=self["bg"])
        self.x_size_frame.grid(column=0, row=1, padx=5, pady=5)
        self.x_size_entry = tk.Entry(
            self.x_size_frame,
            textvariable=self.x_size,
            validate="key",
            validatecommand=(validateCallback, "%P"),
            width=12,
        )
        self.x_size_entry.grid(column=0, row=0, padx=5, pady=5)
        tk.Label(self.x_size_frame, text="mm", bg=self["bg"]).grid(column=1, row=0, padx=(0,5), pady=5)

        self.y_size_frame = tk.LabelFrame(self, text="Height", bg=self["bg"])
        self.y_size_frame.grid(column=1, row=1, padx=5, pady=5)
        self.y_size_entry = tk.Entry(
            self.y_size_frame,
            textvariable=self.y_size,
            validate="key",
            validatecommand=(validateCallback, "%P"),
            width=12,
        )
        self.y_size_entry.grid(column=0, row=0, padx=5, pady=5)
        tk.Label(self.y_size_frame, text="mm", bg=self["bg"]).grid(column=1, row=0, padx=(0,5), pady=5)

        self.x_origin_frame = tk.LabelFrame(self, text="X Offset", bg=self["bg"])
        self.x_origin_frame.grid(column=0, row=2, padx=5, pady=5)
        self.x_origin_entry = tk.Entry(
            self.x_origin_frame,
            textvariable=self.x_origin,
            validate="key",
            validatecommand=(validateCallback, "%P"),
            width=12,
        )
        self.x_origin_entry.grid(column=0, row=0, padx=5, pady=5)
        tk.Label(self.x_origin_frame, text="mm", bg=self["bg"]).grid(column=1, row=0, padx=(0,5), pady=5)

        self.y_origin_frame = tk.LabelFrame(self, text="Y Offset", bg=self["bg"])
        self.y_origin_frame.grid(column=1, row=2, padx=5, pady=5)
        self.y_origin_entry = tk.Entry(
            self.y_origin_frame,
            textvariable=self.y_origin,
            validate="key",
            validatecommand=(validateCallback, "%P"),
            width=12,
        )
        self.y_origin_entry.grid(column=0, row=0, padx=5, pady=5)
        tk.Label(self.y_origin_frame, text="mm", bg=self["bg"]).grid(column=1, row=0, padx=(0,5), pady=5)

        self.lock_ratio_frame = tk.LabelFrame(self, text="Lock Aspect Ratio", bg=self["bg"])
        self.lock_ratio_frame.grid(column=0, row=3, padx=5, pady=5)
        self.lock_ratio_var = tk.IntVar(master, 0, name="lock_ratio")
        self.lock_ratio_button = tk.Checkbutton(
            self.lock_ratio_frame, variable=self.lock_ratio_var, bg=self["bg"]
        )
        self.lock_ratio_button.grid(column=0, row=0)

        self.x_size.trace_add("write", self.updateScreenArea)
        self.y_size.trace_add("write", self.updateScreenArea)
        self.x_origin.trace_add("write", self.updateScreenArea)
        self.y_origin.trace_add("write", self.updateScreenArea)
        self.lock_ratio_var.trace_add("write", self.updateLock)

        self.updateScreenArea(0, 0, 0)

    def updateLock(self, a, b, c):
        print(self.lock_ratio_var.get())
        if self.lock_ratio_var.get() == 1:
            self.y_size_entry.configure(state=tk.DISABLED)

            self.y_size.set(self.getHeight())

        else:
            self.y_size_entry.configure(state=tk.NORMAL)

    def getHeight(self):
        return (
            float(self.master.screen_map_frame.y_size.get())
            / float(self.master.screen_map_frame.x_size.get())
            * float(self.x_size.get())
        )

    def updateScreenArea(self, boi, a, b):

        if self.lock_ratio_var.get() == 1:

            self.y_size.set(self.getHeight())

        self.screen_area.delete("all")
        self.screen_area.create_rectangle(
            self.getX0(),
            self.getY0()+2,
            self.getX1(),
            self.getY1(),
            fill=BG_COLOR,
            width=1,
            outline="black",
        )
        self.screen_area.create_rectangle(
            self.getX0_area(),
            self.getY0_area()+2,
            self.getX1_area(),
            self.getY1_area(),
            fill=AREA_COLOR,
            width=1,
            outline=AREA_BORDER_COLOR,
        )
        print(
            self.getX0_area(), self.getY0_area(), self.getX1_area(), self.getY1_area()
        )
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
        calcWidth = float(self.x_max_size) / self.y_max_size * self.CANVAS_HEIGHT
        # print("calcWidth", calcWidth)
        if calcWidth < self.CANVAS_WIDTH:
            return (self.CANVAS_WIDTH - calcWidth) / 2

        return 0

    def getX1(self):
        calcWidth = float(self.x_max_size) / self.y_max_size * self.CANVAS_HEIGHT
        if calcWidth < self.CANVAS_WIDTH:
            # print(self.CANVAS_WIDTH - calcWidth - self.getX0())
            return calcWidth + self.getX0()
        return self.CANVAS_WIDTH

    def getY0(self):
        calcHeight = float(self.y_max_size) / self.x_max_size * self.CANVAS_WIDTH
        # print("calcHeight", calcHeight)
        if calcHeight < self.CANVAS_HEIGHT:
            return (self.CANVAS_HEIGHT - calcHeight) / 2

        return 0

    def getY1(self):
        calcHeight = float(self.y_max_size) / self.x_max_size * self.CANVAS_WIDTH
        if calcHeight < self.CANVAS_HEIGHT:
            print(calcHeight + self.getY0())
            return calcHeight + self.getY0()
        return self.CANVAS_HEIGHT

    def getX0_area(self):
        calcWidth = (
            (float(self.getX1()) - self.getX0())
            / self.x_max_size
            * float(self.x_size.get())
        )
        return (float(self.getX1()) - self.getX0()) / self.x_max_size * (
            float(self.x_origin.get()) + self.x_max_size_offset
        ) + self.getX0()

    def getX1_area(self):
        calcWidth = (
            (float(self.getX1()) - self.getX0())
            / self.x_max_size
            * float(self.x_size.get())
        )
        return calcWidth + self.getX0_area()

    def getY0_area(self):
        calcHeight = (
            (float(self.getX1()) - self.getX0())
            / self.x_max_size
            * float(self.y_size.get())
        )

        return (float(self.getX1()) - self.getX0()) / self.x_max_size * (
            float(self.y_origin.get()) + self.y_max_size_offset
        ) + self.getY0()

    def getY1_area(self):
        calcHeight = (
            (float(self.getX1()) - self.getX0())
            / self.x_max_size
            * float(self.y_size.get())
        )
        return calcHeight + self.getY0_area()


class ScreenMapFrame(tk.LabelFrame):

    CANVAS_HEIGHT = 120
    CANVAS_WIDTH = 300

    def __init__(self, master, x_max_size, y_max_size, *args, **kwargs):

        tk.LabelFrame.__init__(self, master, *args, **kwargs)

        self.x_size = tk.StringVar(master, x_max_size, name="x_size")
        self.y_size = tk.StringVar(master, y_max_size, name="y_size")
        self.x_origin = tk.StringVar(master, 0, name="x_origin")
        self.y_origin = tk.StringVar(master, 0, name="y_origin")
        self.x_max_size = x_max_size
        self.y_max_size = y_max_size
        self.configure(text="Screen Map", bg=master["bg"])

        self.screen_area = tk.Canvas(
            self,
            height=self.CANVAS_HEIGHT,
            width=self.CANVAS_WIDTH,
            bg=master["bg"],
            borderwidth=0,
            highlightthickness=1,
        )
        self.screen_area.grid(column=0, row=0, columnspan=2, padx=0, pady=5)

        reg = self.register(self.validateDigit)

        self.x_size_frame = tk.LabelFrame(self, text="Width", bg=self["bg"])
        self.x_size_frame.grid(column=0, row=1, padx=5, pady=5)
        x_size_entry = tk.Entry(
            self.x_size_frame,
            textvariable=self.x_size,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
            
        )
        x_size_entry.grid(column=0, row=0, padx=5, pady=5)
        self.x_size_frame.grid(column=0, row=1, padx=5, pady=5)
        tk.Label(self.x_size_frame, text="px", bg=self["bg"]).grid(column=1, row=0, padx=(0,5), pady=5)

        self.y_size_frame = tk.LabelFrame(self, text="Height", bg=self["bg"])
        self.y_size_frame.grid(column=1, row=1, padx=5, pady=5)
        y_size_entry = tk.Entry(
            self.y_size_frame,
            textvariable=self.y_size,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        y_size_entry.grid(column=0, row=0, padx=5, pady=5)
        tk.Label(self.y_size_frame, text="px", bg=self["bg"]).grid(column=1, row=0, padx=(0,5), pady=5)

        self.x_origin_frame = tk.LabelFrame(self, text="X Offset", bg=self["bg"])
        self.x_origin_frame.grid(column=0, row=2, padx=5, pady=5)
        y_origin_entry = tk.Entry(
            self.x_origin_frame,
            textvariable=self.x_origin,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        y_origin_entry.grid(column=0, row=0, padx=5, pady=5)
        tk.Label(self.x_origin_frame, text="px", bg=self["bg"]).grid(column=1, row=0, padx=(0,5), pady=5)

        self.y_origin_frame = tk.LabelFrame(self, text="Y Offset", bg=self["bg"])
        self.y_origin_frame.grid(column=1, row=2, padx=5, pady=5)
        x_origin_entry = tk.Entry(
            self.y_origin_frame,
            textvariable=self.y_origin,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        x_origin_entry.grid(column=0, row=0, padx=5, pady=5)
        tk.Label(self.y_origin_frame, text="px", bg=self["bg"]).grid(column=1, row=0, padx=(0,5), pady=5)

        self.x_size.trace_add("write", self.updateScreenArea)
        self.y_size.trace_add("write", self.updateScreenArea)
        self.x_origin.trace_add("write", self.updateScreenArea)
        self.y_origin.trace_add("write", self.updateScreenArea)

        self.updateScreenArea(0, 0, 0)

    def updateScreenArea(self, boi, a, b):

        self.screen_area.delete("all")
        self.screen_area.create_rectangle(
            self.getX0(),
            self.getY0()+2,
            self.getX1(),
            self.getY1(),
            fill=BG_COLOR,
            width=1,
            outline="black",
        )
        self.screen_area.create_rectangle(
            self.getX0_area(),
            self.getY0_area()+2,
            self.getX1_area(),
            self.getY1_area(),
            fill=AREA_COLOR,
            width=1,
            outline=AREA_BORDER_COLOR,
        )
        try:
            self.master.tablet_area.updateScreenArea(0, 0, 0)
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
        calcWidth = float(self.x_max_size) / self.y_max_size * self.CANVAS_HEIGHT
        # print("calcWidth", calcWidth)
        if calcWidth < self.CANVAS_WIDTH:
            return (self.CANVAS_WIDTH - calcWidth) / 2

        return 0

    def getX1(self):
        calcWidth = float(self.x_max_size) / self.y_max_size * self.CANVAS_HEIGHT
        if calcWidth < self.CANVAS_WIDTH:
            # print(self.CANVAS_WIDTH - calcWidth - self.getX0())
            return calcWidth + self.getX0()
        return self.CANVAS_WIDTH

    def getY0(self):
        calcHeight = float(self.y_max_size) / self.x_max_size * self.CANVAS_WIDTH
        # print("calcHeight", calcHeight)
        if calcHeight < self.CANVAS_HEIGHT:
            return (self.CANVAS_HEIGHT - calcHeight) / 2

        return 0

    def getY1(self):
        calcHeight = float(self.y_max_size) / self.x_max_size * self.CANVAS_WIDTH
        if calcHeight < self.CANVAS_HEIGHT:
            print(calcHeight + self.getY0())
            return calcHeight + self.getY0()
        return self.CANVAS_HEIGHT

    def getX0_area(self):
        return (float(self.getX1()) - self.getX0()) / self.x_max_size * int(
            self.x_origin.get()
        ) + self.getX0()

    def getX1_area(self):
        calcWidth = (
            (float(self.getX1()) - self.getX0())
            / self.x_max_size
            * int(self.x_size.get())
        )
        return calcWidth + self.getX0_area()

    def getY0_area(self):
        calcHeight = (
            (float(self.getX1()) - self.getX0())
            / self.x_max_size
            * int(self.y_size.get())
        )
        return (float(self.getX1()) - self.getX0()) / self.x_max_size * int(
            self.y_origin.get()
        ) + self.getY0()

    def getY1_area(self):
        calcHeight = (
            (float(self.getX1()) - self.getX0())
            / self.x_max_size
            * int(self.y_size.get())
        )
        return calcHeight + self.getY0_area()


class Application(ttk.Frame):

    com_port = None

    def __init__(self, root: tk.Tk, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)

        self.grid(padx=10, pady=10)

        self.configure(bg=FRAME_BG_COLOR)

        self.grid_configure(ipadx=5, ipady=5)

        # Init widgets

        try:
            monitor_area_list = monitor_areas()
        except:
            monitor_area_list = [[0, RECT(0, 0, 1920, 1080), RECT(0, 0, 1920, 1080)]]

        screenWidth = monitor_area_list[0][1].right - monitor_area_list[0][1].left
        screenHeight = monitor_area_list[0][1].bottom - monitor_area_list[0][1].top
        print(screenHeight)

        self.screen_map_frame = ScreenMapFrame(
            self,
            y_max_size=screenHeight,
            x_max_size=screenWidth,
        )
        self.screen_map_frame.grid(column=0, row=1, padx=5, pady=5, columnspan=2)

        self.tablet_area = TabletArea(self)
        self.tablet_area.grid(column=0, row=2, padx=5, pady=5, columnspan=2)

        uploadButton = ttk.Button(self, text="Upload", command=self.uploadSettings)
        uploadButton.grid(column=1, row=3, padx=0, pady=5)

        calibrateButton = ttk.Button(self, text="Calibrate", command=self.calibrate)
        calibrateButton.grid(column=0, row=3, padx=0, pady=5)

        self.startPortListener(pid=PID, vid=VID)

    def calibrate(self):
        comPort = self.get_serial_port_with_pid_vid(PID, VID)
        writeString = "<C>"

        try:
            with serial.Serial(comPort, 19200, timeout=0.5) as ser:
                print(writeString.encode("ASCII"))
                ser.write(writeString.encode("ASCII"))

                ser.timeout = 0.5
                ser.read(10000)

        except Exception as e:
            messagebox.showerror(title="Tablet Connection Error", message=repr(e))

        finally:
            if ser.is_open:
                ser.close()



    def uploadSettings(self):
        comPort = self.get_serial_port_with_pid_vid(PID, VID)
        writeString = "<D"
        writeString2 = "<E"
        try:
            writeString += f"{float(self.tablet_area.x_origin.get()):.2f}" + " "
            new_y_origin = -(
                float(self.tablet_area.y_origin.get())
                + float(self.tablet_area.y_size.get())
                - self.tablet_area.y_max_size / 2.0
            )
            writeString += f"{new_y_origin:.2f}" + " "
            writeString += f"{float(self.tablet_area.x_size.get()):.2f}" + " "
            writeString += f"{float(self.tablet_area.y_size.get()):.2f}"
            writeString += ">"

            writeString2 += f"{int(self.screen_map_frame.x_max_size)}" + " "
            writeString2 += f"{int(self.screen_map_frame.y_max_size)}" + " "

            writeString2 += f"{int(self.screen_map_frame.x_origin.get())}" + " "
            writeString2 += f"{int(self.screen_map_frame.y_origin.get())}" + " "

            writeString2 += f"{int(self.screen_map_frame.x_size.get())}" + " "
            writeString2 += f"{int(self.screen_map_frame.y_size.get())}"
            writeString2 += ">"
        except Exception as e:
            messagebox.showerror(title="Invalid settings", message=repr(e))
        try:
            with serial.Serial(comPort, 19200, timeout=0.5) as ser:
                print(writeString.encode("ASCII"))
                ser.write(writeString.encode("ASCII"))

                ser.timeout = 0.5
                ser.read(10000)

                print(writeString2.encode("ASCII"))
                ser.write(writeString2.encode("ASCII"))

                ser.timeout = 0.5
                ser.read(10000)

        except Exception as e:
            messagebox.showerror(title="Tablet Connection Error", message=repr(e))

        finally:
            if ser.is_open:
                ser.close()

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
root.geometry("338x680")
root.resizable(False, False)
root.title("LLT Configurator")
root.iconbitmap(resource_path("favicon.ico"))
root.configure(bg=FRAME_BG_COLOR)

app = Application(root)
root.mainloop()
