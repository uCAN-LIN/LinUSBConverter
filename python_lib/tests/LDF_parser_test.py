import unittest
from pprint import pprint
from ucanlintools.LDF_parser import parseLDF

class LDFParserTests(unittest.TestCase):
        # def setUp(self):

        # def tearDown(self):

        def test_ldf(self):
            ldf = parseLDF("D:\\e.ldf")
            self.assertEqual(ldf.frames[0].id, 52)
        
        def test_ldf_with_spaces(self):
            ldf = parseLDF("D:\\ldfe.ldf")        
            message = ldf.get_message_by_name('FRAME_A')

            self.assertEqual(ldf.frames[0].id, 52)

        def test_encode_decode_message(self):
            ldf = parseLDF("D:\\ldfe.ldf")        
            message = ldf.get_message_by_id(52)

            bbb = b'\x00\x00\x00\x00\x00\x00' 
            message.decode(bbb)                        
            diff_str = message.diff_str()

            aaa = message.encode({'SIGNAL_A': 1})            
            diff_str = message.diff_str()
            message.decode(aaa)

            message.decode(bbb)                        
            diff_str = message.diff_str()
            self.assertEqual(diff_str, "{'SIGNAL_A' : 0}")

def main():
    unittest.main()

if __name__ == "__main__":
    main()