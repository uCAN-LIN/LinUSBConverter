import bitstruct

class LINFrame:
    def __init__(self,frame_id, frame_len, name, signals, publisher):
        self.id = frame_id
        self.len = frame_len
        self.name = name
        self.signals = signals
        bitsting = ""
        for s in self.signals:
            s['value'] = s['default_val']
            bitsting += "u" + str(s['size_bits'])
        self.publisher = publisher
        self.bitsting = bitsting
        self.__cf = bitstruct.compile(bitsting)        
        self.__last_values = {}

    def encode(self, lin_data):
        for dd in lin_data:
            item = next((x for x in self.signals if x['name'] == dd), None)
            if item != None:
                item['value'][0] = lin_data[dd]
        
        data = list(map(lambda s: s['value'][0], self.signals))        
        p = self.__cf.pack(*data)
        return p

    def decode(self, lin_data):
        p = self.__cf.unpack(lin_data)  
        for i,s in enumerate(self.signals):                                    
            s['value'][0] = p[i]
        return p
    def diff_str(self):
        outStr = "{"
        for i,s in enumerate(self.signals):
            val = s['value'][0]
            if (len(self.__last_values) <= i) or (val != self.__last_values[i]):
                self.__last_values[i] = val
                outStr += '\'' + s['name']  + '\'' + " : " + str(val) + ','
        if len(outStr) > 1:
            outStr = outStr[:-1] + "}"
        else:
            outStr += "}"
        return outStr   


