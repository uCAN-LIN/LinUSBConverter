import ucanlintools.LUC
import ucanlintools.LDF_parser
from ucanlintools.LDF_parser import parseLDF


from pynput import keyboard
import time

""" LIN Master simulation, 2 buttons slave + backlight setup. + LDF """

ldf = parseLDF("example_LDF.ldf")
master_frame = ldf.get_message_by_name('Backlight')
slave_frame = ldf.get_message_by_name('Buttons_Status')

BacklightLevel = 1

def rx_new_data(f):
    global slave_frame
    if (f.id == slave_frame.id):
        slave_frame.decode(f.data)
        print ("LIN> " + slave_frame.diff_str())

lin = ucanlintools.LUC('COM11')

lin.set_new_frame_rx_handler(rx_new_data)

lin.openAsMaster() 

lin.addReceptionFrameToTable(slave_frame.id,slave_frame.len)
lin.addTransmitFrameToTable(master_frame.id,b'00')

lin.enable()

def DataToFrame():
    global BacklightLevel
    aa = master_frame.encode({'backlight_level': BacklightLevel})
    lin.addTransmitFrameToTable(master_frame.id,aa)
    print(aa)

def on_release(key):
    global BacklightLevel
    try:
        if key.char == 'e':
            if (BacklightLevel < 0x0f):
                BacklightLevel = BacklightLevel + 1
                DataToFrame() 
        if key.char == 'd':
            if (BacklightLevel > 0):
                BacklightLevel = BacklightLevel - 1
                DataToFrame()
        
    except AttributeError:
        if key == keyboard.Key.esc:
            # Stop listener
            return False
        # print("special key")


with keyboard.Listener(
        on_release=on_release) as listener:
    listener.join()
    print("SIM END")
    lin.disable()
    del lin
    print("Deinit done")
    


