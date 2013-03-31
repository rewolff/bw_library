from time import sleep

class EditHex():
    hexchar= ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
    def __init__(self,value=0x00,size=2,minval=0,maxval=0xFF,step=1,x=0, y=0,menu=None):
        self.length=size
        self.value=hex(value)[2:]
        while len(self.value) < self.length : self.value = "0"+ self.value
        self.cursorpos=0
        self.x=x
        self.y=y
        self.maxval=maxval
        self.minval=minval
        self.keepvalue=self.value
        self.step=step
        self.menu = menu

    def SetCursor(self):
        self.menu.Display.SetCursor(self.x+self.cursorpos,self.y)
        
    def Show(self):
        self.SetCursor()
        self.menu.Display.Print(self.value)
        self.SetCursor()
        sleep(.2)
        b = self.menu.Buttons.ReportPressed()
        b[self.menu.ButtonEnter]=False
        loop=True
        while loop:
            if b[self.menu.ButtonLeft]:
                if self.cursorpos>0:
                    self.cursorpos -= 1
                    self.SetCursor()
            if b[self.menu.ButtonRight]:
                if self.cursorpos<self.length-1:
                    self.cursorpos+=1
                    self.SetCursor()
            if b[self.menu.ButtonUp]:
                    c = int(self.value[self.cursorpos].lower(),16)
                    if c - self.step < len(self.hexchar)-1 and int(self.value.lower(),16)+self.step <= self.maxval:
                        self.menu.Display.SetCursor(self.x,self.y)
                        s=list(self.value)
                        s[self.cursorpos]=self.hexchar[c+self.step]
                        self.value=''.join(s)
                        self.menu.Display.Print(self.value)
                        self.SetCursor()
            if b[self.menu.ButtonDown]:
                    c = int(self.value[self.cursorpos].lower(),16)
                    if int(self.value.lower(),16) -self.step>=self.minval:
                        self.menu.Display.SetCursor(self.x,self.y)
                        s=list(self.value)
                        s[self.cursorpos]=self.hexchar[c-self.step]
                        self.value=''.join(s)
                        self.menu.Display.Print(self.value)
                        self.SetCursor()
            if b[self.menu.ButtonEsc]:
                return None
            if b[self.menu.ButtonEnter]:
                return int(self.value,16)
            b=self.menu.Buttons.ReportPressed()
            sleep(.2)

class MenuItem():
    def __init__(self,text ='', action = None,DisplayInit=True,value = None):
        self.DisplayInit = DisplayInit
        self.Text=text
        self.Value=value
        self.Action = action

    def Show(self):
        if self.Value:
            return self.Text+self.Value
        else:
            return self.Text

class Menu():
    Items = []
    CursorPosition = 0
    CursorLine = 0
    ButtonUp = 5
    ButtonDown = 4
    ButtonLeft = 3
    ButtonRight = 2
    ButtonEsc = 1
    ButtonEnter = 0
    
    def __init__(self, display, Items = [], buttons = None):
        self.Display = display
        if buttons == None:
            self.Buttons = self.Display
        else:
            self.Buttons = buttons
        self.Items = Items

    def Show(self, menu = None):
        self.CursorPosition=0
        self.CursorLine=0
        self.UpdateMenu()
        self.MenuLoop()
        self.Display.Cursor(False,False)

    def UpdateMenu(self, loop = False):
        self.Display.Cursor(False,False)
        line = 0
        while line<self.Display.Height:
            self.Display.SetCursor(0,line)
            if self.CursorPosition+line < len(self.Items):
                self.Display.Print(self.Items[self.CursorPosition+line].Show()+(" " * (self.Display.Width-len(self.Items[self.CursorPosition+line].Show()))))
            else:
                self.Display.Print(" "*self.Display.Width)
            line+=1
            self.Display.SetCursor(0,self.CursorLine)
        self.Display.Cursor(True,True)

    def MoveUp(self):
        if self.CursorLine>0:
            self.CursorLine-=1
            self.Display.SetCursor(0,self.CursorLine)
        elif self.CursorPosition>0:
            self.CursorPosition-=1
            self.UpdateMenu()

    def MoveDown(self):
        if self.CursorLine<self.Display.Height-1 and len(self.Items)> self.CursorPosition+self.CursorLine+1:
            self.CursorLine+=1
            self.Display.SetCursor(0,self.CursorLine)
        elif self.CursorLine == self.Display.Height-1 and len(self.Items)> self.CursorPosition+self.CursorLine+1:
            self.CursorPosition+=1
            self.UpdateMenu()
            self.Display.SetCursor(0,self.CursorLine)
            
            
    def MenuLoop(self):
        sleep(.1)
        self.Buttons.ReportPressed() #flush register
        Buttons = [False for i in range(0,self.Buttons.PushButtons)]
        while not Buttons[self.ButtonEsc]:
            if Buttons[self.ButtonUp]:
                self.MoveUp()
            if Buttons[self.ButtonDown]:
                self.MoveDown()
            if Buttons[self.ButtonEnter]:
                if self.Items[self.CursorLine+self.CursorPosition].Action != None:
                    if self.Items[self.CursorLine+self.CursorPosition].DisplayInit:
                        self.Display.Cls()
                        self.Display.SetCursor(0,0)
                    if hasattr(self.Items[self.CursorLine+self.CursorPosition].Action,"Show"):
                        ret = self.Items[self.CursorLine+self.CursorPosition].Action.Show(self)
                    else:
                        ret = self.Items[self.CursorLine+self.CursorPosition].Action()
#                    if ret != None:
#                        self.Items[self.CursorLine+self.CursorPosition].ChangeValue(ret)
                    self.UpdateMenu()
            sleep(.2)
            Buttons = self.Buttons.ReportPressed()
            #print Buttons

        self.Display.Cls()

def ProgressBar(value,minval=0, maxval=100 , Display = None, width = None, x=0, y=0):
    if Display != None:
        Display.DefineChar(0)
        Display.Cursor(on=False)
        #Display.DefineChar(0)      # Should be done once
        Display.SetCursor(x,y)
        size=Display.Width
    if width != None:
        size = width
    step=float(maxval-minval)/(size*5)
    full = int(value/step/5)

    rest = int(value/step) % 5
    if rest!=0:
        bar= chr(5)*full+chr(int(rest))
    else:
        bar= chr(5)*full
    if Display!= None:
        bar=bar+" " * (size-len(bar))
        Display.Print(bar)
    else:
        return bar
