import re, os, sys, json
import tkinter, tkinter.filedialog
from FdfParser import parse, get_value

def cnvRgnName(RgnDef):
    return re.search(r'FLASH_REGION_(.+)_[A-Z]+', RgnDef).group(1)

def getJsnKey(jsnPath, key):
    try:
        with open(cfgPath, 'r') as f:
            cfgDict = json.load(f)
            return cfgDict[key]
    except:
        return None

class MainGui:
    def __init__(self, rt, cfgDict):
        self.gui_interface_init(rt)

        menubar = tkinter.Menu(rt)
        fileMenu = tkinter.Menu(menubar, tearoff=0)
        fileMenu.add_command(label=" Load file... ", command=self.browser)
        menubar.add_cascade(label=" File ", menu=fileMenu)
        rt.config(menu=menubar)

        self.fdDict, self.macroDict, self.cfgDict = parse(cfgDict)
        self.buildFlashMap(rt)

    def gui_interface_init(self, rt):
        rt.title('FdVisualizer')
        rt.geometry("800x800+300+50")

    def browser(self):
        initDir = os.getcwd()
        filePath = tkinter.filedialog.askopenfile(title='Browse source path', initialdir=initDir)
        if filePath:
            self.fdfPath = filePath

    def buildFlashMap(self, rt):
        fdOffset, nulBlk= 0, 0
        for fd in self.fdDict:
            tkinter.Label(rt, text=fd, takefocus=True).grid(row=0, column=0, rowspan=2, columnspan=2, sticky='w', padx=10, pady=10)
            for idx, rgn in enumerate(self.fdDict[fd]):
                rgnOffset, rgnSize = get_value(rgn[0], self.macroDict), get_value(rgn[1], self.macroDict)
                if fdOffset < rgnOffset:
                    tkinter.Label(rt, text="", relief='groove', bg='gray'+ str(6 + ((idx + nulBlk) % 2) * 2) +'1', bd=2, width=50).grid(row=idx + nulBlk + 2, column=0, rowspan=2, columnspan=1, padx=15)
                    tkinter.Label(rt, text=hex(fdOffset)).grid(row=idx + nulBlk + 2, column=2, rowspan=1, columnspan=1, sticky='w')
                    nulBlk += 1
                tkinter.Label(rt, text=cnvRgnName(rgn[0]), relief='groove', bg='gray'+ str(6 + ((idx + nulBlk) % 2) * 2) +'1', bd=2, width=50).grid(row=idx + nulBlk + 2, column=0, rowspan=2, columnspan=1, padx=15)
                tkinter.Label(rt, text=hex(rgnOffset)).grid(row=idx + nulBlk + 2, column=2, rowspan=1, columnspan=1, sticky='w')
                fdOffset = rgnOffset + rgnSize
            tkinter.Label(rt, text=hex(fdOffset)).grid(row=idx + nulBlk + 2 + 1, column=2, rowspan=1, columnspan=1, sticky='w')

def main():

    with open('config.json', 'r') as f:
        cfgDict = json.load(f)

    root = tkinter.Tk()
    app = MainGui(root, cfgDict)
    root.mainloop()

if __name__ == '__main__':
    main()
