#!/usr/bin/python

import serial
import sys
import os
import time

print("send boot to serial")
try:
    ser = serial.Serial(sys.argv[1])  # open serial port
    ser.write(b'boot\n\r')     # write a string
    ser.close()             # close port
except:
    print("no serial named " + sys.argv[1])

time.sleep(0.5)

print("write software to DFU")    
os.system('D:\Programy\STMicroelectronics\STM32CubeProgrammer\\bin\STM32_Programmer_CLI.exe -c port=usb1 -e all -d .\TrueSTUDIO\LUCEmbedded\Debug\LUCEmbedded.bin  0x08000000 -v -s')  

