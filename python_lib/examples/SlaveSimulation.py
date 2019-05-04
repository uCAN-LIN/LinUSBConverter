import ucanlintools.LUC
import ucanlintools.LDF_parser

from pynput import keyboard
import time

""" LIN Slave simulation, 2 buttons slave + backlight setup. """

key1 = 0
key2 = 0
BacklightLevel = 0

def rx_new_data(f):
    global key1
    global key2
    global BacklightLevel
    # print ("LIN<" + f.data.hex())
    if (f.id == 11):
        bckl = int.from_bytes(f.data, byteorder='little')
        print ("new backlight level " + str(bckl))
        BacklightLevel = f.data[0]
        KeysToFrame(key1,key2)

lin = ucanlintools.LUC('COM7')

lin.set_new_frame_rx_handler(rx_new_data)

lin.openAsSlave() 

lin.addReceptionFrameToTable(11,1)
lin.addTransmitFrameToTable(12,b'0000')

lin.enable()

def KeysToFrame(key1, key2):
    global BacklightLevel
    aa = 0 
    if (key1):
        aa = 1
    if (key2):
        aa += 16
    aa += (BacklightLevel * 256)
    aa = aa.to_bytes(2, byteorder='little')
    # print (aa)
    lin.addTransmitFrameToTable(12,aa)

def on_press(key):
    global key1
    global key2
    try:
        # print('key {0} pressed'.format(key.char))
        if key.char == 'q':
            key1 = 1
            KeysToFrame(key1,key2)
        if key.char == 'w':
            key2 = 1
            KeysToFrame(key1,key2)
    except AttributeError:
        pass

def on_release(key):
    global key1
    global key2

    try:
        # print('{0} released'.format(key))
        if key.char == 'q':
            key1 = 0
            KeysToFrame(key1,key2)
        if key.char == 'w':
            key2 = 0
            KeysToFrame(key1,key2)
        
    except AttributeError:
        if key == keyboard.Key.esc:
            return False


with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
    print("SIM END")

    lin.disable()
    del lin

    print("Deinit done")
    

