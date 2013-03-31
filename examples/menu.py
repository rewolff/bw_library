"""
    Demo for ui.Menu class

    Requires:
    SPI_RPi_Ui20x4

    External MCP9700 connected to AD on Ui board

    SPI_DIO (with Default Address)
    10k Potentiometer connected to SPI_DIO, this will show progressbar:
       5V-[     ] -GND
             ^
             |
            AD0

    BigRelay/Relay to test relays after SPI Bus Scan

    Buttons on Ui are defined like:

    Up - Down - Left - Right - Esc - Enter

    Press Esc on top level menu will exit apllication

    know bug: Change Address Hexedit Step works on all digits

    After Bus Scan, Select device for more functions.
    Like test relay #nr (latched)
    Even the Address of active Ui can be changed.
    

"""

from BitWizard.bw import *# Import SPI and device classes
from BitWizard.ui import *  # import Menu and HexEditor
import struct

class TestRelay():

    def __init__(self,address):
        self.Address = address

    def Latch(self):
        Relay=self.menu.CursorPosition+self.menu.CursorLine
        self.menu.Display.SetCursor(self.menu.Display.Width-2,self.menu.CursorLine)
        self.menu.Display.Print("On")
        self.Device.Pins[Relay].Set(True)
        sleep(.5)
        self.Device.Pins[Relay].Set(False)

    def Show(self,menu):
        self.Bus = menu.Display.Bus
        self.Device=self.Bus.Devices[self.Address].InUseBy
        self.menu = Menu(menu.Display,[])
        for i in range(0,self.Device.IOPins):
            self.menu.Items.append(MenuItem('Test Relay : '+str(i),DisplayInit=False, action=self.Latch))
        self.menu.Show()
    

class Temperature():

    def __init__(self):
        pass

    def Show(self,menu):
        menu.Display.Print("Interne Temperatuur:")
        menu.Display.SetCursor(0,2)
        menu.Display.Print("Externe Temperatuur:")
        menu.Display.Cursor(False,False)
        while not menu.Buttons.ReportPressed()[menu.ButtonEsc]:
            I= menu.Display.IntTemp.GetCelcius()
            menu.Display.SetCursor(16,1)
            menu.Display.Print(str(round(I,1)))
            E= menu.Display.ExtTemp.GetCelcius()
            menu.Display.SetCursor(16,3)
            menu.Display.Print(str(round(E,1)))
            sleep(.2)
        
class Potmeter():

    def __init__(self):
        pass

    @staticmethod
    def Show(menu):
        dio = DIO(menu.Display.Bus)
        dio.SetPinConfig(0,AnalogIn)
        menu.Display.Print("Draai aan knop")
        menu.Display.SetCursor(0,1)
        menu.Display.Print("Waarde:")
        menu.Display.Cursor(False,False)
        oldvalue = 0
        while not menu.Buttons.ReportPressed()[menu.ButtonEsc]:
            value=dio.Pins[0].GetSample()
            if value != oldvalue:
                oldvalue = value
                menu.Display.SetCursor(menu.Display.Width-len("%4d" % value),1)
                menu.Display.Print("%4d"% value)
                if menu.Display.Height>=3:
                    ProgressBar(value,Display=menu.Display, maxval = 1023,y=2)
            sleep(.2)


class Config():    

    def __init__(self,Address = None, ParentMenu=None):
        self.Address = Address
        self.ParentMenu=ParentMenu


    def ChangeAddress(self):
        new = EditHex(value=self.Address,size=2, step = 2,x=17,y=self.menu.CursorLine, menu=self.menu).Show()
        if new!= None:  #Handle Escape press  
            if self.menu.Display.Bus.Devices[self.Address].InUseBy!=None:
                Device=self.menu.Display.Bus.Devices[self.Address].InUseBy
            else:
                Device = BitWizardBase(self.menu.Display.Bus,address=self.Address)
            Device.ChangeAddress(new)
            self.Address = new
            self.ChangeAddressMenuItem.Value=hex(new)[2:]
            self.ParentMenu.Items=[]
            for A in sorted(self.menu.Display.Bus.Devices.iterkeys()):
                self.ParentMenu.Items.append(MenuItem(hex(A)[2:]+" " +self.menu.Display.Bus.Devices[A].Ident,Config(A,self.ParentMenu)))


    def Show(self,menu):
        self.menu = Menu(menu.Display,[])
        self.ChangeAddressMenuItem=MenuItem('Change Address : ',value=hex(self.Address)[2:],action=self.ChangeAddress,DisplayInit=False)
        self.menu.Items.append(self.ChangeAddressMenuItem)
        Device= menu.Display.Bus.Devices[self.Address]
        if Device:
            if Device.Ident=='spi_bigrelay':
                self.menu.Items.append(MenuItem('Test Relays', TestRelay(self.Address)))
        self.menu.Items.append(MenuItem('Serial : '+ str(BitWizardBase(self.menu.Display.Bus,self.Address).Serial()),DisplayInit=False)) 

        self.menu.Show()

class ScanBus():
    def __init__(self):
        pass

    def Show(self,menu):
        menu.Display.Print("Scanning SPI Bus")
        menu.Display.Bus.scan()
        submenu = Menu(menu.Display,[])
        for A in sorted(menu.Display.Bus.Devices.iterkeys()):
            submenu.Items.append(MenuItem(hex(A)[2:]+" " +menu.Display.Bus.Devices[A].Ident,Config(A,submenu)))
        submenu.Show()               
        



lcd = RPi_Ui_20x4(SPI())
lcd.SetPinConfig(1,MCP9700)

lcd.ExtTemp=lcd.Pins[1]
lcd.Contrast(64)


Submenu = Menu(lcd,[MenuItem('Submenu Item 1'),
                    MenuItem('Submenu Item 1')])

menu = Menu(lcd, [MenuItem('Submenu Demo',Submenu),
                  MenuItem('Temperatuur',Temperature()),
                  MenuItem('Potmeter stand',Potmeter),
                  MenuItem('Scan SPI bus', ScanBus())])
menu.Show()
