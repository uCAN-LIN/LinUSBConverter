import unittest
from pprint import pprint
from LDF_parser import parseLDF

class LDFParserTests(unittest.TestCase):
        # def setUp(self):

        # def tearDown(self):

        def test_ldf(self):
            ldf = parseLDF("D:\\e.ldf")
            self.assertEqual(ldf.frames[0].id, 52)
        
        def test_ldf_with_spaces(self):
            ldf = parseLDF("D:\\ldfe.ldf")        
            message = ldf.get_message_by_name('LIN_ETAT_VCI_1')

            self.assertEqual(ldf.frames[0].id, 52)

        def test_encode_decode_message(self):
            ldf = parseLDF("D:\\ldfe.ldf")        
            message = ldf.get_message_by_name('LIN_ETAT_VCI_1')
            
            aaa = message.encode({'SEEK_DWN_ET_HDC': 1, 'VALID_CDE_RADIO': 1, 'Enable': 1})            
            message.decode(aaa)
            bbb = b'@\x00\x00\x00\x00\x00'
            message.decode(bbb)                        
            diff_str = message.diff_str()
            self.assertEqual(diff_str, "{'VALID_CDE_RADIO' : 0}")

def main():
    unittest.main()

if __name__ == "__main__":
    main()