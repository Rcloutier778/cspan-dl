import tkinter as tk

from lib import *
from tkcalendar import Calendar, DateEntry

import pprint
import datetime



class SeriesPicker(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(text='Pick a series', font=('Arial',20))
        self.label.pack(side='top')

        self.pathVar = tk.StringVar()
        self.path = tk.Entry(textvariable=self.pathVar)

        for sName in SERIES_NAME_TO_ID_DICT:
            bttn = SeriesButton(self.master, sName, self.pathVar)
            bttn.pack()
        
        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=self.master.destroy, font=('Arial',20))
        self.quit.pack(side="bottom")

class SeriesButton(tk.Button):
    def __init__(self, master=None, seriesName=None, pathVar=None):
        
        self.master = master
        assert seriesName in SERIES_NAME_TO_ID_DICT
        self.seriesName = seriesName
        assert pathVar is not None
        self.pathVar = pathVar
        fmt_name = pprint.pformat(self.seriesName, width=30)
        super().__init__(self.master, text=fmt_name, command=self.myCommand, font=('Arial',20))
        self.pathVar = pathVar

    def myCommand(self):
        self.pathVar.set( self.seriesName)
        self.master.destroy()
              

def seriesPickerMain():
    root=tk.Tk()
    app = SeriesPicker(root)
    app.mainloop()
    returnVal = app.pathVar.get()
    return returnVal

def datePicker():
    root = tk.Tk()

    pathVar = tk.StringVar()
    path = tk.Entry(textvariable=pathVar)
    def print_sel():
        pathVar = cal.selection_get()
        root.destroy()
        
    

    today = datetime.date.today()
    lastWeekend = today - datetime.timedelta(days=1+(today.weekday()+1)%7)

    cal = Calendar(root,
                   font="Arial 14", selectmode='day',
                   cursor="hand1", year=lastWeekend.year, month=lastWeekend.month, day=lastWeekend.day)
    cal.pack(fill="both", expand=True)
    tk.Button(root, text="ok", command=print_sel, font=('Arial',20)).pack()
    root.mainloop()
    return cal.selection_get()


class DownloadPicker(tk.Frame):
    def __init__(self, master, resDict):
        super().__init__(master)

        
        self.pathVar = tk.StringVar()
        self.path = tk.Entry(textvariable=self.pathVar)


        self.gridFrame = tk.Frame(self.master)

        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]
    
        self.abstractFrame = tk.Label(self.master, text=' '*90, font=('Arial',30))
        

        for row_idx, tr in enumerate(list(chunks(resDict,3))):
            for col_idx, td in enumerate(tr):
                bttn = DownloadPickerButton(self.gridFrame, td['name'], td['abstract'], self.path, self.abstractFrame)
                bttn.grid(row=row_idx+1, column=col_idx)
                #bttn.pack()
                
        self.quit = tk.Button(self.gridFrame, text="SUBMIT", fg="green",
                              command=self.master.destroy, font=('Arial',20))
        self.gridFrame.pack()
        self.abstractFrame.pack(expand=True)
        self.quit.grid(row=0, column=1)

# Couldn't figure out how to have multiple button actions feeding into a single tikinter extractable var
#   so globals away!
# This is probably bad programming. Too Bad!
SELECTED=[]
class DownloadPickerButton(tk.Button):
    def __init__(self, master=None, name=None, abstract=None, pathVar=None, abstractFrame=None):
        
        self.master = master
        self.name = name
        self.abstract = abstract
        assert pathVar is not None
        self.pathVar = pathVar
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
        global SELECTED
        if self.pressed:
            self.pathVar = self.name
            SELECTED.append(self.name)
            self.config(bg='green', relief=tk.SUNKEN)
        else:
            self.pathVar = ''
            SELECTED.remove(self.name)
            self.config(bg=self.DefClr, relief=tk.RAISED)


def downloadPckerMain(resDict):
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    app = DownloadPicker(root, resDict)
    app.mainloop()
    returnVal = app.pathVar.get()
    global SELECTED
    return SELECTED




if __name__ == '__main__':
    seriesPickerMain()
    print('debug only. dad should not see this bit')

