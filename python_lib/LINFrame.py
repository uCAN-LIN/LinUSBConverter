from bitstruct import *

class LINFrame:
    def __init__(self,frame_id, frame_len, name, signals, publisher):
        self.id = frame_id
        self.len = frame_len
        self.name = name
        self.signals = signals
        for s in self.signals:
            s['value'] = s['default_val']
        self.publisher = publisher
    
    def encode(self):
        bitstr = ''
        data = []
        for s in self.signals:
            bitstr += "u" + str(s['size_bits'])
            data.append(s['value'][0])
        
        p = pack(bitstr,*data)
        return p
