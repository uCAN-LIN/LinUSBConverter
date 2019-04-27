import LUC
import threading, time, sys, os

rx_count = 0

def rx_any(f):
        global rx_count
        rx_count += 1 

def rx_new_data(f):
        print (str(rx_count) + " " + hex(f.id) + ": " + hex(f.data))

lin = LUC.LUC('COM7')

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
        