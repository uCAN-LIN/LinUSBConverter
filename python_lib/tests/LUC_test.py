import unittest
import time
from ucanlintools.LUC import LUC

ff = 0

def rx_any(f):
    global ff
    ff = f

class LUCTesting(unittest.TestCase):
    def setUp(self):
        self.master = LUC('COM15')
        self.slave = LUC('COM7')

        ll = self.master.close()
        ll = self.slave.close()

    def tearDown(self):
        del self.master
        del self.slave

    def test_firmware_version(self):        
        ll = self.master.reqestFirmwareVersion()
        self.assertEqual(ll, '0103')
        ll = self.slave.reqestFirmwareVersion()
        self.assertEqual(ll, '0103')

    def test_comunication(self):
        global ff

        ll = self.master.lowSpeed()
        ll = self.slave.lowSpeed()

        ll = self.master.openAsMaster() 
        ll = self.slave.openAsSlave()       
        self.assertEqual(ll, 1)
        
        ll = self.master.disable()
        ll = self.slave.disable()
        self.assertEqual(ll, 1)        
        
        ll = self.master.addTransmitFrameToTable(0x1,0x2233)
        ll = self.slave.addReceptionFrameToTable(0x1,0x2)
        self.assertEqual(ll, 1)                
        
        ll = self.slave.enable()
        ll = self.master.enable()        
        self.assertEqual(ll, 1)

        self.slave.set_frame_rx_handler(rx_any)
        
        time.sleep(500)
        self.assertEqual(ff.id, 1)
        self.assertEqual(ff.data, 0x2233)

def main():
    unittest.main()

if __name__ == "__main__":
    main()