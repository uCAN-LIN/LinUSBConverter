import serial
import math
import time

class LINFrame:
    id = 0
    data = b'0'


class LUC:
    def __init__(self, com):
        self.ser = serial.Serial(com,timeout=1) 

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
        return (self.ser.readline().decode("utf-8") == 'z\r')

    def disable(self):
        self.flushData(b'r2ff0\r')
        return (self.ser.readline().decode("utf-8") == 'z\r')

    def waitForFrame(self, wait_time_ms):
        count = 0
        sleep_time = 0.002
        frame = ''
        while (True):   
            while (self.ser.in_waiting>0): #if incoming bytes are waiting to be read from the serial input buffer
                char = self.ser.read(1).decode('ascii')
                frame += char
                if (char == '\r'):
                    print(frame)
                    lf = LINFrame()                
                    lf.id = int(frame[2:4],16)
                    lf.data = int(frame[5:-1],16)
                    return lf                         
            time.sleep(sleep_time)
            count += 1
            if (count > wait_time_ms/sleep_time/1000):
                return 0 

        
    def __del__(self):
        self.close()
        self.ser.flush() 
        self.ser.close()