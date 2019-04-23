import unittest
from LDF_parser import parseLDF

class LDFParserTests(unittest.TestCase):
        # def setUp(self):

        # def tearDown(self):

        def test_ldf(self):
            ldf = parseLDF("D:\\e.ldf")
            self.assertEqual(ldf.frames[0]['frame_id'], 52)
        
        def test_ldf_with_spaces(self):
            ldf = parseLDF("D:\\ldfe.ldf")        
            message = ldf.get_message_by_name('LIN_ETAT_VCI_1')
            message.encode()
            self.assertEqual(ldf.frames[0]['frame_id'], 52)
            
def main():
    unittest.main()

if __name__ == "__main__":
    main()