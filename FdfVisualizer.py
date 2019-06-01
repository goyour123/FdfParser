import re, os, sys, json
import tkinter, tkinter.filedialog, tkinter.messagebox
from warnings import warn
from FdfParser import parse, get_value, dictUpdateJson
from FdfRestorer import restore, hexFillZero

MAX_FD_NUM = 3
MIN_SIZE = '0x1000'
MAX_SIZE = '0x1000000'

def cnvRgnName(rgnDef):
    return re.search(r'[FLASH]+_REGION_(.+)_[A-Z]+', rgnDef).group(1)

def getJsnKey(jsnPath, key):
    try:
        with open(cfgPath, 'r') as f:
            cfgDict = json.load(f)
            return cfgDict[key]
    except:
        return None

def setDisplayHex(h):
    return '0x' + ((h[2:].zfill(7))[0:3] + '_' + (h[2:].zfill(7))[3:7]).upper()

def revDisplayHex(s):
    return s.replace('_', '')

class MainGui:
    def __init__(self, rt, cfgDict):

        self.rt = rt
        self.cfgDict = cfgDict
        self.loadCfgFile, self.switchSel = None, None
        self.preSelRgnWidget, self.preSelRgnColor, self.preSelRgnBaseWidget, self.preSelRgnEndWidget = None, None, None, None
        self.curFd = None

        # Menubar
        menubar = tkinter.Menu(self.rt)
        fileMenu = tkinter.Menu(menubar, tearoff=0)
        fileMenu.add_command(label=" Load FDF file... ", command=self.browser)
        menubar.add_cascade(label=" File ", menu=fileMenu)
        self.rt.config(menu=menubar)

        # Flash Canvas
        self.canvas = tkinter.Canvas(self.rt)
        self.flashCanvas = tkinter.Canvas(self.canvas, height=460, width=460, highlightthickness=0)
        self.flashFrame = tkinter.Frame(self.flashCanvas, relief='sunken', bd=2)
        self.flashCanvas.create_window((0, 0), window=self.flashFrame, anchor='nw')

        # Listbox for each FD
        self.fdListbox = tkinter.Listbox(self.rt, height=MAX_FD_NUM, width=20, selectmode=tkinter.BROWSE)
        self.fdListbox.bind('<<ListboxSelect>>', self.onSelect)

        # Scrollbar of Flash Canvas frame
        self.scrollbarFlash = tkinter.Scrollbar(self.canvas, command=self.flashCanvas.yview)

        # Button of parsing file
        self.prsBtn = tkinter.Button(self.rt, text='Parse', command=self.prsBtnCallback, height=3, width=10, state=tkinter.DISABLED, cursor='arrow')

        # Canvas of checkbutton
        self.cbCanvas = tkinter.Canvas(self.rt)
        self.cbInCanvas = tkinter.Canvas(self.cbCanvas, height=50, width=205, relief='groove', bd=1)
        self.cbFrame = tkinter.Frame(self.cbInCanvas)
        self.cbInCanvas.create_window((0, 0), window=self.cbFrame, anchor='nw')

        # Scrollbar of checkbutton frame
        self.scrollbarCb = tkinter.Scrollbar(self.cbCanvas, command=self.cbInCanvas.yview)

        # Entrybox of flash region size
        self.rgnSizeEntry = tkinter.Entry(self.rt, state='disabled', width=18)
        self.rgnSizeEntry.bind('<Return>', self.enterSize)

        # Label of flash region size
        self.rgnSizeLabel = tkinter.Label(self.rt, width=45, anchor='e')

        self.fdListbox.place(x=10, y=6)
        self.cbCanvas.place(x=155, y=5)
        self.prsBtn.place(x=390, y=5)
        self.rgnSizeEntry.place(x=340, y=68)
        self.rgnSizeLabel.place(x=10, y=67)
        self.canvas.place(x=10, y=95)

        self.scrollbarFlash.pack(side=tkinter.RIGHT, fill='y')
        self.scrollbarCb.pack(side=tkinter.RIGHT, fill='y')

        self.flashCanvas.pack()
        self.cbInCanvas.pack()

        self.flashCanvas.configure(yscrollcommand = self.scrollbarFlash.set)
        self.flashCanvas.bind('<Configure>', self.flashOnConfig)

        self.cbInCanvas.configure(yscrollcommand = self.scrollbarCb.set)
        self.cbInCanvas.bind('<Configure>', self.cbOnConfig)

        if 'Fdf' in cfgDict:
            self.sortedfdDict, self.macroDict, self.cfgDict, self.switchInused, self.fdInfo = parse(self.cfgDict)
            self.cr8FdListbox()
            self.cr8DynCheckbtn()
            self.prsBtn.configure(state=tkinter.NORMAL, cursor='spider')

    def flashOnConfig(self, evt):
        self.flashCanvas.configure(scrollregion=self.flashCanvas.bbox('all'))

    def cbOnConfig(self, evt):
        self.cbInCanvas.configure(scrollregion=self.cbInCanvas.bbox('all'))

    def enterSize(self, evt):
        if self.rgnSizeEntry.cget('state') == 'disabled':
            return

        try:
            newSize = hex(int((self.rgnSizeEntry.get()).upper(), 16))
        except:
            tkinter.messagebox.showerror('Error', 'Invalid Value!')
            self.rgnSizeEntry.delete(0, 'end')
            self.rgnSizeEntry.insert(0, self.rgnSize.upper())
            return
        else:
            if int(newSize, 16) == int(self.rgnSize, 16):
                return
            elif (int(newSize, 16) % int('0x1000', 16) != 0) or int(newSize, 16) > int(MAX_SIZE, 16) or int(newSize, 16) <= 0:
                tkinter.messagebox.showerror('Error', 'Invalid Value!' )
                self.rgnSizeEntry.delete(0, 'end')
                self.rgnSizeEntry.insert(0, self.rgnSize.upper())
                return

        sLabel = self.rgnSizeLabel.cget('text')
        for macro in self.macroDict:
            l = re.search('[FLASH]+_REGION_' + sLabel + '_SIZE', macro)
            if l:
                label = l.group(0)
                break

        newSize = newSize[0:2] + (newSize[2:]).upper()
        restore(self.cfgDict, self.switchInused, label, hexFillZero(newSize, 8))
        self.prsBtnCallback()

        e = tkinter.Event()
        for w in self.flashFrame.winfo_children():
            if w.cget('text') == sLabel:
                e.widget = w
                break
        self.rgnButtonCallback(e)

    def prsBtnCallback(self):
        self.sortedfdDict, self.macroDict, self.cfgDict, self.switchInused, self.fdInfo = parse(self.cfgDict)
        self.buildFlashMap()
        self.flashFrame.update_idletasks()
        self.flashCanvas.configure(scrollregion=self.flashCanvas.bbox('all'))

    def browser(self):
        if 'Fdf' in self.cfgDict:
            initDir = os.path.dirname(self.cfgDict['Fdf'])
        else:
            initDir = os.getcwd()
        loadCfgFile = tkinter.filedialog.askopenfile(title='Browse source path', initialdir=initDir, filetypes=[("fdf", "*.fdf")])
        if loadCfgFile:
            self.cfgDict.update({'Fdf': loadCfgFile.name})
            self.sortedfdDict, self.macroDict, self.cfgDict, self.switchInused, self.fdInfo = parse(self.cfgDict)
            self.cr8FdListbox()
            self.cr8DynCheckbtn()
            self.prsBtn.configure(state=tkinter.NORMAL, cursor='spider')
            self.loadCfgFile = loadCfgFile

    def onSelect(self, evt):
        sel = self.fdListbox.curselection()
        if not sel:
            return
        selFd = self.fdListbox.get(sel[0])
        if self.curFd != selFd:
            self.curFd = selFd
            self.buildFlashMap()
            self.flashFrame.update_idletasks()
            self.flashCanvas.configure(scrollregion=self.flashCanvas.bbox('all'))

    def cr8DynCheckbtn(self):
        self.cbDict = {}
        for w in self.cbFrame.winfo_children():
            w.destroy()

        for idx, switch in enumerate(self.switchInused):
            self.cbDict.update({switch: tkinter.IntVar()})
            cb = tkinter.Checkbutton(self.cbFrame, text=switch, variable=self.cbDict[switch], command=self.checkBtnCallback)
            if self.switchInused[switch] == 'YES':
                cb.select()
            cb.grid(row=idx, column=0, sticky=tkinter.NW)
        self.cbFrame.update_idletasks()
        self.cbInCanvas.configure(scrollregion=self.cbInCanvas.bbox('all'))

    def checkBtnCallback(self):
        for switch in self.cbDict:
            if self.cbDict[switch].get() == 1:
                self.cfgDict['Switch'].update({switch: 'YES'})
            else:
                self.cfgDict['Switch'].update({switch: 'NO'})
        self.switchSel = True
        self.prsBtnCallback()

    def cr8FdListbox(self):
        self.fdListbox.delete(0, 'end')
        if self.sortedfdDict:
            for fd in self.sortedfdDict:
                self.fdListbox.insert('end', fd)
            self.fdListbox.selection_set(0, None)
            self.curFd = self.fdListbox.selection_get()
            self.buildFlashMap()
            self.flashFrame.update_idletasks()
            self.flashCanvas.configure(scrollregion=self.flashCanvas.bbox('all'))
        elif self.fdInfo:
            warn('The sortedfdDict is empty. Use fdInfo instead.')
            for fd in self.fdInfo:
                self.fdListbox.insert('end', fd)
        else:
            warn('No FD infomation was found.')

    def rgnButtonCallback(self, evt):
        # Restore the previous selected label's background color
        if self.preSelRgnWidget:
            self.preSelRgnWidget.configure(bg=self.preSelRgnColor)
            self.preSelRgnBaseWidget.configure(bg='SystemButtonFace')
            self.preSelRgnEndWidget.configure(bg='SystemButtonFace')
        self.preSelRgnWidget = evt.widget
        self.preSelRgnColor = evt.widget.cget('bg')

        # Configure the selected label's backgroundcolor
        evt.widget.configure(bg='#34d100')
        evt.widget.focus_set()
        rgnGridRow = evt.widget.grid_info()['row']

        for w in self.flashFrame.winfo_children():
            if re.match(r'0x[0-9A-F]+_[0-9A-F]+', w.cget('text')):
                if w.grid_info()['row'] == rgnGridRow:
                    self.preSelRgnBaseWidget = w
                    w.configure(bg='#fa5fa5')
                elif w.grid_info()['row'] == rgnGridRow + 1:
                    self.preSelRgnEndWidget = w
                    w.configure(bg='#fd5fd5')
                    self.rgnSize = hex(int(revDisplayHex(self.preSelRgnEndWidget.cget('text')), 16) - \
                                    int(revDisplayHex(self.preSelRgnBaseWidget.cget('text')), 16))[2:]

        self.rgnSizeEntry.configure(state='normal')
        self.rgnSizeEntry.delete(0, 'end')
        self.rgnSizeEntry.insert(0, self.rgnSize.upper())
        if not evt.widget.cget('text'):
            self.rgnSizeEntry.configure(state='disabled')

        self.rgnSizeLabel.configure(text=evt.widget.cget('text'))

    def buildFlashMap(self):
        fdOffset, nulBlk, rgnLabel = 0, 0, None
        labelHeight = None
        fdDict = self.sortedfdDict

        for w in self.flashFrame.winfo_children():
            self.preSelRgnWidget, self.preSelRgnColor, self.preSelRgnBaseWidget, self.preSelRgnEndWidget = None, None, None, None
            self.rgnSizeEntry.delete(0, 'end')
            self.rgnSizeEntry.configure(state="disabled")
            self.rgnSizeLabel.configure(text='')
            w.destroy()

        for idx, rgn in enumerate(fdDict[self.curFd]):
            rgnOffset, rgnSize = get_value(rgn[0], self.macroDict), get_value(rgn[1], self.macroDict)
            if fdOffset < rgnOffset:
                rgnLabel = tkinter.Label(self.flashFrame, text="", relief='ridge', bg='gray'+ str(6 + ((idx + nulBlk) % 2) * 2) +'1', bd=2, width=50, height=labelHeight)
                rgnLabel.grid(row=idx + nulBlk, column=0, rowspan=2, columnspan=1, padx=8)
                rgnLabel.bind('<Button-1>', self.rgnButtonCallback)
                tkinter.Label(self.flashFrame, text=setDisplayHex(hex(fdOffset)), height=labelHeight, width=9).grid(row=idx + nulBlk, column=1, rowspan=1, columnspan=1, sticky='w')
                nulBlk += 1
            rgnLabel = tkinter.Label(self.flashFrame, text=cnvRgnName(rgn[0]), relief='ridge', bg='gray'+ str(6 + ((idx + nulBlk) % 2) * 2) +'1', bd=2, width=50, height=labelHeight)
            rgnLabel.grid(row=idx + nulBlk, column=0, rowspan=2, columnspan=1, padx=8)
            rgnLabel.bind('<Button-1>', self.rgnButtonCallback)
            tkinter.Label(self.flashFrame, text=setDisplayHex(hex(rgnOffset)), height=labelHeight, width=9).grid(row=idx + nulBlk, column=1, rowspan=1, columnspan=1, sticky='w')
            fdOffset = rgnOffset + rgnSize
        tkinter.Label(self.flashFrame, text=setDisplayHex(hex(fdOffset)), height=labelHeight, width=9).grid(row=idx + nulBlk + 1, column=1, rowspan=1, columnspan=1, sticky='w')

def main():
    try:
        with open('config.json', 'r') as f:
            cfgDict = json.load(f)
            if not os.path.isfile(cfgDict['Fdf']):
                cfgDict = {}
    except:
        cfgDict = {}

    root = tkinter.Tk()
    app = MainGui(root, cfgDict)

    root.iconbitmap(r'.\img\trilobite.ico')
    root.title('FdVisualizer')
    root.geometry("515x590+450+40")

    root.mainloop()

    if app.loadCfgFile or app.switchSel:
        dictUpdateJson('config.json', app.cfgDict)

if __name__ == '__main__':
    main()
