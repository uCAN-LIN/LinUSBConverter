import serial
import time
import threading
import logging

logger = logging.getLogger()


class LINFrame:
    """LIN Frame class.
        

    Attributes
    ----------
    id: int 
        frame id
    data: bytearray
        frame data as byte array
    """
    id = 0
    data = bytearray()


class LUC:

    def __def_frame_rx_handler(self, f):
        pass

    def __def_new_frame_rx_handler(self, f):
        pass

    def __init__(self, com, timeout=0.02, baudrate=9600):
        self.lastframes = {}
        self.currentframes = {}
        self.ser = serial.Serial(com, timeout=timeout, baudrate=baudrate)
        if self.ser is None:
            raise NameError('SerialPortNotPresent')
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()

        self.__rx_byte_thread_handler = threading.Thread(target=self.__rxThread, args=())
        self.__rx_frame_thread_handler = threading.Thread(target=self.__newFrameProcess, args=())
        self.__uart_buffer = ''
        self._stop_event = threading.Event()
        # Guards serial writes; writes may come from the main thread and from
        # rx handlers (which run in the frame-processing thread).
        self.__serial_lock = threading.Lock()
        # True once enable() has started the rx thread. While running, the rx
        # thread owns all reads, so command methods must not call readline().
        self.__running = False
        # True once the port has been closed, so disable()/__del__ are idempotent.
        self.__closed = False
        self.frame_rx_handler = self.__def_frame_rx_handler
        self.new_frame_rx_handler = self.__def_new_frame_rx_handler

    def set_frame_rx_handler(self, rx_handler):
        """Sets handler for frame reception, will be called after any frame reception.
        
        Parameters
        ----------  
            rx_handler : function handler, with LINFrame argument 
        """

        self.frame_rx_handler = rx_handler

    def set_new_frame_rx_handler(self, rx_handler):
        """Sets handler for frame reception, will be called only when there is diffrent data on frame received.

        Parameters
        ----------  
            rx_handler : function handler, with LINFrame argument 
        
        """
        self.new_frame_rx_handler = rx_handler

    def flushData(self, data):
        with self.__serial_lock:
            self.ser.write(data)
        logger.info(data)

    def __command(self, data, expected):
        """Send a command and confirm its reply.

        While the converter is running (after enable()) the rx thread owns all
        serial reads, so the reply cannot be read here without racing it; in
        that case the command is written and True is returned. Before enable()
        the reply is read and compared against the expected response string.
        """
        self.flushData(data)
        if self.__running:
            return True
        return self.ser.readline().decode("utf-8") == expected

    def requestFirmwareVersion(self):
        self.flushData(b'v\r')
        line = self.ser.readline().decode("utf-8")
        return line.replace("v", "").replace("\r", "")

    def openAsMaster(self):
        """Open LIN Converter in Master mode"""
        return self.__command(b'O\r', '\r')

    def lowSpeed(self):
        """LIN low speed"""
        return self.__command(b'S2\r', '\r')

    def highSpeed(self):
        """LIN high speed"""
        return self.__command(b'S1\r', '\r')

    def openAsSlave(self):
        """Open LIN Converter in slave mode"""
        return self.__command(b'L\r', '\r')

    def openAsMonitor(self):
        """Open LIN Converter in monitor mode"""
        return self.__command(b'l\r', '\r')

    def close(self):
        """Close LIN connection"""
        return self.__command(b'C\r', '\r')

    def addTransmitFrameToTable(self, id, data):
        """Add a transmit frame to the LIN Converter table.

        In master/slave mode this registers the frame in the schedule table.
        In monitor mode it transmits the frame immediately on the bus.

        Parameters
        ----------
            id : int
                LIN frame id (0..0x3F)
            data : bytes-like or int
                Frame payload. Pass bytes (e.g. b'\\x22\\x33'); an int is
                accepted and encoded as a big-endian byte string.
        """
        return self.__command(self._format_transmit_line(id, data), 'z\r')

    @staticmethod
    def _format_transmit_line(id, data):
        """Build the 't' transmit command bytes for a frame.

        Returns the SLCAN line, e.g. b't00122233\\r' for id=1, data=b'\\x22\\x33'.
        """
        if isinstance(data, int):
            data_str = format(data, 'x')
            if len(data_str) % 2:
                data_str = '0' + data_str
        else:
            data_str = bytes(data).hex()
        data_len = len(data_str) // 2
        line = ('t0' + format(id, '02x') + str(data_len) + data_str + '\r')
        return line.encode()

    def addReceptionFrameToTable(self, id, len):
        """Add a reception header to the LIN Converter table"""
        line = ('r0' + format(id, '02x') + str(len) + '\r')
        return self.__command(line.encode(), 'z\r')

    def enable(self):
        """Enable frame sending"""
        self.__running = True
        self.flushData(b'r1ff0\r')
        # r = (self.ser.readline().decode("utf-8") == 'z\r')
        self.__rx_byte_thread_handler.start()
        self.__rx_frame_thread_handler.start()
        return 1

    def disable(self):
        """Stop reception.

        Idempotent: safe to call more than once and after deInitSerial().
        """
        if self.__closed:
            return False

        if self.__rx_byte_thread_handler.is_alive():
            self._stop_event.set()
            self.__rx_byte_thread_handler.join()
            self.__rx_frame_thread_handler.join()

        # rx thread has stopped, so this method can safely read the reply again
        self.__running = False

        time.sleep(0.010)

        # Discard any received frames still buffered so the reply read below is
        # not contaminated by them.
        self.ser.reset_input_buffer()
        self.flushData(b'r2ff0\r')
        return self.ser.readline().decode("utf-8") == 'z\r'

    def __isStartingChar(self, c):
        return (c == 't') or (c == 'r')

    def __rxThread(self):
        while True:
            if self._stop_event.is_set():
                break

            while self.ser.in_waiting > 0:
                cc = self.ser.read(self.ser.in_waiting).decode('ascii')
                self.__uart_buffer += cc
            time.sleep(0.001)

    def __newFrameProcess(self):
        while True:
            if self._stop_event.is_set():
                break
            f = self.__waitForFrame()
            if f is not None:
                self.frame_rx_handler(f)
                if (self.currentframes.get(f.id) is None) or (self.currentframes[f.id] != f.data):
                    self.currentframes[f.id] = f.data
                    self.new_frame_rx_handler(f)

    def __waitForFrame(self):
        while True:
            if self._stop_event.is_set():
                return None

            if len(self.__uart_buffer) > 1000:
                self.__uart_buffer = ''

            start = self.__uart_buffer.find('t')
            end = self.__uart_buffer.find('\r')

            if start != -1 and end != -1:
                if start > (end - 5):
                    self.__uart_buffer = self.__uart_buffer[start:]
                else:
                    frame_string = self.__uart_buffer[start:end]

                    self.__uart_buffer = ''
                    lf = LINFrame()
                    try:
                        lf.id = int(frame_string[2:4], 16)
                        lf.data = bytes.fromhex(frame_string[5:])
                        return lf
                    except ValueError:
                        pass
                        # @TODO FIXME this should not occur but sometimes does ...
                        # JP: found this error when using default serial baudrate 9600. Changing it to 19200 fixed
                        # the issue for me. Added as optional argument to initialization.
                        # print ("!!id " + frame_string[2:4])
                        # print ("!!data " + frame_string[5:])
                        # print ("!!wf " + frame_string)       

            time.sleep(0.001)

    def deInitSerial(self):
        """Close the serial port. Idempotent: safe to call more than once."""
        if self.__closed:
            return
        self.__closed = True
        try:
            self.ser.flush()
        except Exception:
            pass
        self.ser.close()

    def isRunning(self):
        """Simple function that returns true if rx thread is alive. Useful for implementation of exception and
        interruption (like KeyboardInterrupt) handling in scripts using LUC object.
        """
        return self.__rx_byte_thread_handler.is_alive()

    def __del__(self):
        try:
            self.disable()
        except Exception:
            pass
        try:
            self.deInitSerial()
        except Exception:
            pass
