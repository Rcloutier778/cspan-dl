import tkinter as tk

from lib import *
from tkcalendar import Calendar

import pprint
import datetime
import sys

FONT = ('Arial', 20)

class SeriesPicker(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.label = tk.Label(self, text='Pick a series', font=FONT)
        self.label.pack(side='top')

        self.pathVar = tk.StringVar()
        self.path = tk.Entry(textvariable=self.pathVar)

        for sName in SERIES_NAME_TO_ID_DICT:
            bttn = SeriesButton(self, sName, self.pathVar)
            bttn.pack()

        def quit_action():
            self.destroy()
            self.master.quit()

        self.quit_button = tk.Button(self, text="QUIT", fg="red",
                              command=quit_action, font=FONT)
        self.quit_button.pack(side="bottom")

class SeriesButton(tk.Button):
    def __init__(self, master, seriesName, pathVar):
        
        self.master = master
        assert seriesName in SERIES_NAME_TO_ID_DICT
        self.seriesName = seriesName
        self.pathVar = pathVar
        fmt_name = pprint.pformat(self.seriesName, width=30)
        super().__init__(self.master, text=fmt_name, command=self.myCommand, font=FONT)
        self.pathVar = pathVar

    def myCommand(self):
        self.pathVar.set(self.seriesName)
        self.master.destroy()
        self.master.quit()


class DatePicker(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()
        self.master = master

        today = datetime.date.today()
        lastWeekend = today - datetime.timedelta(days=1 + (today.weekday() + 1) % 7)

        self.cal = Calendar(self,
                       font="Arial 14", selectmode='day',
                       cursor="hand1", year=lastWeekend.year, month=lastWeekend.month, day=lastWeekend.day)
        self.cal.pack(fill="both", expand=True)

        def quit_action():
            self.destroy()
            self.master.quit()

        tk.Button(self, text="ok", command=quit_action, font=('Arial', 20)).pack()

class DownloadPicker(tk.Frame):
    def __init__(self, master, resDict):
        super().__init__(master)
        self.master = master
        self.pack()

        self.gridFrame = tk.Frame(self)

        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
    
        self.abstractFrame = tk.Label(self, text=' '*90, font=('Arial',30))
        
        self.bttns = []
        for row_idx, tr in enumerate(list(chunks(resDict,3))):
            for col_idx, td in enumerate(tr):
                bttn = DownloadPickerButton(self.gridFrame, td['name'], td['abstract'], self.abstractFrame)
                bttn.grid(row=row_idx+1, column=col_idx)
                self.bttns.append(bttn)

        def submit_action():
            self.destroy()
            self.master.quit()

        self.submit_button = tk.Button(self.gridFrame, text="SUBMIT", fg="green",
                              command=submit_action, font=FONT)
        self.gridFrame.pack()
        self.abstractFrame.pack(expand=True)
        self.submit_button.grid(row=0, column=1)

class DownloadPickerButton(tk.Button):
    def __init__(self, master=None, name=None, abstract=None, abstractFrame=None):
        
        self.master = master
        self.name = name
        self.abstract = abstract
        self.pressed = False
        self.DefClr = master.cget("bg")
        self.abstractFrame = abstractFrame
        fmt_name = pprint.pformat(self.name, width=50)
        super().__init__(self.master, text=fmt_name, command=self.myCommand, font=('Arial',15))
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        formatted_abstract = pprint.pformat(self.abstract)
        self.abstractFrame.configure(text=formatted_abstract)

    def on_leave(self, enter):
        self.abstractFrame.configure(text=" "*90)
        

    def myCommand(self):
        self.pressed = not self.pressed
        if self.pressed:
            self.config(bg='green', relief=tk.SUNKEN)
        else:
            self.config(bg=self.DefClr, relief=tk.RAISED)

class GUI(object):
    def __init__(self):
        self.root = tk.Tk()
        self.series = None
        self.date_selected = None
        self.pickedShows = []

    def __enter__(self):
        self.seriesPicker()
        if not self.series:
            print("Goodbye!")
            sys.exit(0)
        self.datePicker()
        if not self.date_selected:
            print('Goodbye!')
            sys.exit(0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.root.destroy()

    def seriesPicker(self):
        app = SeriesPicker(self.root)
        app.mainloop()
        self.series = app.pathVar.get()
        return self.series

    def datePicker(self):
        cal = DatePicker(self.root)
        cal.mainloop()
        self.date_selected = cal.cal.selection_get()
        return self.date_selected

    def downloadPicker(self, resDict):
        self.root.state('zoomed')

        app = DownloadPicker(self.root, resDict)
        app.mainloop()
        self.pickedShows = [bttn.name for bttn in app.bttns if bttn.pressed]
        if not self.pickedShows:
            print('Goodbye!')
            sys.exit(0)
        return self.pickedShows


if __name__ == '__main__':
    with GUI() as gui:
        print(gui.series)
        print(gui.date_selected)

    print('debug only. dad should not see this bit')

