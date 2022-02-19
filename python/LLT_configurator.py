from ast import Str
from email import message
import os
import sys
import threading
import time
import tkinter as tk
from pprint import pprint
from tkinter import messagebox, ttk
import tkinter
import tkinter.tix

import serial
import serial.tools.list_ports
import tktooltip

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
    """Get absolute path to resource, works for dev and for PyInstaller"""
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


class TabletArea(ttk.Labelframe):

    CANVAS_HEIGHT = 120
    CANVAS_WIDTH = 300

    def __init__(self, master, *args, **kwargs):
        ttk.Labelframe.__init__(self, master, *args, **kwargs)
        self.configure(text="Tablet Area")

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

        self.x_size_frame = ttk.Labelframe(self, text="Width")
        self.x_size_frame.grid(column=0, row=1, padx=5, pady=5)
        self.x_size_entry = ttk.Entry(
            self.x_size_frame,
            textvariable=self.x_size,
            validate="key",
            validatecommand=(validateCallback, "%P"),
            width=12,
        )
        self.x_size_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.x_size_frame, text="mm").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.y_size_frame = ttk.Labelframe(self, text="Height")
        self.y_size_frame.grid(column=1, row=1, padx=5, pady=5)
        self.y_size_entry = ttk.Entry(
            self.y_size_frame,
            textvariable=self.y_size,
            validate="key",
            validatecommand=(validateCallback, "%P"),
            width=12,
        )
        self.y_size_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.y_size_frame, text="mm").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.x_origin_frame = ttk.Labelframe(self, text="X Offset")
        self.x_origin_frame.grid(column=0, row=2, padx=5, pady=5)
        self.x_origin_entry = ttk.Entry(
            self.x_origin_frame,
            textvariable=self.x_origin,
            validate="key",
            validatecommand=(validateCallback, "%P"),
            width=12,
        )
        self.x_origin_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.x_origin_frame, text="mm").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.y_origin_frame = ttk.Labelframe(self, text="Y Offset")
        self.y_origin_frame.grid(column=1, row=2, padx=5, pady=5)
        self.y_origin_entry = ttk.Entry(
            self.y_origin_frame,
            textvariable=self.y_origin,
            validate="key",
            validatecommand=(validateCallback, "%P"),
            width=12,
        )
        self.y_origin_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.y_origin_frame, text="mm").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.lock_ratio_frame = ttk.Labelframe(self, text="lock_ratio_button")
        # self.lock_ratio_frame.grid(column=0, row=3, padx=5, pady=5)
        self.lock_ratio_var = tk.IntVar(master, 0, name="lock_ratio")
        self.lock_ratio_button = ttk.Checkbutton(
            self, text="Link Aspect Ratio", variable=self.lock_ratio_var
        )
        self.lock_ratio_button.grid(column=0, row=3, padx=0, pady=(0, 5))

        tktooltip.ToolTip(
            self.lock_ratio_button,
            msg="Link aspect ratio of tablet area to screen area",
            delay=0,
            refresh=0.1,
        )

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

    def updateScreenArea(self, a, b, c):

        if self.lock_ratio_var.get() == 1:

            self.y_size.set(self.getHeight())

        self.screen_area.delete("all")
        self.screen_area.create_rectangle(
            self.getX0(),
            self.getY0() + 2,
            self.getX1(),
            self.getY1(),
            fill=BG_COLOR,
            width=1,
            outline="black",
        )
        self.screen_area.create_rectangle(
            self.getX0_area(),
            self.getY0_area() + 2,
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

        elif input == "":
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


class ScreenMapFrame(ttk.Labelframe):

    CANVAS_HEIGHT = 120
    CANVAS_WIDTH = 300

    def __init__(self, master, x_max_size, y_max_size, *args, **kwargs):

        ttk.Labelframe.__init__(self, master, *args, **kwargs)

        self.x_size = tk.StringVar(master, x_max_size, name="x_size")
        self.y_size = tk.StringVar(master, y_max_size, name="y_size")
        self.x_origin = tk.StringVar(master, 0, name="x_origin")
        self.y_origin = tk.StringVar(master, 0, name="y_origin")
        self.x_max_size = x_max_size
        self.y_max_size = y_max_size
        self.configure(text="Screen Map")

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

        self.x_size_frame = ttk.Labelframe(self, text="Width")
        self.x_size_frame.grid(column=0, row=1, padx=5, pady=5)
        x_size_entry = ttk.Entry(
            self.x_size_frame,
            textvariable=self.x_size,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        x_size_entry.grid(column=0, row=0, padx=5, pady=5)
        self.x_size_frame.grid(column=0, row=1, padx=5, pady=5)
        ttk.Label(self.x_size_frame, text="px").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.y_size_frame = ttk.Labelframe(self, text="Height")
        self.y_size_frame.grid(column=1, row=1, padx=5, pady=5)
        y_size_entry = ttk.Entry(
            self.y_size_frame,
            textvariable=self.y_size,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        y_size_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.y_size_frame, text="px").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.x_origin_frame = ttk.Labelframe(self, text="X Offset")
        self.x_origin_frame.grid(column=0, row=2, padx=5, pady=5)
        y_origin_entry = ttk.Entry(
            self.x_origin_frame,
            textvariable=self.x_origin,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        y_origin_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.x_origin_frame, text="px").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.y_origin_frame = ttk.Labelframe(self, text="Y Offset")
        self.y_origin_frame.grid(column=1, row=2, padx=5, pady=5)
        x_origin_entry = ttk.Entry(
            self.y_origin_frame,
            textvariable=self.y_origin,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        x_origin_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.y_origin_frame, text="px").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.x_size.trace_add("write", self.updateScreenArea)
        self.y_size.trace_add("write", self.updateScreenArea)
        self.x_origin.trace_add("write", self.updateScreenArea)
        self.y_origin.trace_add("write", self.updateScreenArea)

        self.updateScreenArea(0, 0, 0)

    def updateScreenArea(self, boi, a, b):

        self.screen_area.delete("all")
        self.screen_area.create_rectangle(
            self.getX0(),
            self.getY0() + 2,
            self.getX1(),
            self.getY1(),
            fill=BG_COLOR,
            width=1,
            outline="black",
        )
        self.screen_area.create_rectangle(
            self.getX0_area(),
            self.getY0_area() + 2,
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

        elif input == "":
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


class Frame1(ttk.Frame):
    def __init__(self, root: tk.Tk, screenWidth, screenHeight, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)
        self.screen_map_frame = ScreenMapFrame(
            self,
            y_max_size=screenHeight,
            x_max_size=screenWidth,
        )
        self.screen_map_frame.grid(column=0, row=1, padx=5, pady=(5, 5), columnspan=2)

        self.tablet_area = TabletArea(self)
        self.tablet_area.grid(column=0, row=2, padx=5, pady=(0, 5), columnspan=2)


class Frame2(ttk.Frame):
    def __init__(self, root, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)
        # Self setup
        self.grid(row=0, column=0)

        # Variables
        self.exp_filter_delay = tk.DoubleVar(self, name="exp_filter_delay")
        self.exp_filter_activate = tk.IntVar(self, name="exp_filter_activate")
        self.exp_filter_activate.set(0)

        self.left_handed_var = tk.IntVar(self, name="left_handed_var")

        reg = self.register(self.validateDigit)

        self.filter_frame = ttk.Labelframe(self, text="Smoothing Filter")
        self.filter_frame.grid(row=0, column=0, padx=5, pady=5)
        self.entry_delay = ttk.Entry(
            self.filter_frame,
            width=8,
            textvariable=self.exp_filter_delay,
            validatecommand=(reg, "%P"),
        )
        self.entry_delay.grid(row=1, column=1, padx=0, pady=5)

        self.checkbox_delay = ttk.Checkbutton(
            self.filter_frame, variable=self.exp_filter_activate, text="Activate"
        )
        self.checkbox_delay.grid(row=0, column=0, padx=5, pady=(5, 0))

        ttk.Label(self.filter_frame, text="Time Constant").grid(
            row=1, column=0, padx=5, pady=5, sticky="E"
        )
        ttk.Label(self.filter_frame, text="ms").grid(
            row=1, column=2, padx=(2, 5), pady=5, sticky="E"
        )

        self.handedness_frame = ttk.Labelframe(self, text="Handedness")
        self.handedness_frame.grid(
            row=1, column=0, padx=(5, 5), pady=(0, 5), sticky="W"
        )
        self.checkbox_left_hand = ttk.Checkbutton(
            self.handedness_frame, variable=self.left_handed_var, text="Left Handed"
        )
        self.checkbox_left_hand.grid(row=0, column=0)

    def validateDigit(self, input: str):

        if input.isdigit():
            return True

        elif input == "":
            return True

        else:
            return False


class Application(ttk.Frame):

    com_port = None

    def __init__(self, root: tk.Tk, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)

        self.grid(padx=10, pady=0)

        self.grid_configure(ipadx=5, ipady=5)

        # Init widgets

        try:
            monitor_area_list = monitor_areas()
        except:
            monitor_area_list = [[0, RECT(0, 0, 1920, 1080), RECT(0, 0, 1920, 1080)]]

        screenWidth = monitor_area_list[0][1].right - monitor_area_list[0][1].left
        screenHeight = monitor_area_list[0][1].bottom - monitor_area_list[0][1].top
        print(screenHeight)

        self.tab_frame = ttk.Notebook(self)

        self.frame1 = Frame1(self, screenWidth, screenHeight)
        self.frame2 = Frame2(self)

        self.frame1.grid(row=0, column=0)
        self.frame2.grid(row=0, column=0)

        self.tab_frame.add(self.frame1, text="Area Settings")
        self.tab_frame.add(self.frame2, text="Misc. Settings")

        self.tab_frame.grid(row=0, column=0, columnspan=3, pady=(10, 0))

        self.status_indicator_var = tk.StringVar(self, name="status_indicator")

        uploadButton = ttk.Button(self, text="Upload", command=self.uploadSettings)
        uploadButton.grid(column=2, row=1, padx=0, pady=5)

        calibrateButton = ttk.Button(self, text="Calibrate", command=self.calibrate)
        calibrateButton.grid(column=1, row=1, padx=0, pady=5)

        self.statusLabelFrame = ttk.Labelframe(
            self, text="Status", height=42, width=100
        )
        self.statusLabelFrame.grid(row=1, column=0, sticky="W", pady=4)

        self.status_indicator_label = ttk.Label(
            self.statusLabelFrame, textvariable=self.status_indicator_var
        )
        self.status_indicator_label.grid(column=0, row=1, padx=3, pady=0)
        self.statusLabelFrame.grid_propagate(0)

        self.style = ttk.Style(self)
        self.style.configure("LableForeground.Red", foreground="red")

        self.startPortListener(pid=PID, vid=VID)

    def calibrate(self):
        return_message = messagebox.askokcancel(
            title="Confirm Calibration", message="Are you sure you want to calibrate?"
        )
        if return_message is False:
            return

        comPort = self.get_serial_port_with_pid_vid(PID, VID)
        writeString = "<C>"

        try:
            with serial.Serial(comPort, 19200, timeout=0.5) as ser:
                print(writeString.encode("ASCII"))
                ser.write(writeString.encode("ASCII"))
                time.sleep(0.1)

        except Exception as e:
            messagebox.showerror(title="Tablet Connection Error", message=repr(e))

        else:
            messagebox.showinfo(
                title="Calibration Complete", message="Calibration Complete"
            )

        finally:
            if ser.is_open:
                ser.close()

    def uploadSettings(self):
        comPort = self.get_serial_port_with_pid_vid(PID, VID)
        writeString = "<D"
        writeString2 = "<E"
        writeString3 = "<F"

        try:
            writeString += f"{float(self.frame1.tablet_area.x_origin.get()):.2f}" + " "
            new_y_origin = -(
                float(self.frame1.tablet_area.y_origin.get())
                + float(self.frame1.tablet_area.y_size.get())
                - self.frame1.tablet_area.y_max_size / 2.0
            )
            writeString += f"{new_y_origin:.2f}" + " "
            writeString += f"{float(self.frame1.tablet_area.x_size.get()):.3f}" + " "
            writeString += f"{float(self.frame1.tablet_area.y_size.get()):.3f}"
            writeString += ">"

            writeString2 += f"{int(self.frame1.screen_map_frame.x_max_size)}" + " "
            writeString2 += f"{int(self.frame1.screen_map_frame.y_max_size)}" + " "

            writeString2 += f"{int(self.frame1.screen_map_frame.x_origin.get())}" + " "
            writeString2 += f"{int(self.frame1.screen_map_frame.y_origin.get())}" + " "

            writeString2 += f"{int(self.frame1.screen_map_frame.x_size.get())}" + " "
            writeString2 += f"{int(self.frame1.screen_map_frame.y_size.get())}"
            writeString2 += ">"

            writeString3 += f"{int(self.frame2.exp_filter_activate.get())} "
            writeString3 += f"{float(self.frame2.exp_filter_delay.get()):.3f} "
            writeString3 += f"{int(self.frame2.left_handed_var.get())}"
            writeString3 += ">"

        except Exception as e:
            messagebox.showerror(title="Invalid settings", message=repr(e))
        try:
            with serial.Serial(comPort, 19200, timeout=0.5) as ser:
                print(writeString.encode("ASCII"))
                ser.write(writeString.encode("ASCII"))

                time.sleep(0.1)

                print(writeString2.encode("ASCII"))
                ser.write(writeString2.encode("ASCII"))

                time.sleep(0.1)

                print(writeString3.encode("ASCII"))
                ser.write(writeString3.encode("ASCII"))

                time.sleep(0.1)

        except Exception as e:
            messagebox.showerror(title="Tablet Connection Error", message=repr(e))
        else:
            messagebox.showinfo(title="Upload Complete", message="Upload Complete")
        finally:
            if ser.is_open:
                ser.close()

    def startPortListener(self, pid, vid):
        self.portListenerThread = threading.Thread(
            target=self.portListener, args=(pid, vid), daemon=True
        )
        self.portListenerThread.start()

    def portListener(self, pid, vid):
        """Sets the com port variable given the target pid and vid"""
        while True:
            self.com_port = self.get_serial_port_with_pid_vid(pid, vid)
            if self.com_port is not None:
                self.status_indicator_var.set("Connected")
                self.status_indicator_label.configure(foreground="green")
            else:
                self.status_indicator_var.set("Not Connected")
                self.status_indicator_label.configure(foreground="grey")
            time.sleep(0.2)

    def check_port_available(self, port: Str):

        try:
            serial.Serial(port=port, baudrate=115200)
        except serial.SerialException:
            return False
        return True

    def get_serial_port_with_pid_vid(self, pid, vid):
        """Return the port name of the correct PID, VID"""
        port_list = serial.tools.list_ports.comports()
        for port in port_list:
            if port.pid == pid and port.vid == vid:
                return port.name

        return None


root = tk.Tk()
root.geometry("338x675")
root.resizable(False, False)
root.title("HYKU Configurator")
root.iconbitmap(resource_path("favicon.ico"))

style = ttk.Style(root)

app = Application(root)
root.mainloop()
