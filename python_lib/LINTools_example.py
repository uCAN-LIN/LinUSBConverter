import LUC
import threading, time, sys, os

lin = LUC.LUC('COM7')
lin.close()
lin.openAsMaster() 
lin.disable()

def statusFrameThread():
    global lin
    f52 = 0
    f54 = 0
    while True:
        f = lin.waitForFrame(0)
        
        if (f.id == 54):
                if (f54 != f.data):
                        f54 = f.data
                        print ("54 : " + hex(f54))
        if (f.id == 52):
                if (f52 != f.data):
                        f52 = f.data
                        print ("52 : " + hex(f52))
        
w_tx = threading.Thread(target=statusFrameThread) 
w_tx.start()

lin.addReceptionFrameToTable(52,8)
lin.addReceptionFrameToTable(54,8)
lin.enable()


input("Press Enter to continue...")
lin.disable()
os._exit(1)    
        