import serial
import math
import time
import threading

class LINFrame:
    id = 0
    data = b'0'


class LUC:

    def __def_frame_rx_handler(self,f):
        pass

    def __def_new_frame_rx_handler(self,f):
        pass

    def __init__(self, com):
        self.lastframes = {}
        self.currentframes = {}
        self.ser = serial.Serial(com,timeout=0.02)
        if (self.ser == None):
            raise NameError('SerialPortNotPresent') 
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()
        
        self.__rx_byte_thread_handler = threading.Thread(target=self.__rxThread, args=())                     
        self.__rx_frame_thread_handler = threading.Thread(target=self.__newFrameProcess, args=())
        self.__uart_buffer = ''
        self._stop_event = threading.Event()        
        self.frame_rx_handler = self.__def_frame_rx_handler
        self.new_frame_rx_handler = self.__def_new_frame_rx_handler

    def set_frame_rx_handler(self, rx_handler):
        self.frame_rx_handler = rx_handler

    def set_new_frame_rx_handler(self, rx_handler):
        self.new_frame_rx_handler = rx_handler

    def flushData(self, data):
        self.ser.write(data)
        print(data)
    

    def reqestFirmwareVersion(self):
        self.flushData(b'v\r')
        line = self.ser.readline().decode("utf-8")         
        return line.replace("v","").replace("\r","")

    def openAsMaster(self):
        self.flushData(b'O\r')        
        return (self.ser.readline().decode("utf-8") == '\r')

    def lowSpeed(self):
        self.flushData(b'S2\r')        
        return (self.ser.readline().decode("utf-8") == '\r')
    
    def highSpeed(self):
        self.flushData(b'S1\r')        
        return (self.ser.readline().decode("utf-8") == '\r')

    def openAsSlave(self):
        self.flushData(b'L\r')        
        return (self.ser.readline().decode("utf-8") == '\r')

    def openAsMonitor(self):
        self.flushData(b'l\r')        
        return (self.ser.readline().decode("utf-8") == '\r')

    def close(self):
        self.flushData(b'C\r')        
        return (self.ser.readline().decode("utf-8") == '\r')

    def addTransmitFrameToTable(self,id, data):
        data_str = hex(data).replace("0x","")
        data_len = math.floor(len(data_str)/2)
        line = ('t0' + hex(id).replace("0x","").rjust(2,'0') + str(data_len) + data_str + '\r') 
        self.flushData(line.encode())
        return (self.ser.readline().decode("utf-8") == 'z\r')

    def addReceptionFrameToTable(self,id, len):
        line = ('r0' + hex(id).replace("0x","").rjust(2,'0') + str(len) + '\r') 
        self.flushData(line.encode())
        return (self.ser.readline().decode("utf-8") == 'z\r')

    def enable(self):
        self.flushData(b'r1ff0\r')
        # r = (self.ser.readline().decode("utf-8") == 'z\r')
        self.__rx_byte_thread_handler.start()
        self.__rx_frame_thread_handler.start()
        return 1

    def disable(self):
        if (self.__rx_byte_thread_handler.is_alive()):
            self._stop_event.set()
            self.__rx_byte_thread_handler.join()
            self.__rx_frame_thread_handler.join()
        
        self.flushData(b'r2ff0\r')
        return (self.ser.readline().decode("utf-8") == 'z\r')

    def __isStartingChar(self,c):
        return ((c == 't') or (c == 'r'))

    def __rxThread(self):
        while True:
            if (self._stop_event.is_set()):
                break
                
            while(self.ser.in_waiting > 0):                
                cc = self.ser.read(self.ser.in_waiting).decode('ascii')
                self.__uart_buffer += (cc)                                   
            time.sleep(0.001)
    
    def __newFrameProcess(self):
        while True:
            if (self._stop_event.is_set()):
                break
            f = self.__waitForFrame()
            if (f != None):
                self.frame_rx_handler(f)
                if(self.currentframes.get(f.id) == None) or (self.currentframes[f.id] != f.data):                
                    self.currentframes[f.id] = f.data
                    self.new_frame_rx_handler(f)

    def __waitForFrame(self):
        while True:
            if (self._stop_event.is_set()):
                return None

            if (len(self.__uart_buffer) > 1000):
                self.__uart_buffer = ''

            start = self.__uart_buffer.find('t')
            end =  self.__uart_buffer.find('\r')

            if (start != -1 and end != -1):
                if (start > (end - 5)):
                    self.__uart_buffer = self.__uart_buffer[end:]
                else: 
                    frame_string = self.__uart_buffer[start:end]

                    self.__uart_buffer = ''

                    lf = LINFrame()                
                    lf.id = int(frame_string[2:4],16)
                    lf.data = int(frame_string[5:-1],16)
                    return lf
            
            time.sleep(0.001)

    def deInitSerial(self):
        self.ser.flush() 
        self.ser.close()
        del self.ser

    def __del__(self):
        self.disable()
        self.close()
        self.deInitSerial()
        