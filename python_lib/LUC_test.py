import unittest
import LUC

class LUCTesting(unittest.TestCase):
    def setUp(self):
        self.master = LUC.LUC('COM30')
        self.slave = LUC.LUC('COM7')

        ll = self.master.close()
        ll = self.slave.close()

    def tearDown(self):
        del self.master
        del self.slave

    def test_firmware_version(self):        
        ll = self.master.reqestFirmwareVersion()
        self.assertEqual(ll, '0102')
        ll = self.slave.reqestFirmwareVersion()
        self.assertEqual(ll, '0102')

    def test_comunication(self):
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

        ll = self.slave.waitForFrame(2000)
        self.assertEqual(ll.id, 1)
        self.assertEqual(ll.data, 0x2233)

def main():
    unittest.main()

if __name__ == "__main__":
    main()