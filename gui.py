import tkinter as tk

from lib import *
from tkcalendar import Calendar

import pprint
import datetime
import sys
import functools

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
                            font=FONT, selectmode='day',
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
        
        
        self.rootFrame = tk.Frame(self)
        self.rootFrame.pack()
        
        self.mainFrame = tk.Frame(self.rootFrame)
        self.mainFrame.grid(sticky='news')
        
        max_abstract_depth = max([pprint.pformat(x['abstract'], width=120).count('\n') for x in resDict]) - 1
        self.abstractFrame = tk.Label(self, text=' \n'*max_abstract_depth, font=FONT)
        self.abstractFrame.pack()
        
        
        
        # Create a frame for the canvas with non-zero row&column weights
        frame_canvas = tk.Frame(self.mainFrame)
        frame_canvas.grid(row=2, column=0, pady=(5, 0), sticky='nw')
        frame_canvas.grid_rowconfigure(0, weight=1)
        frame_canvas.grid_columnconfigure(0, weight=1)
        
        # Set grid_propagate to False to allow 5-by-5 buttons resizing later
        frame_canvas.grid_propagate(False)
        
        # Add a canvas in that frame
        canvas = tk.Canvas(frame_canvas)#, bg="yellow")
        canvas.grid(row=0, column=0, sticky="news")
        
        # Link a scrollbar to the canvas
        vsb = tk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        canvas.configure(yscrollcommand=vsb.set)
        
        self.gridFrame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.gridFrame, anchor='nw')
        
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
        
        self.bttns = []
        num_cols = 3
        
        
        
        for row_idx, tr in enumerate(list(chunks(resDict, num_cols))):
            for col_idx, td in enumerate(tr):
                bttn = DownloadPickerButton(self.gridFrame, td['name'], td['abstract'], self.abstractFrame, max_abstract_depth)
                bttn.grid(row=row_idx, column=col_idx, sticky='news', pady=(5, 0), padx=(5, 0))
                self.bttns.append(bttn)
        
        self.gridFrame.update_idletasks()
        
        # Resize the canvas frame to show exactly 5-by-5 buttons and the scrollbar
        first5columns_width = max([x.winfo_width() for x in self.bttns]) * num_cols
        first5rows_height = self.master.winfo_height() // 2
        
        print(first5columns_width, first5rows_height)
        frame_canvas.config(width=first5columns_width + vsb.winfo_width(),
                            height=first5rows_height)
        
        # Set the canvas scrolling region
        canvas.config(scrollregion=canvas.bbox("all"))
        
        
        
        def submit_action():
            self.destroy()
            self.master.quit()
        
        self.submit_button = tk.Button(self.mainFrame, text="SUBMIT", fg="green",
                                       command=submit_action, font=FONT)
        self.submit_button.grid(row=0, column=0)

class DownloadPickerButton(tk.Button):
    def __init__(self, master=None, name=None, abstract=None, abstractFrame=None, max_abstract_depth=None):
        
        self.master = master
        self.name = name
        self.abstract = abstract
        self.pressed = False
        self.DefClr = master.cget("bg")
        self.abstractFrame = abstractFrame
        self.max_abstract_depth = max_abstract_depth
        fmt_name = pprint.pformat(self.name, width=30)
        super().__init__(self.master, text=fmt_name, command=self.myCommand, font=('Arial',15))
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        formatted_abstract = pprint.pformat(self.abstract, width=120)
        self.abstractFrame.configure(text=formatted_abstract)
    
    def on_leave(self, enter):
        self.abstractFrame.configure(text=" \n"*self.max_abstract_depth)
    
    
    def myCommand(self):
        self.pressed = not self.pressed
        if self.pressed:
            self.config(bg='green', relief=tk.SUNKEN)
        else:
            self.config(bg=self.DefClr, relief=tk.RAISED)


class SaveMethod(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH)
        self.label = tk.Label(self, text='How would you like to save the files?', font=FONT)
        self.label.pack(side='top')
        
        self.selected = None
        
        
        fmt_to_hint = {
            'mp4': 'Normal mp4 download',
            'dvd': 'Save in the same format that appears on the dvd',
            'iso': 'Same as dvd option, but contained within a .iso file, for later burning'
        }
        
        
        
        gridFrame = tk.Frame(self)
        gridFrame.pack()
        
        
        fmt_to_bttn = {}
        
        def bttn_action(fmt):
            def bttn_action_wrapper(*args, **kwargs):
                self.selected = fmt
                for bttn in fmt_to_bttn.values():
                    bttn.config(relief=tk.RAISED)
                fmt_to_bttn[fmt].config(relief=tk.SUNKEN)
            return bttn_action_wrapper
        
        self.abstractFrame = tk.Label(self, text='', font=FONT)
        self.abstractFrame.pack()
        
        def on_enter(fmt):
            def on_enter_wrapper(event):
                formatted_abstract = pprint.pformat(fmt_to_hint[fmt])
                self.abstractFrame.configure(text=formatted_abstract)
            return on_enter_wrapper
        
        def on_leave(event):
            self.abstractFrame.configure(text='')
        
        
        mp4 = tk.Button(gridFrame, text='.mp4', font=FONT, command=bttn_action('mp4'))
        mp4.grid(row=1, column=0)
        mp4.bind("<Enter>", on_enter('mp4'))
        mp4.bind("<Leave>", on_leave)
        fmt_to_bttn['mp4'] = mp4
        
        dvd = tk.Button(gridFrame, text='.dvd', font=FONT, command=bttn_action('dvd'))
        dvd.grid(row=1, column=1)
        dvd.bind("<Enter>", on_enter('dvd'))
        dvd.bind("<Leave>", on_leave)
        fmt_to_bttn['dvd'] = dvd
        
        iso = tk.Button(gridFrame, text='.iso', font=FONT, command=bttn_action('iso'))
        iso.grid(row=1, column=2)
        iso.bind("<Enter>", on_enter('iso'))
        iso.bind("<Leave>", on_leave)
        fmt_to_bttn['iso'] = iso
        
        
        self.keep_mp4_var = tk.BooleanVar()
        self.keep_mp4 = tk.Checkbutton(self, text="Also keep the downloaded mp4 file?", font=FONT, variable=self.keep_mp4_var)
        self.keep_mp4.pack()
        
        def submit_action():
            self.destroy()
            self.master.quit()
        
        submit_button = tk.Button(self, text="SUBMIT", fg="green",
                                  command=submit_action, font=FONT)
        submit_button.pack(side='bottom')


class GUI(object):
    def __init__(self):
        self.root = tk.Tk()
        self.series = None
        self.date_selected = None
        self.pickedShows = []
        self.fmt = None
        self.keep_mp4 = True
    
    def __enter__(self):
        self.saveMethod()
        if not self.fmt:
            print("Goodbye!")
            sys.exit(0)
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
    
    def saveMethod(self):
        self.root.state('zoomed')
        app = SaveMethod(self.root)
        app.mainloop()
        self.fmt = app.selected
        self.keep_mp4 = app.keep_mp4_var.get()
    
    def seriesPicker(self):
        app = SeriesPicker(self.root)
        app.mainloop()
        self.series = app.pathVar.get()
        return self.series
    
    def datePicker(self):
        cal = DatePicker(self.root)
        cal.mainloop()
        selected_date = cal.cal.selection_get()
        
        # CSPAN calendar shows sat, sun, mon, but resolves to it for sun-sat, skipping
        #   to the next week
        
        if selected_date.weekday() in [6,0]:
            selected_date -= datetime.timedelta(days=1 if selected_date.weekday() else 2)
        
        
        self.date_selected = selected_date
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

