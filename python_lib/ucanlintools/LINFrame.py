class LINFrame:
    """A LIN frame from an LDF, with signal encode/decode.

    Signals are packed the LIN way: the frame data is one little-endian
    integer and each signal occupies size_bits starting at its bit_offset
    (bit 0 = least significant bit of byte 0). A signal without a
    'bit_offset' is placed right after the previous one.
    """

    def __init__(self, frame_id, frame_len, name, signals, publisher):
        self.id = frame_id
        self.len = frame_len
        self.name = name
        self.signals = signals
        bitsting = ""
        offset = 0
        for s in self.signals:
            s.setdefault('bit_offset', offset)
            offset = s['bit_offset'] + s['size_bits']
            s['value'] = list(s['default_val'])     # copy: decode must not change the default
            bitsting += "u" + str(s['size_bits'])
        self.publisher = publisher
        self.bitsting = bitsting
        self.__last_values = {}

    def __byte_len(self):
        used = max((s['bit_offset'] + s['size_bits'] for s in self.signals), default=0)
        return max(self.len, (used + 7) // 8)

    def encode(self, lin_data):
        """Set the given signals ({name: value}) and return the frame bytes.
        Signals not given keep their last value."""
        for dd in lin_data:
            item = next((x for x in self.signals if x['name'] == dd), None)
            if item is not None:
                item['value'][0] = lin_data[dd]

        raw = 0
        for s in self.signals:
            mask = (1 << s['size_bits']) - 1
            raw |= (int(s['value'][0]) & mask) << s['bit_offset']
        return raw.to_bytes(self.__byte_len(), 'little')

    def decode(self, lin_data):
        """Update every signal from the frame bytes; returns their values in
        signal order."""
        raw = int.from_bytes(bytes(lin_data), 'little')
        values = []
        for s in self.signals:
            v = (raw >> s['bit_offset']) & ((1 << s['size_bits']) - 1)
            s['value'][0] = v
            values.append(v)
        return tuple(values)

    def diff_str(self):
        outStr = "{"
        for i, s in enumerate(self.signals):
            val = s['value'][0]
            if (len(self.__last_values) <= i) or (val != self.__last_values[i]):
                self.__last_values[i] = val
                outStr += '\'' + s['name'] + '\'' + " : " + str(val) + ','
        if len(outStr) > 1:
            outStr = outStr[:-1] + "}"
        else:
            outStr += "}"
        return outStr
