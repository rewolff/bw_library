
"""
@mainpage BitWizardLib introduction
@section Introduction
BitWizardLib is an Objective python library which interconnects python to I2C and/or SPI devices
produced by Bitwizard.

It can also be used to control devices on the busses over TCP/IP. By that you are able to run and or develop programs on computers not equipped with I2C/SPI busses.
@section Installation
After you have unpacked the dristribution .zip or .tgz the library is easily installed with: python setup.py install
@section Getting started
After installation you are ready to get going, see the example section of this documentation.

@example clock.py
@example menu.py
@example daemon.py
"""

from spi_ctypes import *
from ctypes import *

import struct
import time
from fcntl import ioctl,fcntl
import posix
from time import sleep
import socket
import threading

# Try to import SMBus, module is NOT needed if I2C is not used
try:
    from smbus import SMBus
except:
    pass

# Constants for BitWizzard Functions

Print       = 0x00
Ident       = 0x01
Serial      = 0x02

Contrast    = 0x12
Backlight   = 0x13
InitLcd     = 0x14

class _ATTiny():
    ADCChannelConfig = {0:0x07,1:0x03,3:0x2,4:0x01,6:0x00}
    AddFor1V1 = 0x80

class _ATMega():
    ADCChannelConfig = {0:0x47,1:0x46}
    AddFor1V1 = 0x80
#
# NETPnp is under construction and not functional (yet)
#
class NETPnp(object):
    Port = None
    UDPSocket=None
    
    def __init__(self,Port=50000):
        self.Port=Port
        self.UDPServer = threading.Thread(target= self.ScanListener)
        self.UDPServer.start()
        
    def ScanListener(self):
        self.UDPSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.UDPSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.UDPSocket.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
        self.UDPSocket.bind(('',self.Port))
        while True:
            Message,Address = self.UDPSocket.recvfrom(1024)
            print Address, Message
            if Message == 'BitWizardNet':
                pass
            self.UDPSocket.sendto('BWNET',Address)

    def scan(self):
        Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        Socket.bind(('', 0))
        Socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        Socket.sendto("BitWizardNet",('<broadcast>',50000))
        
        m,a = Socket.recvfrom(1000)
        print m,a


class NET(object):
    """
    This class is used as a base clase for both I2C and SPI busses. It makes it possible to run an BitWizardLib based application on a computer with no I2C or SPI bus directly connected to it.
    If you want to use this functionality, see the I2C or SPI bus Documentation.
    @brief Baseclass for extending I2C and SPI busses over TCP/IP.
    """
    Port = 50000
    Server=None
    Socket=None
    TCPServer = None
    
    def _NetTransaction(self,OutBuffer,read=0):
        buf='  '
        if self.Socket == None:
            self.NetInit()
        if self.Socket != None:
            bsend = self.Socket.send(struct.pack('H',read)+OutBuffer)
            if bsend == len(OutBuffer)+2:
                buf =self.Socket.recv(100)
            self.Socket.close()
            self.Socket=None
        return 0,buf
                
    def RequestHandler(self,Socket):
        OutBuffer=Socket.recv(100)
        r,b = self.Transaction(OutBuffer[2:],struct.unpack('H',OutBuffer[0:2])[0])
        Socket.send(b)

    def NetInit(self):
        self.Socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.Socket.connect((self.Server,self.Port))
        
    def ListenerTread(self):
        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.Socket.bind((socket.gethostname(),self.Port))
        self.Socket.listen(5)
        while 1:
            C, A = self.Socket.accept()
            self.TCPServer = threading.Thread(target = self.RequestHandler, args=(C,))
            self.TCPServer.start()

    def __del__(self):
        if self.TCPServer != None:
            self.TCPServer = None
        if self.Socket != None:
            self.Socket.close()


class _Bus(object):
    
    def Read_Int8(self,Address,Register):
        """
        @brief Read a signed Int8 
        @param Address The address of the device
        @param Register the register to read from
        @retval Read_Int8 signed 8 bit integer
        """
        return struct.unpack('b',self.Transaction(chr(Address+1)+chr(Register),3)[1][2])[0]

    def Write_Int8(self,Address,Register,Int8):
        """
        @brief Write a signed Int8
        @param Address The address of the device
        @param Register The register to write to
        @param Int8 Data to write
        """
        self.Transaction(chr(Address)+chr(Register)+struct.pack('b',Int8))

    def Read_uInt8(self,Address,Register):
        """
        @brief Read a single uInt8 (byte)
        @param Address Byte: The address of the device
        @param Register Byte: The register to read from
        @retval Read_uInt8 Unsigned 8 bit integer
        """
        return struct.unpack('B',self.Transaction(chr(Address+1)+chr(Register),3)[1][2])[0]

    def Write_uInt8(self,Address,Register,uInt8):
        """
        @brief Write a unsigned Int8
        @param Address The address of the device
        @param Register The register to write to
        @param Int8 Data to write
        """
        self.Transaction(chr(Address)+chr(Register)+struct.pack('B',uInt8))

    def Read_uInt8s(self,Address,Register,Number=0):
        """
        @brief Read an List of uInt8 (byte)
        @param Address The address of the device
        @param Register The register to read from
        @param Number The amount of byes to read, if 0 or not set, an unexpected length is received
        @retval Read_uInt8s list of Unsigned 8 bit integers
        @todo: Not implemented yet
        """
        pass
    

    
    def Write_uInt8s(self,Address,Register,*Bytes):
        """
        @brief Write an List of uInt8 (byte)
        @param Address The address of the device
        @param Register The register to write to
        @param Bytes any number of uInt8 parameters to send
        """

        self.Transaction(chr(Address)+chr(Register)+''.join([chr(b) for b in Bytes])) 

    def Read_uInt16(self,Address,Register):
        """
        @brief Read a unsigned Int16 
        @param Address The address of the device
        @param Register the register to read from
        @retval Read_uInt16 Unsigned 16 bit integer
        """
        return struct.unpack('H',self.Transaction(chr(Address+1)+chr(Register),6)[1][2:4])[0]

    def Write_uInt16(self,Address,Register,uInt16):
        """
        @brief Write a unsigned Int16
        @param Address The address of the device
        @param Register The register to write to
        @param uInt16 Data to write
        """
        self.Transaction(chr(Address)+chr(Register)+struct.pack('H',uInt16))

    def Read_uInt16s(self,Address,Register,Number):
        """
        @brief Read an List of uInt16 (byte)
        @param Address The address of the device
        @param Register The register to read from
        @param Number The amount of uInt to read, if 0 or not set, an unexpected length is received
        @retval Read_uInt16s list of Unsigned 8 bit integers
        @todo: Not implemented yet
        """
        pass

    def Write_uInt16s(self,Address,Register,*Word):
        """
        @brief Write an List of uInt16
        @param Address The address of the device
        @param Register The register to write to
        @param Bytes any number of uInt16 parameters to send
        @todo: Not implemented yet
        """

        pass
                             
    def Read_Int32(self,Address,Register):
        """
        @brief Read a signed Int32 
        @param Address The address of the device
        @param Register the register to read from
        @retval Read_Int32 signed 32 bit integer
        """
        return struct.unpack('i',self.Transaction(chr(Address+1)+chr(Register),6)[1][2:6])[0]

    def Write_Int32(self,Address,Register,Int32):
        """
        @brief Write a signed Int32
        @param Address The address of the device
        @param Register The register to write to
        @param Int32 Data to write
        """
        self.Transaction(chr(Address)+chr(Register)+struct.pack('i',Int32))

    def Read_uInt32(self,Address,Register):
        """
        @brief Read a unsigned Int32 
        @param Address The address of the device
        @param Register the register to read from
        @retval Read_uInt32 Unsigned 32 bit integer
        """
        return struct.unpack('I',self.Transaction(chr(Address+1)+chr(Register),6)[1][2:6])[0]

    def Write_uInt32(self,Address,Register,uInt32):
        """
        @brief Write a unsigned Int32
        @param Address The address of the device
        @param Register The register to write to
        @param uInt32 Data to write
        """
        self.Transaction(chr(Address)+chr(Register)+struct.pack('I',uIt32))

    def Read32s(self,Address,Register,Number):
        pass

    def Write32s(self,Address,Register, *Long):
        pass

    def Read_String(self,Address,Register,MaxLen=0x20):
        """
        @brief Read a string
        @param Address The address of the device
        @param Register The register to read from
        @param MaxLen Maximum length of string to receive (it handles '0' terminated strings)
        @retval Read_String String
        """
        ret,rxbuf = self.Transaction(chr(Address+1)+chr(Register),MaxLen)
        return string_at(addressof(rxbuf)+2)    

    def Write_String(self,Address,Register,String,MaxLen=0x20):
        """
        @brief Write a string
        @param Address The address of the device
        @param Register The register to write to
        @param String The String to write
        @param MaxLen Maximum length of string to send
        """
        if len(String)>MaxLen:
           String=String[0:20]                  
        self.Transaction(chr(Address)+chr(Register)+String)
                             
        
class I2C(_Bus,NET):
    "Class representing a I2C bus, locally or over TCP/IP. Use an Instance of this class as the bus parameter for any board"
    Devices = {}
    DeviceList= {}
    class Device():
        """class respresening a device connected to the bus,
        instances are created automatically"""
        def __init__(self,address,InUseBy=None,Bus = None,Ident=''):
            """address = int (0x00-0xFF), address of this device
            Ident   = The Identification of the device for scan matching, default:''
            InUseBy = If an Instance of a device-class is created, InUseBy points to that Instance"""
            self.Ident = Ident
            self.InUseBy = InUseBy
            VersionStrip =Ident.split(' ')[0].lower()
            if Ident !='' and VersionStrip in I2C.DeviceList:
                self.InUseBy = I2C.DeviceList[VersionStrip](Bus,address)
            else:
                self.Type=None
            if self.InUseBy!=None:
                self.InUseBy.Ident=VersionStrip

    def __init__(self,device=0,Port=None,Server=None):
        """
        @param device The I2C bus to use e.g. /dev/i2c-0, /dev/i2c-1 etc.
        @param Port Default=None if set to an Integer this will be the TCP/IP port to listen on.
        @param Server Default=None if set to a string e.g. '192.168.200.137' the bus listening on that address/port combination will be connected to.
        @todo Ckeck for Raspberry Pi, and its version in /Proc/CPUInfo

        If you Init an I2CBus like s = I2C(1,Port=50000) it wil listen to connections from a remote bw_library
        on any other computer a bw_library installation can make use of tcp communications like the I2C bus is connected to the local machine.

        Netbus = SPI(Server= '192.168.200.1',port=50000)
        In this case the device parameter is ignored.
        """
        self.Port = Port
        self.Server=Server
        if self.Server != None:  # TCP Client mode
            self.NetInit()
            self.Transaction=self._NetTransaction
        else:
            try:
                self.I2cBus = SMBus(device)
            except :
                print 'Need python-smbus for I2C bus to work'
                print ''
                print 'To install: sudo apt-get install python-smbus'
                return None
            if self.Port != None: #TCP Server Mode
                self.ServerThread = threading.Thread(target=self.ListenerTread)
                self.ServerThread.start()

    def Close(self):
        self.I2cBus.close()

    def Transaction(self, OutBuffer,read=0):
        if read!=0:
            try:
                return 0,'  '+''.join([chr(m) for m in self.I2cBus.read_i2c_block_data((ord(OutBuffer[0])>>1),ord(OutBuffer[1]))])
            except IOError:
                return 0,"  "
        else:
            self.I2cBus.write_i2c_block_data(ord(OutBuffer[0])>>1  ,ord(OutBuffer[1]), [ord(m) for m in OutBuffer[2:]])           
            return 0,None

    #
    # TODO: change Transaction to _Bus.Read_String
    #
    def scan(self,Display=None,line=0):
        for i in range(0x00,0xFF,0x02):
            ret, buf = self.Transaction(chr(i)+chr(Ident),0x20)

            Identification =""
            for c in buf[2:]:
                if ord(c)==0: break
                if ord(c) in range(32,127):
                    Identification +=c

            if Identification != "":
                if i in self.Devices:
                    self.Devices[i].Ident=Identification
                else:
                    self.Devices[i]=I2C.Device(i,Ident=Identification,Bus=self)
            if Display!=None:
                ProgressBar(i,minval=0, maxval=0xFF , Display = Display, y=line)
                sleep(.05)

    def AddDevice(self,Address, InUseBy):
        self.Devices[Address]=I2C.Device(Address,InUseBy=InUseBy,Bus=self)




class SPI(_Bus,NET):
    """class respresenting an SPI Bus"""
    ReadSpeed = 50000
    WriteSpeed = 100000
    Devices = {}
    DeviceList={}
    class Device():
        """class respresening a device connected to the bus,
        instances are created automatically"""
        def __init__(self,address,InUseBy=None,Bus = None,Ident=''):
            """address = int (0x00-0xFF), address of this device
            Ident   = The Identification of the device for scan matching, default:''
            InUseBy = If an Instance of a device-class is created, InUseBy points to that Instance"""
            self.Ident = Ident
            self.InUseBy = InUseBy
            VersionStrip =Ident.split(' ')[0].lower()
            if Ident !='' and VersionStrip in SPI.DeviceList:
                self.InUseBy = SPI.DeviceList[VersionStrip](Bus,address)
            else:
                self.Type=None
            if self.InUseBy!=None:
                self.Ident=VersionStrip
    
    def __init__(self, device = '/dev/spidev0.0', delay = 40, speed = 200000, bits = 8,Port=None,Server=None):
        """
        @param device Any SPI-Bus device in /dev, default /dev/spidev0.0
        @param delay SPI Bus delay between transactions in ms, default 0
        @param speed Set the Bus Speed (Obsolete)
        @param bits Number of bits in a data word, default = 8
        @param Port Default=None if set to an Integer this will be the TCP/IP port to listen on.
        @param Server Default=None if set to a string e.g. '192.168.200.137' the bus listening on that address/port combination will be connected to.

        If you Init an SPIBus like s = SPI(Port=50000) it wil listen to connections from a remote bw_library
        on any other computer a bw_library installation can make use of tcp communications like the SPI bus is connected to the local machine.

        Netbus = SPI(Server= '192.168.200.1',port=50000)
        In this case the device parameter is ignored.
        """
        self.Port = Port
        self.Server=Server
        if self.Server != None:
            self.Transaction=self._NetTransaction
        else:
            if self.Port != None: # Init Server Thread
                self.ServerThread = threading.Thread(target=self.ListenerTread)
                self.ServerThread.start()
            self.Bits = c_uint8(bits)
            self.Speed = self.WriteSpeed
            self.Delay = c_uint16(delay)
            self.Device = device
            self.File = posix.open(self.Device, posix.O_RDWR)
            self.SetBits()
            self.SetSpeed()
        
    def Close(self):
        """
        Close the filehandle to this bus
        """ 
        posix.close(self.File)

    def Transaction(self,OutBuffer, read = 0):
        """
        Do a SPI Transaction
        @param OutBuffer mandatory String, containing chr(Address)+chr(Command)+chr(databyte 1)+....
        @param read Number of bytes to read from the SPI device

        There would be no need to call this method as normally Read/Write methods would be called.
        """
        ReceiveBuffer = create_string_buffer(chr(0) * 0x80)
        TransmitBuffer= create_string_buffer(OutBuffer)
        Transaction = spi_ioc_transfer()
        Transaction.speed_hz = c_uint32(self.Speed)
        Transaction.tx_buf=addressof(TransmitBuffer)
        Transaction.rx_buf=addressof(ReceiveBuffer)
        Transaction.delay_usecs = self.Delay
        if read > 0 and self.Speed!= self.ReadSpeed:   # Slow down speed for reading
            Transaction.speed_hz = self.ReadSpeed
        elif read==0 and self.Speed!=self.WriteSpeed:
            Transaction.speed_hz = self.WriteSpeed
        if self.Speed != Transaction.speed_hz:
            self.Speed = Transaction.speed_hz
            self.SetSpeed()
        if read > len(OutBuffer):
            Transaction.len=read
        else:
            Transaction.len= len(OutBuffer)
        Transaction.bits_per_word = self.Bits
        Transaction.cs_change = 0
        Transaction.pad = 0
        print type(addressof(Transaction))
        ret = ioctl(self.File,SPI_IOC_MESSAGE(1), addressof(Transaction))
        return ret, ReceiveBuffer

    def SetBits(self):
        ret = ioctl(self.File, SPI_IOC_WR_BITS_PER_WORD, self.Bits);
        if ret == -1:
            print "can't set bits per word"

#    def GetBits(self):
#        ret = ioctl(self.File, SPI_IOC_RD_BITS_PER_WORD, addressof(self.Bits));
#        if ret == -1:
#            print "can't get bits per word"

    def SetSpeed(self):
#        ret = ioctl(self.File, SPI_IOC_WR_MAX_SPEED_HZ, addressof(self.Speed));
        ret = ioctl(self.File, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack('I',self.Speed));
        if ret == -1:
            print "can't set max speed hz"

#    def GetSpeed(self):
#        ret = ioctl(lcd, SPI_IOC_RD_MAX_SPEED_HZ, addressof(self.Speed));
#        if ret == -1:
#            print "can't get max speed hz"


    #
    # TODO: change Transaction to _Bus.Read_String
    #
    def scan(self,Display=None,line=0):
        for i in range(0x00,0xFF,0x02):
            ret, buf = self.Transaction(chr(i+1)+chr(0x01),0x20)
            Identification =""
            for c in buf[2:]:
                if ord(c)==0: break
                if ord(c) in range(32,127):
                    Identification +=c
            if Identification != "":
                if i in self.Devices:
                    self.Devices[i].Ident=Identification.split(" ")[0].lower()
                else:
                    self.Devices[i]=SPI.Device(i,Ident=Identification,Bus=self)
            if Display!=None:
                ProgressBar(i,minval=0, maxval=0xFF , Display = Display, y=line)
                sleep(.05)

    def AddDevice(self,Address, InUseBy):
        self.Devices[Address]=SPI.Device(Address,InUseBy,Bus=self)
# -----------------------------------------------------------------------------
        
class BitWizardBase(object):
    DefaultAddress = 0x00
    
    def __init__(self, bus , address = None):
        if address == None:
            self.Address = self.DefaultAddress
        else:
            self.Address = address
        self.Bus = bus
        if self.Address in self.Bus.Devices:
            self.Bus.Devices[self.Address].InuseBy=self
        else:
            self.Bus.AddDevice(self.Address,InUseBy=self)

    # Return the Identification String of this Board
    def Ident(self):
        """
        @brief returns the Identification string of this board
        @retval Ident String
        """
        return self.Bus.Read_String(self.Address,Ident)

    # Retrun the Serial Number of this Board
    # TODO: use _NET method
    def Serial(self):
        """
        @brief returns the Serial Number of this board
        @retval Serial Long
        """
        ret,buf= self.Bus.Transaction(chr(self.Address+1)+chr(Serial),0x06)
        return struct.unpack(">L", buf[2:6])[0] 

    # Change the Address of this board, this can be done realtime and after calling this method
    # the objects instance will continue to communicate using the new address.
    def ChangeAddress(self, newaddress=None):
        """
        @brief change the address of the board, It will update all internal addressing so the object will continue to work after changing.
        @param newaddress when set it will change to that address, if not It will retrun the board to it's default address.
        """
        if newaddress == None:
            newaddress = self.DefaultAddress
        if self.Address != newaddress:            
            self.Bus.Write_uInt8(self.Address,0xF1,0x55)
            self.Bus.Write_UInt8(self.Address,0xF2,0xAA)
            self.Bus.Write_uInt8(self.Address,0xF0,nwewaddress)
            self.Bus.Devices[newaddress]=self.Bus.Devices[self.Address]
            del self.Bus.Devices[self.Address]
            self.Address = newaddress
        

class BitWizardLcd(BitWizardBase):
    DefaultAddress = 0x82
    Cursor = "Off" #Blink, On

    # Set cursor to Position
    # x = position >= 0
    # y = line >=0
    def SetCursor(self,x,y):
        """
        @brief Set Cursor position
        """
        self.Bus.Write_uInt8(self.Address,0x11,32*y+x)

    def Cls(self):
        """
        @brief Clear screen of LCD and reset the cursor to 0,0
        """
        self.Bus.Write_uInt8(self.Address,0x10,0x00)

    def Print(self,text = ""):
        """
        @brief Print text on the current cursor position
        """
        self.Bus.Write_String(self.Address,0x00, text)


    def PrintAt(self,x=0,y=0,text=''):
        """
        @brief Print text on the given x/y position
        """
        self.SetCursor(x,y)
        self.Print(text)

    # Set the Contrast of the LCD
    def Contrast(self, value=128):
        """
        @brief Change LCD contrast, defaults to 128
        """
        self.Bus.Write_uInt8(self.Address,Contrast,value)

    # Set the BackLight of the LCD
    def Backlight(self, value = 128):
        """
        @brief Change the intensity of the backlight, Defaults to 128
        """
        self.Bus.Write_uInt8(self.Address,Backlight,value)

    # Initialize the LCD Controller
    def Init(self):
        self.Bus.Write_uInt8(self.Address,InitLcd,value)

    # Send Command to LCD Controller
    def LcdCmd(self,cmd):
        self.Bus.Write_uInt8(self.Address,0x01,0x00)

    # Set Cursor Visible and make it blink or not
    def Cursor(self,on=True,blink=False):
        """
        @brief Show the cursor and/or set it to blink
        """
        value = 8+4
        if on and blink:
            value+=1
        elif on and not blink:
            value+=2
        self.Bus.Write_uInt8(self.Address,0x01,value)

    # Set Cursor to the home position (0,0)
    
    def CursorHome(self):
        """
        @brief Move the cursor to 0,0 or HOME position
        """
        self.Bus.Write_uInt8(self.Address, 0x01, 0x02)
            
    def DefineChar(self,char, Data=[0,0,0,0,0,0,0,0]):
        """Define a charachter
        @todo: This does NOT work (yet) and is for BitWizard.ui.ProgressBar
        @todo: Change to make it functional"""
        self.Bus.Transaction(chr(self.Address)+chr(0x01)+chr(0x40))
        self.Bus.Transaction(chr(self.Address)+chr(0x00)+chr(0x00)+chr(0x00)+chr(0x00)+chr(0x00)+chr(0x00)+chr(0x00)+chr(0x00)+chr(0x00))
        self.Bus.Transaction(chr(self.Address)+chr(0x01)+chr(0x48))
        self.Bus.Transaction(chr(self.Address)+chr(0x00)+chr(0x10)+chr(0x10)+chr(0x10)+chr(0x10)+chr(0x10)+chr(0x10)+chr(0x10)+chr(0x10))
        self.Bus.Transaction(chr(self.Address)+chr(0x01)+chr(0x50))
        self.Bus.Transaction(chr(self.Address)+chr(0x00)+chr(0x18)+chr(0x18)+chr(0x18)+chr(0x18)+chr(0x18)+chr(0x18)+chr(0x18)+chr(0x18))
        self.Bus.Transaction(chr(self.Address)+chr(0x01)+chr(0x58))
        self.Bus.Transaction(chr(self.Address)+chr(0x00)+chr(0x1C)+chr(0x1C)+chr(0x1C)+chr(0x1C)+chr(0x1C)+chr(0x1C)+chr(0x1C)+chr(0x1C))
        self.Bus.Transaction(chr(self.Address)+chr(0x01)+chr(0x60))
        self.Bus.Transaction(chr(self.Address)+chr(0x00)+chr(0x1E)+chr(0x1E)+chr(0x1E)+chr(0x1E)+chr(0x1E)+chr(0x1E)+chr(0x1E)+chr(0x1E))
        self.Bus.Transaction(chr(self.Address)+chr(0x01)+chr(0x68))
        self.Bus.Transaction(chr(self.Address)+chr(0x00)+chr(0x1F)+chr(0x1F)+chr(0x1F)+chr(0x1F)+chr(0x1F)+chr(0x1F)+chr(0x1F)+chr(0x1F))
        
    def DisplayMode(self, cursormove=True,displayshift=False):
        """
        Change the Display mode of the LCD
        @todo: Does not work, Investigate odd behaviour of LCD                                
        """
        value=16
        if cursormove:
            value+=4
        elif displayshift:
            value+=4
        self.Bus.Write_uInt8(self.Address,0x01,value)

class BitWizardPushButtons(BitWizardBase):
    """
    Base class for pushbutton devices like the Pushbutton or RPi_Ui boards. There is no need to create an instance of this class. If used as a base for another class, overWrite PushButtons to the actual number
    """
    PushButtons = 0
    def ReadAll(self):
        """
        Read All buttons for them being pressed right now.
        @retval an array of length self.PushButtons with boolean values, True when being pressed
        """
        v =self.Bus.Read_uInt8(self.Address,0x10)
        Buttons = []
        for i in range(0,self.PushButtons):
            Buttons.append(v & 2**i == 2**i)
        return Buttons

    def ReadOne(self,button):
        """
        Check One button to see if it is pressed or not.
        @param button Int:= Buttonnumber >=0 < self.PushButtons
        @retval True if the button is being Pressed
        """
        return bool(self.Bus.Read_uInt8(self.Address, 0x40+button))

    def ReadOneInv(self,button):
        """
        Read the Status of one butten, like ReadOne
        @retval Boolean, is equal to: not self.ReadOne(button)
        """
        return bool(self.Bus.Read_uInt8(self.Address, 0x20+button))

    def ReportPressed(self):
        """
        Report if any button has been pressed since this method was last called. Will reset the register
        you can use this in a loop, be shure to flush the register beforehand by calling this once.
        If you keep a button pushed, it will read out ans True multiple times.
        @retval an array of length self.PushButtons with boolean values, True if that button has been pressed
        """
        v =self.Bus.Read_uInt8(self.Address,0x30)
        Buttons = []
        for i in range(0,self.PushButtons):
            Buttons.append(v & 2**i == 2**i)
        return Buttons
    
    def ReportPressedOnce(self):
        """
        Report if any button has been pressed since this method was last called. Will reset the register
        you can use this in a loop, be shure to flush the register beforehand by calling this once.
        @retval an array of length self.PushButtons with boolean values, True if that button has been pressed
        If you keep a button pushed, it will read out as 1 only once.
        """
        v =self.Bus.Read_uInt8(self.Address,0x31)
        Buttons = []
        for i in range(0,self.PushButtons):
            Buttons.append(v & 2**i == 2**i)
        return Buttons


class IOPin():
    """
    Base class for implementing basic interfaces to IOPins on BitWizard Boards.
    Use of this object is Internal to this library.
    """
    IO=0
    def __init__(self,Pin, parent):
        self.Pin=Pin
        self.Bus=parent.Bus
        self.Address = parent.Address
        self.IODevice=parent.IODevice
        if parent.PinConfig.has_key(Pin):
            if parent.PinConfig[Pin].has_key('property'):
                setattr(parent,parent.PinConfig[Pin]['property'],self)

    def PinMask(self):
        return (2**self.Pin) * self.IO


class DigitalIn(IOPin):
    """
    @brief Base class for communicating Digital Input Pins 
    """
    def __init__(self,Pin,parent):
        IOPin.__init__(self,Pin,parent)
        
    def Get(self):
        """
        Get the current state of this pin.
        @retval Boolean, True for Input High, False for Input Low
        """
        return bool(self.Bus.Read_uInt8(self.Address, 0x40+self.Pin))        
        
class DigitalOut(IOPin):
    """
    @brief Base class for communicating Digital Output Pins 
    """
    IO=1
    def __init__(self,Pin,parent):
        IOPin.__init__(self,Pin,parent)

    def Set(self,value):
        """
        Set the Output value of this pin
        @param value Boolean: True for On/False for off
        """
        if value:
            onoff = 0x01
        else:
            onoff = 0x00
        self.Bus.Write_uInt8(self.Address,0x20+self.Pin, onoff)

    def Get(self):
        """
        Get the current state of this pin.
        @todo: implement (now just returns False)
        @retval Boolean True for Input High, False for Input Low
        """
        value=False
        return value


class AnalogIn(IOPin):
    """
    @brief Base class for communicating Analog Input Pins 
    """
    ADChannel = None
    Vref = 5
    def __init__(self,Pin,parent):
        IOPin.__init__(self,Pin,parent)
        if parent.PinConfig.has_key(self.Pin):
            if parent.PinConfig[self.Pin].has_key("vref"):
                #print "Vref found"
                self.Vref = parent.PinConfig[self.Pin]["vref"]
        self.ADDevice  = parent
        self.ADChannel = self.ADDevice.ADCChannels
        self.ADDevice.ADCChannels+=1
        self.Config()

    def Config(self):
        CConfig = self.IODevice.ADCChannelConfig[self.Pin]
        if self.Vref ==1:
            CConfig += self.IODevice.AddFor1V1 
        self.Bus.Write_uInt8(self.Address,0x70+self.ADChannel,CConfig)
        
    def Get(self):        
        """
        Sample the value according to this Boards Samples/Bitshift config
        @retval 16 bit value (0..65535)
        """
        return self.Bus.Read_uInt16(self.Address,0x68+self.Pin)
    
    def GetSample(self):        
        """
        take one Sample without the Boards Bitshift Config
        @retval 10 bit value (0..1023)
        """
        return self.Bus.Read_uInt16(self.Address,0x60+self.Pin)

    def __del__(self):
        self.ADDevice.ADCChannels-=1

class MCP9700(AnalogIn):
    """
    @brief class representing an MCP9700 temperature Sensor to an AnalogIn IOPin
    """
    VoltPerDegree = 0.010
    RefVoltage = 1.1000
    Vref=1    

    def GetCelcius(self):
        """
        @retval Current Temperature value as float in Degree Celcius
        """
        ADCMax = (self.ADDevice.ADSamples * 1023) /(2**self.ADDevice.ADBitshift)
        sample=self.Get()
        R = self.RefVoltage / ADCMax
        Volt = sample*R-.5        
        return Volt/self.VoltPerDegree

    def GetKelvin(self):
        """
        @retval Current Temperature value as float in Degree Kelvin
        """
        return self.GetCelcius() + 273.15

    def GetFahrenheit(self):
        """
        @retval Current Temperature value as float in Degree Fahrenheit
        """
        return self.GetCelcius()*1.8+32
        

class PWMOut(IOPin):
    """
    @brief class representing an IOPin used for PWM output
    """
    def Set(self,value):
        """
        Set the PWM output value
        @param value Byte: the value
        """
        self.Bus.Write_uInt8(self.Address,0x50+self.Pin,value)        

    def Get(self):
        """
        Get the current value of this pin.
        @todo: implement (now just retruns 0)
        @retval Int 0-255
        """
        value=0
        return value


class IOPinBase():
    """
    Class For BitWizard boards with Digital/Analog IO, On board Temperature sensors etc. Use this as a baseclass for creating new board classes only.
    It is part of the automatic reconfiguration code. Classed using this as a baseclass can override PinConfig, ADSamples and ADBitshift. and calls to SetPinConfig and InitAnalog might be usefull and can be done in realtime.
    @brief class for BitWizzard boards with IOPins.
    """
    IODevice=_ATTiny
    PinConfig = {}
    IOPins = 0
    ADCChannels = 0
    ADCChannelConfig = {}
    ADSamples = 4096
    ADBitshift = 6

    def __init__(self):
        self.Pins={}
        for p in range(self.IOPins):
            if self.PinConfig.has_key(p):
                self.Pins[p]=self.PinConfig[p]["device"](p,self)
            else:
                self.Pins[p]= DigitalIn(p,self)
        self.DoPinConfig()
        self.InitAnalog(self.ADSamples,self.ADBitshift)

    def DoPinConfig(self):
        mask = 0
        pwmmask = 0
        for p in range(self.IOPins):
            mask = mask | self.Pins[p].PinMask()
            if isinstance(self.Pins[p],PWMOut):
                pwmmask = pwmmask | 2**p
        self.SetInputOutput(mask,pwmmask)

    def SetPinConfig(self,pin, pintype, **kwargs):
        """
        Set or change the functionality of one IOPin.
        @param pin Int: The Pinnummer on the board to Set/Change.
        @param pintype class: Can be any subclass of IOPin, like DigitalIn, DogitalOut, PWMOut, AnalogIn, MCP9700 etc. 
        @param kwargs list: additional configuration passed to the __init__ when in instance of pintype is created.
        """
        if self.Pins[pin]!=None:
            del self.Pins[pin]
        if self.PinConfig.has_key(pin):
            if self.PinConfig[pin].has_key('property'):
                delattr(self,self.PinConfig[pin]['property'])
            del self.PinConfig[pin]
        if not self.PinConfig.has_key(pin):
            self.PinConfig[pin] = kwargs           
        self.PinConfig[pin]["device"]=pintype
        c = self.ADCChannels
        self.Pins[pin]=pintype(pin,self)
        self.DoPinConfig()
        if c!= self.ADCChannels:
            self.Bus.Write_uInt8(self.Address,0x80,self.ADCChannels)

    def SetInputOutput(self, mask=0x00,pwmmask=0x00):
        self.Bus.Write_uInt8(self.Address,0x30,mask)
        self.Bus.Write_uInt8(self.Address,0x5F,pwmmask)
        
    def InitAnalog(self,ADSamples=None,ADBitshift=None):
        """
        Use this method to change the number of samples and bitshift returned bu the Get function of an analogIn Pin or connected sensor
        @param ADSamples Int: Set the number of samples to add, typically 256,1024,2048,4096 (Default)
        @param ADBitshift Int:
        @see Bitwizard.nl wiki for detailed information 
        """
        if self.ADCChannels > 0:
            if ADSamples!=None:
                self.ADSamples  = ADSamples
            if ADBitshift != None:
                self.ADBitshift = ADBitshift
            self.Bus.Write_uInt16(self.Address,0x81,self.ADSamples)
            self.Bus.Write_uInt16(self.Address,0x81,self.ADSamples)# there was a bug in old firmware, send twice
            self.Bus.Write_uInt8(self.Address,0x82,self.ADBitshift)
            self.Bus.Write_uInt8(self.Address,0x80,self.ADCChannels)
            

class DIO(BitWizardBase,IOPinBase):
    """
    @brief class representing the LCD_DIO board.
    """
    
    PinConfig={}
    IOPins = 7
    DefaultAddress = 0x84

    def __init__(self,bus, Address=None):
        BitWizardBase.__init__(self,bus,Address)
        IOPinBase.__init__(self)

    def SetAllOutputs(self,value=0x00):
        """
        Sets Set All outputs
        @param value Byte: bitmap, pin 0 is LSB 
        """
        self.Bus.Write_uInt8(self.Address,0x10,value)
        
SPI.DeviceList["spi_dio"]= DIO      
I2C.DeviceList["i2c_dio"]= DIO      
    

     

class LCD_16x2(BitWizardLcd):
    """
    @brief class representing the LCD_16x2 board.
    """
    DefaultAddress = 0x82
    Width=16
    Height=2


class LCD_20x4(BitWizardLcd):
    """
    @brief class representing the LCD_20x4 board.
    """
    DefaultAddress = 0x94
    Width=20
    Height=4
SPI.DeviceList["spi_lcd"]= LCD_20x4      
I2C.DeviceList["i2c_lcd"]= LCD_20x4      


class Servo(BitWizardBase):
    """
    @brief class representing the Servo board.
    """
    DefaultAddress= 0x86
    Servos = 7

    def SetPosition(self,servo = 1,position=128):
        self.Bus.Write_uInt8(self.Address,0x19+servo, position)
        
    def GetPosition(self,servo): 
        self.Bus.Read_uInt8(self.Address,0x19+servo)

SPI.DeviceList["spi_servo"]= Servo      
I2C.DeviceList["i2c_servo"]= Servo      


class PushButtons_4(BitWizardPushButtons):
    """
    @brief class representing the 4Pushbutton board.
    @todo Set DefaultAddress to correct value
    """

    #DefaultAddress = 0x00
    PushButtons=4

class Ui_PushButtons(BitWizardPushButtons):
    PushButtons=6

class RPi_Ui_20x4(LCD_20x4,Ui_PushButtons,IOPinBase):
    """
    @brief class representing the RPi_Ui_20x4 board for Raspberry Pi
    """
    IOPins=2
    DefaultAddress = 0x94
    IODevice = _ATMega
    ADSamples = 4096
    ADBitshift = 6
    PinConfig={0:{"device":MCP9700,'property':'IntTemp'},1:{"device":AnalogIn,"vref":1,'property':'ExtAnalog'}}

    def __init__(self,*args,**kwargs):
        BitWizardBase.__init__(self,*args,**kwargs)
        IOPinBase.__init__(self)
    
SPI.DeviceList["spi_rpi_ui"]= RPi_Ui_20x4     
I2C.DeviceList["i2c_rpi_ui"]= RPi_Ui_20x4     

    

class RPi_Ui_16x2(LCD_16x2,Ui_PushButtons, IOPinBase):
    """
    @brief class representing the RPi_Ui_16x2 board for Raspberry Pi.
    """

    DefaultAddress = 0x94
    IOPins=2
    DefaultAddress = 0x94
    IODevice = _ATMega
    ADSamples = 4096
    ADBitshift = 6
    PinConfig={0:{"device":MCP9700,'property':'IntTemp'},1:{"device":AnalogIn,"vref":1,'property':'ExtAnalog'}}

    def __init__(self,*args,**kwargs):
        BitWizardBase.__init__(self,*args,**kwargs)
        IOPinBase.__init__(self)

#SPI.DeviceList["spi_rpi_ui"]= RPi_Ui_16x2     
# Impossible to tell which LCD is connected during .

def SetAutodetectLCD(lcd):
    """
    Since it is impossible to tell which LCD is connected it is impossible
    for the I2C/SPI.scan() method to create the proper instance.
    Pass the proper object reference (Not Instance), ie. LCD_16x2, LCD20x4 before scan is called.

    The system default is 20x4, change to 16x2 with SetAutoDetectLCD(LCD_16x2)
    """
    SPI.DeviceList["spi_lcd"]= lcd     
    I2C.DeviceList["i2c_lcd"]= lcd     
    
def SetAutoDetectUi(Ui):
    """
    Since it is impossible to tell which LCD is connected it is impossible
    for the I2C/SPI.scan() method to create the proper instance.
    Pass the proper object reference(Not instance of), ie. RPi_Ui_16x2, RPi_Ui_20x4 before scan is called.
    
    the system default is 20x4, change to 16x2 with SetAutoDetectUi(RPi_Ui_16x2) 
    """
    SPI.DeviceList["spi_rpi_ui"]= Ui     
    I2C.DeviceList["i2c_rpi_ui"]= Ui     


class LED7Segment(BitWizardBase):
    """
    @brief class representing the SPI_7Segment board.
    @todo: Investigate SetHex4 seems to influence the dots when d3=7 ??!?!?
    """

    DefaultAddress = 0x96

    def SetBitmap4(self,D1=0,D2=0,D3=0,D4=0):
        self.Bus.Write_uInt8s(self.Address,0x10,D1,D2,D3,D4)

    def SetBitmap1(self,char, value=0):
        self.Bus.Write_uInt8(self.Address,0x20+char,value)

    def SetHex4(self,D1=0,D2=0,D3=0,D4=0):
        self.Bus.Write_uInt8s(self.Address,0x11,D1,D2,D3,D4)
        
    def SetHex1(self,char, value=0):
        self.Bus.Write_uInt8(self.Address,0x30+char,value)

    def BottomDot(self,on=True):
        if on:
            value=0x01
        else:
            value=0x00
        self.Bus.Write_uInt8(self.Address,0x40,value)
        
    def UpperDot(self,on=True):
        if on:
            value=0x01
        else:
            value=0x00
        self.Bus.Write_uInt8(self.Address,0x41,value)

    def BothDots(self,on=True):
        if on:
            value=0x01
        else:
            value=0x00
        self.Bus.Write_uInt8(self.Address,0x42,value)


    def GetBitmap4(self,D1=0,D2=0,D3=0,D4=0):
        """@todo: does not work"""
        return self.Bus.Transaction(chr(self.Address)+chr(0x10)+chr(D1))

    def GetBitmap1(self,chart):
        """@todo: does not work"""
        return self.Bus.Transaction(chr(self.Address)+chr(0x19+char))
SPI.DeviceList['spi_7segment']=LED7Segment



class Relay(BitWizardBase,IOPinBase):
    """
    @brief class representing the 2Relay board.
    """

    DefaultAddress = 0x8E
    IOPins = 2
    PinConfig = {0:{'device':DigitalOut},1:{'device':DigitalOut}}

def __init__(self,bus, Address=None):
        BitWizardBase.__init__(self,bus,Address)
        IOPinBase.__init__(self)

SPI.DeviceList["spi_relay"]= Relay      
I2C.DeviceList["i2c_relay"]= Relay      


class BigRelay(BitWizardBase,IOPinBase):
    """
    @brief class representing the BigRelay board.
    """

    DefaultAddress = 0x9E
    IOPins = 6
    PinConfig = {}
    PinConfig[0]={'device':DigitalOut}
    PinConfig[1]={'device':DigitalOut}
    PinConfig[2]={'device':DigitalOut}
    PinConfig[3]={'device':DigitalOut}
    PinConfig[4]={'device':DigitalOut}
    PinConfig[5]={'device':DigitalOut}

    def __init__(self,bus, Address=None):
        BitWizardBase.__init__(self,bus,Address)
        IOPinBase.__init__(self)


SPI.DeviceList["spi_bigrelay"]= BigRelay      
I2C.DeviceList["i2c_bigrelay"]= BigRelay      


class Fet3(BitWizardBase,IOPinBase):
    """
    @brief class representing the 3FET board.
    """

    DefaultAddress = 0x8A
    IOPins = 3
    PinConfig = {}
    PinConfig[0] = {'device':DigitalOut}
    PinConfig[1] = {'device':DigitalOut}
    PinConfig[2] = {'device':DigitalOut}

    def __init__(self,bus, Address=None):
        BitWizardBase.__init__(self,bus,Address)
        IOPinBase.__init__(self)

SPI.DeviceList["spi_3fet"]= Fet3      
I2C.DeviceList["i2c_3fet"]= Fet3      

class StepperMotor:
    """
    
    @brief: class for using the steppermotor functions on 7FET and MOTOR boards.
    @todo: document
    @todo: test with MotorBoard
    @todo: change Bus.Transaction
    """

    class StepperPin(IOPin):
        IO=1

    def StepperInit(self,StepAngle=1.0,Reduction=1.0, North=0, StepDelay=200 ,CurrentPosition=None,Reverse=False):
        self.StepAngle = StepAngle
        self.Reduction = Reduction
        self.Reverse = Reverse
        self.North = North
        for p in range(4):
            self.SetPinConfig(p,StepperMotor.StepperPin)
        self.SetStepDelay(StepDelay)
        print self.GetCurrentPosition()
        if CurrentPosition!=None:
            self.SetCurrentPosition(CurrentPosition)
            
    def DegreeToSteps(self,Degree):
        """
        @brief Function to convert Degree's to steps, used internally
        @param Degree 
        @ retval int the amount of steps to make for the given Degree 
        """
        return int(round(Degree*(self.Reduction/self.StepAngle/2)))

    def StepsToDegree(self,Steps):
        """
        @brief Function to convert steps to Degree's, used internally
        @param Steps
        @ retval int the amount of degrees to make rotated for the given steps 
        """
        return int(round(Steps/(self.Reduction/self.StepAngle/2)))
    
    def SetCurrentPosition(self,pos):
        """
        @brief Set the current position, at startup (power on) the CurrentPosition == 0
        @param Position set the internal Current
        @ retval int the amount of steps to make for the given Degree 
        """

        if self.Reverse: pos*=-1
        self.Bus.Transaction(chr(self.Address)+chr(0x40)+struct.pack('@l',pos))

    def GetCurrentPosition(self):
        r,v = self.Bus.Transaction(chr(self.Address+1)+chr(0x40),0x06)
        if self.Reverse:
           r=-1
        else:
            r=1
        return r*struct.unpack('@l', v[2:6])[0]

    def GetCurrentDegree(self):
        return self.StepsToDegree(self.GetCurrentPosition())

    def SetTargetPosition(self,pos):
        if self.Reverse: pos*=-1
        self.Bus.Transaction(chr(self.Address)+chr(0x41)+struct.pack('@l',pos))

    def GetTargetPosition(self):
        if self.Reverse:
           r=-1
        else:
            r=1
        return r*struct.unpack('@l',z.Bus.Transaction(chr(z.Address+1)+chr(0x41),0x06)[1][2:6])[0]

    def SetTargetDegree(self,Degree):
        self.SetTargetPosition(self.DegreeToSteps(Degree))

    def GetTargetDegree(self):
        return self.StepsToDegree(self.GetTargetPosition())

    def SetRelativePosition(self,pos):
        if self.Reverse: pos*=-1
        self.Bus.Transaction(chr(self.Address)+chr(0x42)+struct.pack('@l',pos))

    def SetRelativeDegree(self,Degree):
        self.SetRelativePosition(self.DegreeToSteps(Degree))

    def SetStepDelay(self,delay=200):
        """
        @brief Set the delay between steps in milliseconds.
        @param delay : Default 200 (5 steps per second).
        """        
        self.Bus.Transaction(chr(self.Address)+chr(0x43)+chr(delay))

    def GetStepDelay(self):
        self.Bus.Transaction(chr(self.Address+1)+Chr(0x43),0x3)


class Fet7(BitWizardBase,IOPinBase,StepperMotor):
    """
    @brief class representing the 7Fet board.
    """
    DefaultAddress = 0x88
    IOPins = 7
    PinConfig={}
    PinConfig[0] = {'device':DigitalOut}
    PinConfig[1] = {'device':DigitalOut}
    PinConfig[2] = {'device':DigitalOut}
    PinConfig[3] = {'device':DigitalOut}
    PinConfig[4] = {'device':DigitalOut}
    PinConfig[5] = {'device':DigitalOut}
    PinConfig[6] = {'device':DigitalOut}

    def __init__(self,bus, Address=None):
        BitWizardBase.__init__(self,bus,Address)
        IOPinBase.__init__(self)

                             
SPI.DeviceList["spi_7fet"]= Fet7      
I2C.DeviceList["i2c_7fet"]= Fet7      


if __name__ == "__main__":
    S=SPI()
    s=Fet7(S)
    s.StepperInit(5.625,64)
    print s.GetCurrentPosition()

    #s.SetCurrentPosition(0)
    s.SetCurrentPosition(360)
    print s.GetCurrentPosition()
    
