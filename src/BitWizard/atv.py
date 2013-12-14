from ctypes import c_uint16
import json

class sp5055(object):
    """
    Python object for cummunicating with the sp5055 or compatible PPL
    I2C
    """

    Address = 0xc0
    
    def __init__(self,bus , address = None):
        """
        @param Bus Pass the I2C Bus object
        @param Address The address of the sp5055 on the I2C Bus, default 0xC0
        """
        if address != None:
            self.Address=Address
        self.Bus= Bus

    def SetFrequency(self,frequency):
        """
        Set the frequency for the PLL in MHZ (float), in steps of 125Khz
        ie: sp5055Object.SetFrequency(1240.125)
        """
        f = c_uint16(int(frequency*8))
        self.Bus.Transaction(chr(self.Address)+chr(0)+chr(f.value & 0xFF)+chr(f.value>>8)+chr(0b11111110))

class fms6501a(object):
    Address= 0x86
    _inputs=12
    _outputs=9
    Gain6db=0x00
    Gain7db=0x20
    Gain8db=0x40
    Gain9db=0x60
    InputClamp = 0
    InputBias = 1

    def SafeDefaults(self,filename='MatrixDefaults.json'):
        Defaults={}
        Defaults['inputs']=[]
        Defaults['outputs']=[]
        for i in self.Input:
            Defaults['inputs'].append({'Input':i,
                                       'Clamp':self.Input[i].ClampBit})
        for i in self.Output:
            Defaults['outputs'].append({'Output':i,
                                        'Enable':self.Output[i]._Enable,
                                        'Gain': self.Output[i]._Gain,
                                        'Source' :self.Output[i]._Source})
        f = open(filename,'w')
        json.dump(Defaults,f)
        f.close()

    def LoadDefaults(self,filename='MatrixDefaults.json'):
        try:
            f=open(filename,'r')
            Defaults=json.load(f)
            f.close()
            Loaded=True
        except:
            Loaded=False
        if Loaded:
            for i in Defaults['inputs']:
                self.Input[i['Input']].SetClamp(i['Clamp'])
            for i in Defaults['outputs']:
                self.Output[i['Output']]._Enable = i['Enable']
                self.Output[i['Output']]._Gain = i['Gain']
                self.Output[i['Output']]._Source = i['Source']
                self.Output[i['Output']]._Update()

    
    class _Input(object):
        def __init__(self, Pin, parent):
            self.Pin = Pin
            self.ClampBit=0
            self.Parent=parent

        def SetClamp(self, Clamp):
            data=0
            if self.Pin > 8:
                self.ClampBit= 2**(self.Pin-9) * Clamp
                for inp in range(9,13):
                    data+=self.Parent.Input[inp].ClampBit
                register = 0x1E
            else:
                self.ClampBit= 2**(self.Pin-1) * Clamp
                for inp in range(1,9):
                    data+=self.Parent.Input[inp].ClampBit
                register= 0x1D
            self.Parent.Bus.Write_uInt8(self.Parent.Address, register, data)
                        
    class _Output(object):

        def __init__(self, Out, parent, Enable=False, Gain=0x00, Source=1):
            self.Register = Out        
            self._Enable = Enable
            self._Gain = Gain
            self._Source=Source
            self.Parent=parent

        def _Update(self):
            out=0
            if self._Enable:
                out+=128
            out+=self._Gain
            self.Parent.Bus.Write_uInt8(self.Parent.Address, self.Register ,out+self._Source)

        def Enable(self):
            self._Enable=True
            self._Update()

        def Disable(self):
            self._Enable=False
            self._Update()

        def Gain(self,Gain):
            self._Gain=Gain
            self._Update()

        def Source(self, Source):
            self._Source=Source
            self._Update()
                        
    def __init__(self,Bus,address=None):
        self.Bus=Bus
        if self.Address==None:
            self.Address=address
        self.Output={}
        self.Input={}
        for i in range(1,self._outputs+1):
            self.Output[i]=self._Output(i, self)
        for i in range(1,self._inputs+1):
            self.Input[i]=self._Input(i, self)
        self.LoadDefaults()

if __name__ == "__main__":
    from BitWizard.bw import I2C
    matrix=fms6501a(I2C())
    matrix.Input[2].SetClamp(1)
    matrix.Output[1].Source(7)
    matrix.Output[1].Enable()
    matrix.Output[1].Gain(fms6501a.Gain8db)

