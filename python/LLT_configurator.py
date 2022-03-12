import os
import pathlib
import subprocess
import sys
import threading
import time
import tkinter as tk
import tkinter.tix
from ast import Call, Str
from pprint import pformat, pprint
from tkinter import messagebox, ttk
import requests
from typing import List, Callable, Union
import json
import logging

import serial
import serial.tools.list_ports
import tktooltip
from github import Github
import screeninfo

PID = 0x802F
VID = 0x2886


import ctypes

BG_COLOR = "#b3b3b3"
AREA_COLOR = "#a3ebff"
AREA_BORDER_COLOR = "#0083c9"

FRAME_BG_COLOR = "SystemButtonFace"
FRAME_BG_COLOR = "#EBEBF0"


user = ctypes.windll.user32


class FirmwareRelease:
    def __init__(self, release_name: str, release_download_url: str) -> None:
        self.release_name = release_name
        self.release_download_url = release_download_url


def resolve_resource_path(relative_path: str):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        base_path = pathlib.Path(".").resolve()

    return pathlib.Path(base_path) / relative_path
    # return os.path.join(base_path, relative_path)


def get_serial_port_with_pid_vid(pid, vid):
    """Return the port name of the correct PID, VID"""
    port_list = serial.tools.list_ports.comports()
    for port in port_list:
        if port.pid == pid and port.vid == vid:
            return port.name

    return None


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


monitor_list = screeninfo.get_monitors()
monitor_primary = [x.name for x in monitor_list if x.is_primary][0]
monitor_object_primary = [x for x in monitor_list if x.is_primary][0]
monitor_list_names = [x.name for x in monitor_list]

is_calibration_canceled = None

for monitor in monitor_list:
    print(str(monitor))


class MonitorTabletRectangle:
    """Holds info on monitor or tablet coords"""

    def __init__(self, x0, y0, x1, y1) -> None:
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def __eq__(self, other):
        if not isinstance(other, MonitorTabletRectangle):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return (
            self.x0 == other.x0
            and self.y0 == other.y0
            and self.x1 == other.x1
            and self.y1 == other.y1
        )

    def __str__(self):
        return pformat(self.__dict__)


class MonitorBoundingBox:
    def __init__(self, min_x, min_y, max_x, max_y) -> None:
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y


def get_scaling_factor(canvas_width, canvas_height, bounding_box: MonitorBoundingBox):
    """Returns the scaling factor to draw a rectangle on a canvas
    given the canvas dimensions and bounding box"""

    scale_factor_x = (canvas_width * 1.0) / (bounding_box.max_x - bounding_box.min_x)
    scale_factor_y = (canvas_height * 1.0) / (bounding_box.max_y - bounding_box.min_y)
    return min(scale_factor_x, scale_factor_y)


def shift_origin(
    monitor_rect: MonitorTabletRectangle, bounding_box: MonitorBoundingBox
):
    """Shift origin of the given screen areas"""
    monitor_rect.x0 -= bounding_box.min_x
    monitor_rect.y0 -= bounding_box.min_y
    monitor_rect.x1 -= bounding_box.min_x
    monitor_rect.y1 -= bounding_box.min_y


def center_in_canvas_x_gap(
    canvas_width,
    canvas_height,
    scaling_factor,
    bounding_box: MonitorBoundingBox,
):
    """Returns the x dimension gap required to center a rectangle a canvas given args.
    Minimum of 0.
    Args:   canvas_with
            canvas_height
            scaling_factor
            bounding_box"""
    gap_x = (bounding_box.max_x - bounding_box.min_x) * scaling_factor - canvas_width
    return max(0, gap_x)


def center_in_canvas_y_gap(
    self,
    canvas_width,
    canvas_height,
    scaling_factor,
    bounding_box: MonitorBoundingBox,
):
    """Returns the x dimension gap required to center a rectangle a canvas given args.
    Minimum of 0.
    Args:   canvas_with
            canvas_height
            scaling_factor
            bounding_box"""
    gap_y = (bounding_box.max_y - bounding_box.min_y) * scaling_factor - canvas_height
    return max(0, gap_y)


class TabletArea(ttk.Labelframe):

    CANVAS_HEIGHT = 100
    CANVAS_WIDTH = 300

    def __init__(
        self,
        master,
        get_screen_area_callback: Callable[[], MonitorTabletRectangle],
        *args,
        **kwargs,
    ):
        ttk.Labelframe.__init__(self, master, *args, **kwargs)
        self.configure(text="Tablet Area")

        self.x_size = tk.DoubleVar(master, 80, name="x_size_tablet")
        self.y_size = tk.DoubleVar(master, 60, name="y_size_tablet")
        self.x_origin = tk.DoubleVar(master, 40, name="x_origin_tablet")
        self.y_origin = tk.DoubleVar(master, 0, name="y_origin_tablet")
        self.x_max_size = 120
        self.x_max_size_offset = 0
        self.y_max_size = 90
        self.y_max_size_offset = 0
        self.get_screen_area_callback = get_screen_area_callback

        self.screen_area = tk.Canvas(
            self,
            height=self.CANVAS_HEIGHT + 1,
            width=self.CANVAS_WIDTH + 1,
            bg=master["bg"],
            borderwidth=0,
            highlightthickness=0,
            bd=0,
        )
        self.screen_area.grid(column=0, row=0, columnspan=2, padx=0, pady=5)

        validateCallback = self.register(self.validateFloat)

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
        self.updateScreenArea(0, 0, 0)
        if self.lock_ratio_var.get() == 1:
            self.y_size_entry.configure(state=tk.DISABLED)

            # self.y_size.set(self.get_height_with_aspect_ratio_lock())
        else:
            self.y_size_entry.configure(state=tk.NORMAL)

    def get_height_with_aspect_ratio_lock(self):
        """Calculate the height of tablet area to match screen area aspect ratio"""
        print("get_height_with_aspect_ratio_lock")
        screen_area_rectangle = self.get_screen_area_callback()
        aspect_ratio_x_y = float(
            screen_area_rectangle.y1 - screen_area_rectangle.y0
        ) / float(screen_area_rectangle.x1 - screen_area_rectangle.x0)

        return aspect_ratio_x_y * float(self.x_size.get())

    def get_bounding_box(
        self, monitor_list: List[Union[screeninfo.Monitor, MonitorTabletRectangle]]
    ):

        bounding_box = MonitorBoundingBox(0, 0, 0, 0)
        for monitor in monitor_list:
            if isinstance(monitor, MonitorTabletRectangle):
                bounding_box.min_x = min(monitor.x0, bounding_box.min_x)
                bounding_box.min_y = min(monitor.y0, bounding_box.min_y)
                bounding_box.max_x = max(monitor.x1, bounding_box.max_x)
                bounding_box.max_y = max(monitor.y1, bounding_box.max_y)
                ...
            elif isinstance(monitor, screeninfo.Monitor):
                bounding_box.min_x = min(monitor.x, bounding_box.min_x)
                bounding_box.min_y = min(monitor.y, bounding_box.min_y)
                bounding_box.max_x = max(monitor.x + monitor.width, bounding_box.max_x)
                bounding_box.max_y = max(monitor.y + monitor.height, bounding_box.max_y)

        return bounding_box

    def get_scaling_factor(
        self, canvas_width, canvas_height, bounding_box: MonitorBoundingBox
    ):
        """Returns the scaling factor to draw a rectangle on a canvas
        given the canvas dimensions and bounding box"""

        scale_factor_x = (canvas_width * 1.0) / (
            bounding_box.max_x - bounding_box.min_x
        )
        scale_factor_y = (canvas_height * 1.0) / (
            bounding_box.max_y - bounding_box.min_y
        )
        return min(scale_factor_x, scale_factor_y)

    def shift_origin(
        self, monitor_rect: MonitorTabletRectangle, bounding_box: MonitorBoundingBox
    ):
        """Shift origin of the given screen areas"""
        monitor_rect.x0 -= bounding_box.min_x
        monitor_rect.y0 -= bounding_box.min_y
        monitor_rect.x1 -= bounding_box.min_x
        monitor_rect.y1 -= bounding_box.min_y

    def center_in_canvas_x_gap(
        self,
        canvas_width,
        canvas_height,
        scaling_factor,
        bounding_box: MonitorBoundingBox,
    ):
        """Returns the x dimension gap required to center a rectangle a canvas given args.
        Minimum of 0.
        Args:   canvas_with
                canvas_height
                scaling_factor
                bounding_box"""

        gap_x = (
            canvas_width - (bounding_box.max_x - bounding_box.min_x) * scaling_factor
        )
        return max(0, gap_x / 2)

    def center_in_canvas_y_gap(
        self,
        canvas_width,
        canvas_height,
        scaling_factor,
        bounding_box: MonitorBoundingBox,
    ):
        """Returns the x dimension gap required to center a rectangle a canvas given args.
        Minimum of 0.
        Args:   canvas_with
                canvas_height
                scaling_factor
                bounding_box"""
        gap_y = (
            canvas_height - (bounding_box.max_y - bounding_box.min_y) * scaling_factor
        )
        return max(0, gap_y / 2)

    def updateScreenArea(self, a, b, c):

        if self.lock_ratio_var.get() == 1:

            self.y_size.set(self.get_height_with_aspect_ratio_lock())

        self.screen_area.delete("all")

        tablet_area_rectangle = MonitorTabletRectangle(
            self.x_origin.get(),
            self.y_origin.get(),
            self.x_origin.get() + self.x_size.get(),
            self.y_origin.get() + self.y_size.get(),
        )

        tablet_size_rectangle = MonitorTabletRectangle(
            self.x_max_size_offset,
            self.y_max_size_offset,
            self.x_max_size,
            self.y_max_size,
        )
        rectangle_list = [tablet_area_rectangle, tablet_size_rectangle]

        bounding_box = self.get_bounding_box(rectangle_list)

        scaling_factor = self.get_scaling_factor(
            self.CANVAS_WIDTH, self.CANVAS_HEIGHT, bounding_box
        )

        self.shift_origin(tablet_area_rectangle, bounding_box)
        self.shift_origin(tablet_size_rectangle, bounding_box)

        gap_x = self.center_in_canvas_x_gap(
            self.CANVAS_WIDTH, self.CANVAS_HEIGHT, scaling_factor, bounding_box
        )
        gap_y = self.center_in_canvas_y_gap(
            self.CANVAS_WIDTH, self.CANVAS_HEIGHT, scaling_factor, bounding_box
        )

        # Draw Tablet surface
        self.screen_area.create_rectangle(
            tablet_size_rectangle.x0 * scaling_factor + gap_x,
            tablet_size_rectangle.y0 * scaling_factor + gap_y,
            tablet_size_rectangle.x1 * scaling_factor + gap_x,
            tablet_size_rectangle.y1 * scaling_factor + gap_y,
            fill=BG_COLOR,
            width=1,
            outline="black",
        )

        # Draw Tablet surface
        """self.screen_area.create_rectangle(
            self.getX0(),
            self.getY0() + 2,
            self.getX1(),
            self.getY1(),
            fill=BG_COLOR,
            width=1,
            outline="black",
        )"""

        self.screen_area.create_rectangle(
            tablet_area_rectangle.x0 * scaling_factor + gap_x,
            tablet_area_rectangle.y0 * scaling_factor + gap_y,
            tablet_area_rectangle.x1 * scaling_factor + gap_x,
            tablet_area_rectangle.y1 * scaling_factor + gap_y,
            fill=AREA_COLOR,
            width=1,
            outline=AREA_BORDER_COLOR,
        )

        """# Draw selected tablet area
        self.screen_area.create_rectangle(
            self.getX0_area(),
            self.getY0_area() + 2,
            self.getX1_area(),
            self.getY1_area(),
            fill=AREA_COLOR,
            width=1,
            outline=AREA_BORDER_COLOR,
        )"""
        self.update()
        return

    def validateFloat(self, input: str):

        # try to parse int
        if input == "" or input == "-":
            return True
        try:
            float(input)
        except Exception as e:
            print(repr(e))
            return False
        else:
            return True


class ScreenMapFrame(ttk.Labelframe):

    CANVAS_HEIGHT = 120
    CANVAS_WIDTH = 300

    def __init__(
        self,
        master,
        update_tablet_area_callback: Callable,
        *args,
        **kwargs,
    ):

        ttk.Labelframe.__init__(self, master, *args, **kwargs)
        self.update_tablet_area_callback = update_tablet_area_callback

        self.x_size = tk.StringVar(master, 0, name="x_size")
        self.y_size = tk.StringVar(master, 0, name="y_size")
        self.x_origin = tk.StringVar(master, 0, name="x_origin")
        self.y_origin = tk.StringVar(master, 0, name="y_origin")
        self.selected_monitor_preset = tk.StringVar(master, monitor_primary)
        self.selected_mode = tk.BooleanVar(master, 0, "selected_mode")

        self.configure(text="Screen Map")

        self.screen_area = tk.Canvas(
            self,
            height=self.CANVAS_HEIGHT + 1,
            width=self.CANVAS_WIDTH + 1,
            bg=master["bg"],
            borderwidth=0,
            highlightthickness=0,
            bd=0,
        )
        self.screen_area.grid(column=0, row=0, columnspan=2, padx=0, pady=5)

        reg = self.register(self.validateDigit)

        self.x_size_frame = ttk.Labelframe(self, text="Width")
        self.x_size_frame.grid(column=0, row=2, padx=5, pady=5)
        x_size_entry = ttk.Entry(
            self.x_size_frame,
            textvariable=self.x_size,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        x_size_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.x_size_frame, text="px").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.y_size_frame = ttk.Labelframe(self, text="Height")
        self.y_size_frame.grid(column=1, row=2, padx=5, pady=5)
        self.y_size_entry = ttk.Entry(
            self.y_size_frame,
            textvariable=self.y_size,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        self.y_size_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.y_size_frame, text="px").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.x_origin_frame = ttk.Labelframe(self, text="X Offset")
        self.x_origin_frame.grid(column=0, row=3, padx=5, pady=5)
        self.y_origin_entry = ttk.Entry(
            self.x_origin_frame,
            textvariable=self.x_origin,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        self.y_origin_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.x_origin_frame, text="px").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.y_origin_frame = ttk.Labelframe(self, text="Y Offset")
        self.y_origin_frame.grid(column=1, row=3, padx=5, pady=5)
        self.x_origin_entry = ttk.Entry(
            self.y_origin_frame,
            textvariable=self.y_origin,
            validate="key",
            validatecommand=(reg, "%P"),
            width=12,
        )
        self.x_origin_entry.grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(self.y_origin_frame, text="px").grid(
            column=1, row=0, padx=(0, 5), pady=5
        )

        self.monitor_select_frame = ttk.Labelframe(self, text="Monitor Presets")
        self.monitor_select_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        self.monitor_select_dropdown = ttk.Combobox(
            self.monitor_select_frame,
            textvariable=self.selected_monitor_preset,
            width=18,
        )
        self.monitor_select_dropdown.grid(row=1, column=0, padx=5, pady=5)
        self.monitor_select_dropdown["values"] = monitor_list_names + ["Custom"]
        ttk.Label(self.monitor_select_frame, text="Preset ").grid(
            column=0, row=0, padx=(0, 5), pady=5
        )
        self.mode_selector_checkbox = ttk.Checkbutton(
            self.monitor_select_frame,
            text="osu! Absolute Map Mode",
            variable=self.selected_mode,
        )
        self.mode_selector_checkbox.grid(row=0, column=0, padx=5, pady=5)

        self.x_size.trace_add("write", self.update_screen_area)
        self.y_size.trace_add("write", self.update_screen_area)
        self.x_origin.trace_add("write", self.update_screen_area)
        self.y_origin.trace_add("write", self.update_screen_area)
        self.selected_mode.trace_add("write", self.switch_mode_callback)
        self.selected_monitor_preset.trace_add("write", self.monitor_select_callback)

        self.monitor_select_callback(0, 0, 0)
        self.update_screen_area(0, 0, 0)

    def get_bounding_box(
        self, monitor_list: List[Union[screeninfo.Monitor, MonitorTabletRectangle]]
    ):

        bounding_box = MonitorBoundingBox(10000, 10000, -10000, -10000)
        for monitor in monitor_list:
            if isinstance(monitor, MonitorTabletRectangle):
                bounding_box.min_x = min(monitor.x0, bounding_box.min_x)
                bounding_box.min_y = min(monitor.y0, bounding_box.min_y)
                bounding_box.max_x = max(monitor.x1, bounding_box.max_x)
                bounding_box.max_y = max(monitor.y1, bounding_box.max_y)
                ...
            elif isinstance(monitor, screeninfo.Monitor):
                bounding_box.min_x = min(monitor.x, bounding_box.min_x)
                bounding_box.min_y = min(monitor.y, bounding_box.min_y)
                bounding_box.max_x = max(monitor.x + monitor.width, bounding_box.max_x)
                bounding_box.max_y = max(monitor.y + monitor.height, bounding_box.max_y)

        return bounding_box

    def get_scaling_factor(
        self, canvas_width, canvas_height, bounding_box: MonitorBoundingBox
    ):

        scale_factor_x = (canvas_width * 1.0) / (
            bounding_box.max_x - bounding_box.min_x
        )
        scale_factor_y = (canvas_height * 1.0) / (
            bounding_box.max_y - bounding_box.min_y
        )
        return min(scale_factor_x, scale_factor_y)

    def shift_origin(
        self, monitor_rect: MonitorTabletRectangle, bounding_box: MonitorBoundingBox
    ):
        monitor_rect.x0 -= bounding_box.min_x
        monitor_rect.y0 -= bounding_box.min_y
        monitor_rect.x1 -= bounding_box.min_x
        monitor_rect.y1 -= bounding_box.min_y

    def center_in_canvas_x_gap(
        self,
        canvas_width,
        canvas_height,
        scaling_factor,
        bounding_box: MonitorBoundingBox,
    ):
        gap_x = (
            canvas_width - (bounding_box.max_x - bounding_box.min_x) * scaling_factor
        )
        return max(0, gap_x / 2)

    def center_in_canvas_y_gap(
        self,
        canvas_width,
        canvas_height,
        scaling_factor,
        bounding_box: MonitorBoundingBox,
    ):
        gap_y = (
            canvas_height - (bounding_box.max_y - bounding_box.min_y) * scaling_factor
        )
        return max(0, gap_y / 2)

    def get_selected_screen_area(self):
        """Returns the current selected screen area as a MonitorRectangle object"""
        return MonitorTabletRectangle(
            int(self.x_origin.get()),
            int(self.y_origin.get()),
            int(self.x_size.get()) + int(self.x_origin.get()),
            int(self.y_origin.get()) + int(self.y_size.get()),
        )

    def monitor_select_callback(self, var_name, var_index, event_type):
        """Called when monitor preset is selected"""
        for monitor in monitor_list:
            if self.selected_monitor_preset.get() == monitor.name:
                self.x_size.set(monitor.width)
                self.y_size.set(monitor.height)
                self.x_origin.set(monitor.x)
                self.y_origin.set(monitor.y)

    def switch_mode_callback(self, var_name, var_index, event_type):
        if self.selected_mode.get():
            self.x_origin_entry["state"] = "disabled"
            self.y_origin_entry["state"] = "disabled"

        # Draw all monitors
        else:
            self.x_origin_entry["state"] = "normal"
            self.y_origin_entry["state"] = "normal"

        self.update_screen_area(0,0,0)

    def update_screen_area(self, var_name, var_index, event_type):
        """Redraws the screen area map"""

        bounding_box_list = [self.get_selected_screen_area()]

        if not self.selected_mode.get():
            bounding_box_list += monitor_list

        print(bounding_box_list)

        bounding_box = self.get_bounding_box(bounding_box_list)
        print(bounding_box.min_x, bounding_box.max_x, bounding_box.min_y, bounding_box.max_y)
        scaling_factor = self.get_scaling_factor(
            self.CANVAS_WIDTH, self.CANVAS_HEIGHT, bounding_box
        )
        self.screen_area.delete("all")
        gap_x = self.center_in_canvas_x_gap(
            self.CANVAS_WIDTH, self.CANVAS_HEIGHT, scaling_factor, bounding_box
        )
        gap_y = self.center_in_canvas_y_gap(
            self.CANVAS_WIDTH, self.CANVAS_HEIGHT, scaling_factor, bounding_box
        )

        screen_area_rectangle = MonitorTabletRectangle(
            int(self.x_origin.get()),
            int(self.y_origin.get()),
            int(self.x_origin.get()) + int(self.x_size.get()),
            int(self.y_origin.get()) + int(self.y_size.get()),
        )
        self.shift_origin(screen_area_rectangle, bounding_box)

        is_matching_monitor = False

        # Draw all monitors
        if not self.selected_mode.get():

            for monitor in monitor_list:
                monitor_rectangle = MonitorTabletRectangle(
                    monitor.x,
                    monitor.y,
                    monitor.x + monitor.width,
                    monitor.y + monitor.height,
                )
                self.shift_origin(monitor_rectangle, bounding_box)

                self.screen_area.create_rectangle(
                    (monitor_rectangle.x0) * scaling_factor + gap_x,
                    (monitor_rectangle.y0) * scaling_factor + gap_y,
                    (monitor_rectangle.x1) * scaling_factor + gap_x,
                    (monitor_rectangle.y1) * scaling_factor + gap_y,
                    fill=BG_COLOR,
                    width=1,
                    outline="black",
                )

                # Match current screen settings with preset
                if monitor_rectangle == screen_area_rectangle:
                    self.selected_monitor_preset.set(monitor.name)
                    is_matching_monitor = True

        # Check abs mode

        # If no match, set to Custom
        if not is_matching_monitor:
            self.selected_monitor_preset.set("Custom")

        # Draw current area
        self.screen_area.create_rectangle(
            (screen_area_rectangle.x0) * scaling_factor + gap_x,
            (screen_area_rectangle.y0) * scaling_factor + gap_y,
            (screen_area_rectangle.x1) * scaling_factor + gap_x,
            (screen_area_rectangle.y1) * scaling_factor + gap_y,
            fill=AREA_COLOR,
            width=1,
            outline=AREA_BORDER_COLOR,
        )

        try:
            # self.master.tablet_area.updateScreenArea(0, 0, 0)
            self.update_tablet_area_callback()
        except AttributeError:
            pass
        self.update()
        return

    def validateDigit(self, input: str):

        if input == "" or input == "-":
            return True

        try:
            int(input)
        except Exception as e:
            return False

        else:
            return True


class Frame1(ttk.Frame):
    def __init__(self, root: tk.Tk, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)
        self.screen_map_frame = ScreenMapFrame(
            self,
            update_tablet_area_callback=self.update_tablet_area_callback,
        )
        self.screen_map_frame.grid(column=0, row=1, padx=5, pady=(5, 5), columnspan=2)

        self.tablet_area = TabletArea(
            self, self.screen_map_frame.get_selected_screen_area
        )
        self.tablet_area.grid(column=0, row=2, padx=5, pady=(0, 5), columnspan=2)

    def update_tablet_area_callback(self):
        self.tablet_area.updateScreenArea(0, 0, 0)


class Frame2(ttk.Frame):
    def __init__(self, root, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)

        # Self setup
        self.grid(row=0, column=0)

        # GUI Variables
        self.exp_filter_delay = tk.DoubleVar(self, name="exp_filter_delay")
        self.exp_filter_activate = tk.IntVar(self, name="exp_filter_activate")
        self.exp_filter_activate.set(0)

        self.left_handed_var = tk.IntVar(self, name="left_handed_var")

        reg = self.register(self.validateDigit)

        # Smoothing Filter GUI widgets

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

        # Handedness GUI widgets

        self.handedness_frame = ttk.Labelframe(self, text="Handedness")
        self.handedness_frame.grid(
            row=1, column=0, padx=(5, 5), pady=(0, 5), sticky="W"
        )
        self.checkbox_left_hand = ttk.Checkbutton(
            self.handedness_frame, variable=self.left_handed_var, text="Left Handed"
        )
        self.checkbox_left_hand.grid(row=0, column=0)

        # H

    def validateDigit(self, input: str):

        if input.isdigit():
            return True

        elif input == "":
            return True

        else:
            return False


class Frame3(ttk.Frame):
    def __init__(self, root, calibrate_command, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)

        # Self configs
        self.grid(row=0, column=0)

        # Variables
        self.selected_firmware_release = tk.StringVar(
            self, name="selected_firmware_release"
        )
        self.firmware_release_dict: dict[str, str] = dict()

        # Calibrate GUI elements
        self.calibrate_frame = ttk.Labelframe(self, text="Calibrate")
        self.calibrate_frame.grid(row=0, column=0, padx=5, pady=5, sticky="W")
        self.calibrate_button = ttk.Button(
            self.calibrate_frame, text="Calibrate", command=calibrate_command
        )
        self.calibrate_button.grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
        )

        # Firmware Update elements
        self.update_frame = ttk.Labelframe(self, text="Firmware Update")
        self.update_frame.grid(row=1, column=0, padx=5, pady=5, sticky="W")
        self.update_button = ttk.Button(
            self.update_frame, text="Update", command=self.upload_firmware_callback
        )
        self.update_button["state"] = "disabled"
        self.update_button.grid(row=1, column=0, padx=5, pady=5, sticky="W")
        self.fetch_releases_button = ttk.Button(
            self.update_frame,
            text="Fetch Releases",
            command=self.fetch_firmware_callback,
        )
        self.fetch_releases_button.grid(row=0, column=1)
        self.firmware_combobox = ttk.Combobox(
            self.update_frame, textvariable=self.selected_firmware_release, width=10
        )
        self.firmware_combobox.grid(row=0, column=0)

    def reset_port(self, port: serial.Serial):
        """Resets given port by opening and closing port twice within 500ms at 1200 baud"""
        assert not port.is_open
        port.baudrate = 1200
        port.open()
        time.sleep(0.05)
        port.close()
        time.sleep(0.05)
        port.open()
        time.sleep(0.05)
        port.close()
        # Wait for reset and enumeration
        time.sleep(1)

    def bossac_upload(self, bossac_path: str, bin_path: str):
        """Run Bossac to upload given bin file"""

        args = (
            f"{bossac_path}",
            f"--info",
            "-i",  # INFO
            "-e",  # Erase
            "-w",  # Write
            "-v",  # Verify
            f"{bin_path}",
            "-R",
        )

        popen = subprocess.run(
            args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = popen.stdout.decode("ASCII")
        err = popen.stderr.decode("ASCII")
        print(output)
        print(err)

    def download_firmware(self, file_path: str, url: str):
        """Download file from given url to given filename"""

        r = requests.get(url, allow_redirects=True)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        open(file_path, "wb").write(r.content)

    def upload_firmware_callback(self):
        """Callback for firmware upload button"""
        ok_cancel_response = messagebox.askokcancel(
            title="Confirm Firmware Update",
            message="Continue with Firmware Update? Tablet will need to be recalibrated and settings will need to be reuploaded.",
        )

        if not ok_cancel_response:
            return

        comPort = get_serial_port_with_pid_vid(PID, VID)
        port = serial.Serial()
        port.port = comPort

        release_name = self.selected_firmware_release.get()
        url = self.firmware_release_dict[release_name]
        bin_path = resolve_resource_path(f"binaries2/{release_name}")

        try:
            self.download_firmware(bin_path, url)
        except Exception as e:
            messagebox.showerror(
                title="Error Downloading Firmware", message=f"Error: {repr(e)}"
            )

        try:
            self.reset_port(port)
        except Exception as e:
            messagebox.showerror(
                title="Error Reseting Port", message=f"Error: {repr(e)}"
            )

        try:
            self.bossac_upload(
                resolve_resource_path("tools/bossac.exe"),
                resolve_resource_path(bin_path),
            )
        except Exception as e:
            messagebox.showerror(
                title="Error Uploading Firmware", message=f"Error: {repr(e)}"
            )

        return

    def get_firmware_release_list(self, firmware_release_dict: dict[str, str] = dict()):
        print(os.environ.get("GITHUB_TOKEN"))
        g = Github(os.environ.get("GITHUB_TOKEN"))
        rate_limit = g.get_rate_limit()
        print(rate_limit)

        firmware_release_list: list[FirmwareRelease] = list()

        repo = g.get_repo("sssata/HYKU_Firmware")
        release_list = repo.get_releases()

        for release in release_list:
            asset_list = release.get_assets()
            for asset in asset_list:
                print(asset.name)
                if asset.name.endswith(".bin"):
                    print(asset.browser_download_url)
                    firmware_release_list.append(
                        FirmwareRelease(release.title, asset.browser_download_url)
                    )
                    firmware_release_dict[release.title] = asset.browser_download_url

        return firmware_release_dict

    def fetch_firmware_callback(self):
        """callback function for fetch firmware releases button
        Gets firmware list and download urls from github
        Sets the self.firmware_release_dict as well"""

        try:
            self.get_firmware_release_list(self.firmware_release_dict)
        except Exception as e:
            messagebox.showerror(
                title="Error while getting firmware releases",
                message=f"Error: {repr(e)}",
            )
        self.firmware_combobox["values"] = list(self.firmware_release_dict.keys())

        if self.firmware_release_dict:
            self.update_button["state"] = "normal"
            self.selected_firmware_release.set(
                list(self.firmware_release_dict.keys())[0]
            )


class CalibrateInfoFrame(tk.Toplevel):
    """Popup window containing info about calibration"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("600x440")
        self.protocol("WM_DELETE_WINDOW", self.set_cancel)
        self.resizable(False, False)
        self.calibrate_instructions_image = tk.PhotoImage(
            file=resolve_resource_path("calibrate_image_annotated.png")
        )

        self.image_canvas = tk.Canvas(self, width=600, height=400)
        self.image_canvas.grid(row=0, column=0, columnspan=2, sticky="NSEW")
        self.image_canvas.create_image(
            0, 0, image=self.calibrate_instructions_image, anchor=tk.NW
        )

        self.calibrate_button = ttk.Button(
            self, text="Calibrate", command=self.set_calibrate
        )
        self.calibrate_button.grid(row=1, column=1, pady=5)

        self.cancel_button = ttk.Button(self, text="Cancel", command=self.set_cancel)
        self.cancel_button.grid(row=1, column=0, pady=5)

    def set_cancel(self):
        global is_calibration_canceled
        is_calibration_canceled = True
        self.destroy()

    def set_calibrate(self):
        global is_calibration_canceled
        is_calibration_canceled = False
        self.destroy()


class Application(ttk.Frame):

    com_port = None

    def __init__(self, root: tk.Tk, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)

        self.grid(padx=10, pady=0)

        self.grid_configure(ipadx=5, ipady=5)

        # Init widgets

        self.tab_frame = ttk.Notebook(self)

        self.frame1 = Frame1(self)
        self.frame2 = Frame2(self)
        self.frame3 = Frame3(self, calibrate_command=self.calibrate)

        self.frame1.grid(row=0, column=0)
        self.frame2.grid(row=0, column=0)

        self.tab_frame.add(self.frame1, text="Area Settings")
        self.tab_frame.add(self.frame2, text="Misc. Settings")
        self.tab_frame.add(self.frame3, text="Tools")

        self.tab_frame.grid(row=0, column=0, columnspan=3, pady=(10, 0))

        self.status_indicator_var = tk.StringVar(self, name="status_indicator")

        uploadButton = ttk.Button(self, text="Upload", command=self.uploadSettings)
        uploadButton.grid(column=2, row=1, padx=0, pady=5)

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
        # self.style.configure("LablelForeground.Red", foreground="red")

        self.startPortListener(pid=PID, vid=VID)

    def calibrate(self):

        nice = CalibrateInfoFrame()
        nice.wait_window()
        if is_calibration_canceled:
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

    def get_fw_version(self, port: serial.Serial):
        assert port.is_open
        port.reset_input_buffer()
        port.reset_output_buffer()
        port.write(b"<V>")
        read_1 = port.readline()
        read_1_string = read_1.decode("ASCII").rstrip("\r\n")
        assert (
            read_1.decode("ASCII").rstrip("\r\n") == "V"
        ), f"Failed to read firmware version, response line 1: {read_1_string}"
        read_2 = port.readline()
        return read_2.decode(encoding="ASCII").rstrip("\r\n")

    def write_settings(self, port: serial.Serial, dict_to_write: dict):

        # set write command
        dict_to_write["cmd"] = "W"

        # Write dict as json
        assert port.is_open
        port.reset_input_buffer()
        port.reset_output_buffer()
        out_json_string = json.dumps(
            dict_to_write,
            ensure_ascii=True,
            check_circular=True,
            separators=(",", ":"),
            sort_keys=False,
        )
        port.write(out_json_string.encode("ASCII"))

        # Read response
        port.read_until(b"{")
        in_bytes = bytes(b"{") + port.read_until(b"}")
        print(in_bytes.decode("ASCII"))
        dict_read: dict = json.loads(in_bytes)
        assert dict_read.get("cmd") == "W"

    def write_settings_test(self, port: serial.Serial, dict_to_write: dict):
        dict_to_write["cmd"] = "W"
        pprint(print(dict_to_write))
        json_string = json.dumps(
            dict_to_write,
            ensure_ascii=True,
            check_circular=True,
            separators=(",", ":"),
            sort_keys=False,
        )
        print("minified length: ", len(json_string))
        print(json_string)

    def write_area_settings(self, port: serial.Serial):
        if self.frame1.screen_map_frame.selected_mode.get():
            selected_screen_area = self.frame1.screen_map_frame.get_selected_screen_area()
            screen_bounding_box = self.frame1.screen_map_frame.get_bounding_box(
                [selected_screen_area]
            )
            self.frame1.screen_map_frame.shift_origin(
                selected_screen_area, screen_bounding_box
            )
            tablet_data = {
                "t.x": self.frame1.tablet_area.x_origin.get(),
                "t.y": 45
                - (
                    self.frame1.tablet_area.y_origin.get()
                    + self.frame1.tablet_area.y_size.get()
                ),
                "t.w": self.frame1.tablet_area.x_size.get(),
                "t.h": self.frame1.tablet_area.y_size.get(),
                "s.x": selected_screen_area.x0,
                "s.y": selected_screen_area.y0,
                "s.w": selected_screen_area.x1 - selected_screen_area.x0,
                "s.h": selected_screen_area.y1 - selected_screen_area.y0,
                "s.wm": screen_bounding_box.max_x - screen_bounding_box.min_x,
                "s.hm": screen_bounding_box.max_y - screen_bounding_box.min_y,
            }
        else:
            selected_screen_area = self.frame1.screen_map_frame.get_selected_screen_area()
            screen_bounding_box = self.frame1.screen_map_frame.get_bounding_box(
                monitor_list
            )
            self.frame1.screen_map_frame.shift_origin(
                selected_screen_area, screen_bounding_box
            )
            tablet_data = {
                "t.x": self.frame1.tablet_area.x_origin.get(),
                "t.y": 45
                - (
                    self.frame1.tablet_area.y_origin.get()
                    + self.frame1.tablet_area.y_size.get()
                ),
                "t.w": self.frame1.tablet_area.x_size.get(),
                "t.h": self.frame1.tablet_area.y_size.get(),
                "s.x": selected_screen_area.x0,
                "s.y": selected_screen_area.y0,
                "s.w": selected_screen_area.x1 - selected_screen_area.x0,
                "s.h": selected_screen_area.y1 - selected_screen_area.y0,
                "s.wm": screen_bounding_box.max_x - screen_bounding_box.min_x,
                "s.hm": screen_bounding_box.max_y - screen_bounding_box.min_y,
            }
        pprint(tablet_data)

        self.write_settings(port, tablet_data)

    def write_misc_settings(self, port: serial.Serial):
        tablet_data = {
            "left": bool(self.frame2.left_handed_var.get()),
            "f.a": bool(self.frame2.exp_filter_activate.get()),
            "f.c": float(self.frame2.exp_filter_delay.get()),
        }
        self.write_settings(port, tablet_data)

        pprint(tablet_data)

    def uploadSettings(self):
        comPort = self.get_serial_port_with_pid_vid(PID, VID)
        try:
            assert comPort is not None, "No Tablet Connected"
            with serial.Serial(comPort, baudrate=115200, timeout=0.5) as ser:
                fw_version = self.get_fw_version(ser)

                print("fw_version", fw_version)

                if int(fw_version) < 4:
                    raise Exception(
                        "Please Update Firmware Version to v0.5 or later through tools tab"
                    )

                time.sleep(0.1)

                self.write_area_settings(ser)
                self.write_misc_settings(ser)

        except Exception as e:
            messagebox.showerror(title="Upload Settings Error", message=e)
        else:
            messagebox.showinfo(
                title="Upload Complete",
                message="Upload Complete. Please unplug and replug tablet if screen area was changed.",
            )
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
root.geometry("338x715")
root.resizable(False, False)
root.title("HYKU Configurator")
root.iconbitmap(resolve_resource_path("favicon.ico"))

style = ttk.Style(root)

app = Application(root)
root.mainloop()
