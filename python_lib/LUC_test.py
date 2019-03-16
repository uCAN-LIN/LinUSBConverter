import unittest
import LUC

class LUCTesting(unittest.TestCase):
    def setUp(self):
        self.luc = LUC.LUC('COM7')
    def tearDown(self):
        del self.luc
    def test_firmware_version(self):        
        ll = self.luc.reqestFirmwareVersion()
        self.assertEqual(ll, '0102')
    def test_master(self):
        ll = self.luc.openAsMaster()        
        ll = self.luc.addTransmitFrameToTable(0x1,0x2233)        
        self.assertEqual(ll, 1)



def main():
    unittest.main()

if __name__ == "__main__":
    main()