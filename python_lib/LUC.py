import serial
import math

class LUC:
    def __init__(self, com):
        self.ser = serial.Serial(com,timeout=1) 

    def reqestFirmwareVersion(self):
        self.ser.write(b'v\r')
        line = self.ser.readline().decode("utf-8")         
        return line.replace("v","").replace("\r","")

    def openAsMaster(self):
        self.ser.write(b'O\r')        
        return (self.ser.readline().decode("utf-8") == '\r')

    def addTransmitFrameToTable(self,id, data):
        data_str = hex(data).replace("0x","")
        data_len = math.floor(len(data_str)/2)
        line = ('t'+ hex(id).replace("0x","") + str(data_len) + data_str + '\r') 
        self.ser.write(line.encode())
        return (self.ser.readline().decode("utf-8") == '\r')


    def __del__(self):
        self.ser.close()