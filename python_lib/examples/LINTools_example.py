import ucanlintools.LUC
import threading, time, sys, os
from ucanlintools.LDF_parser import parseLDF
import binascii

rx_count = 0

def rx_any(f):
        global rx_count
        rx_count += 1 

def rx_new_data(f):
        global message
        print (str(rx_count) + " " + hex(f.id) + ": " +(f.data.hex()))
        if (message.id == f.id):
                message.decode(f.data)
                print(message.diff_str())

ldf = parseLDF("D:\\ldfe.ldf")        
message = ldf.get_message_by_name('FRAME_A')


lin = ucanlintools.LUC('COM7')

lin.set_frame_rx_handler(rx_any)
lin.set_new_frame_rx_handler(rx_new_data)

lin.openAsMaster() 

lin.addReceptionFrameToTable(52,8)
lin.addReceptionFrameToTable(54,8)
lin.enable()

input("Press Enter to continue... \r")

lin.disable()
lin.close()
lin.deInitSerial()     

os._exit(1)    
        