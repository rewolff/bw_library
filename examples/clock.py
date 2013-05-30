#!/usr/bin/python
from time import *
from BitWizard.bw import *

c = LED7Segment(SPI())

digit=[0xa,0xa,0xa,0xa]    
    
while True:
    t=strftime('%H%M%S',localtime())
    for d in range(4):
        if t[d]!=digit[d]:
            digit[d]=t[d]
            c.SetHex1(d,int(digit[d]))
    if int(t[4:])%2==0:
        c.BothDots(True)
    else:
        c.BothDots(False)
    sleep(1)
