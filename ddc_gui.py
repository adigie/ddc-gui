#!/usr/bin/env python
import tkinter as tk
import subprocess
import re


class Display:
    class InvalidDisplayException(Exception):
        pass

    def __init__(self, data):
        lines = data.split("\n")
        if re.match("Display [0-9]+", lines[0]) is None:
            raise self.InvalidDisplayException()
        self.bus = re.match("\s+I2C bus:\s+/dev/i2c-(?P<bus>[\d]+)", lines[1]).groupdict()["bus"]
        self.model = re.match("\s+Model:\s+(?P<model>\S.*)", lines[4]).groupdict()["model"]


class DisplayFrame(tk.LabelFrame):
    def __init__(self, display, master=None):
        super().__init__(master, text=display.model)
        self.pack()

        scale_b = tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL)
        scale_b.config(command=lambda value, ref=scale_b: self.on_scroll(value, ref))
        scale_b.config(length=400)
        scale_b.pack(side="top")
        scale_b._job = None
        scale_b._bus = display.bus
        scale_b._code = "0x10"
        scale_b.set(self.read_value(display.bus, "0x10"))

        scale_c = tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL)
        scale_c.config(command=lambda value, ref=scale_c: self.on_scroll(value, ref))
        scale_c.config(length=400)
        scale_c.pack(side="top")
        scale_c._job = None
        scale_c._bus = display.bus
        scale_c._code = "0x12"
        scale_c.set(self.read_value(display.bus, "0x12"))

    def read_value(self, bus, code):
        out = subprocess.check_output(["ddcutil", "--bus", bus, "getvcp", code]).decode()
        return int(out[63:69])

    def on_scroll(self, value, ref):
        if ref._job:
            ref.after_cancel(ref._job)
        ref._job = ref.after(500, lambda: self.on_scroll_complete(ref._bus, ref._code, value))

    def on_scroll_complete(self, bus, code, value):
        subprocess.check_output(["ddcutil", "--bus", bus, "setvcp", code, value])


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        out = subprocess.check_output(["ddcutil", "detect"]).decode()
        data = out.split("\n\n")
        for d in data:
            try:
                frame = DisplayFrame(Display(d), master=self)
                frame.pack(side="top")
            except Display.InvalidDisplayException:
                pass


root = tk.Tk()
app = Application(master=root)
app.mainloop()
