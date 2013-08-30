#!/usr/bin/python
from time import *
from BitWizard.bw import *
from os import fork
from sys import exit

c = LED7Segment(SPI())

digit=[0xa,0xa,0xa,0xa]    
pid = fork()
if pid!=0:
    exit(0)
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
