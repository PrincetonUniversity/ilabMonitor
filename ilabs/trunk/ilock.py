#!/bin/env python

import telnetlib
import time

numOutlets = 2
defaultSleepSecs = 1.0

encoding = 'utf-8'
commands = {'all outlets on': 'ps 1',
            'all outlets off': 'ps 0',
            'status': 'pshow'}
    
banner = 'Synaccess Inc. Telnet Session V6.1.'.encode(encoding) + b'\n\r'

class Ilock:
    def __init__(self, host, sleepSecs=defaultSleepSecs):
        self.host = host
        self.sleepSecs = sleepSecs

    def open(self):
        self.tn = telnetlib.Telnet(self.host)
        
    def initDevice(self):
        time.sleep(self.sleepSecs)
        self.tn.write(b'\n')
        time.sleep(self.sleepSecs)
        reply = self.tn.read_until(banner)
        self.tn.write(b'\r\n')

    def display(self, b):
        '''Convert the bytes from a telnet read to unicode,
        and display each line.'''

        s = b.decode(encoding)
        lines = s.split('\n')
        for line in lines:
            line = line.strip('\r')
            if line == '>' or line in commands:  # Don't print the prompt or the echo of our commands.
                continue
            print(line)

    def parseStatus(self, b):
        s = b.decode(encoding)
        lines = s.split('\n')
        countOff = 0
        countOn = 0
        for line in lines:
            line = line.strip('\r')
            if 'Outlet1' in line or 'Outlet2' in line:
                fields = line.split('|')
                fields = [f.strip() for f in fields]
                if fields[2] == 'ON':
                    countOn += 1
                elif fields[2] == 'OFF':
                    countOff += 1
        return countOff, countOn

    def turnOutletsOff(self):
        time.sleep(self.sleepSecs)
        self.tn.write('ps 0'.encode(encoding) + b'\r\n')
        time.sleep(self.sleepSecs)
        reply = self.tn.read_very_eager()
        return reply

    def turnOutletsOn(self):
        time.sleep(self.sleepSecs)
        self.tn.write('ps 1'.encode(encoding) + b'\r\n')
        time.sleep(self.sleepSecs)
        reply = self.tn.read_very_eager()
        return reply

    def getStatus(self):
        time.sleep(self.sleepSecs)
        self.tn.write('pshow'.encode(encoding) + b'\r\n')
        time.sleep(self.sleepSecs)
        reply = self.tn.read_very_eager()
        countOff, countOn = self.parseStatus(reply)
        return countOff, countOn

    def close(self):
        self.tn.close()
        
if __name__ == '__main__':

    ilock = Ilock('ilocka04')

    ilock.open()
    
    ilock.initDevice()


    countOff, countOn = ilock.getStatus()
    print('Outlets off: %d outlets on: %d' % (countOff, countOn))

    if (countOff == numOutlets and countOn == 0) or (countOn == numOutlets and countOff == 0):
        if countOff == numOutlets:
            ilock.turnOutletsOn()
        elif countOn == numOutlets:
            ilock.turnOutletsOff()
        countOff, countOn = ilock.getStatus()
        print('Outlets off: %d outlets on: %d' % (countOff, countOn))
    else:
        print('Outlets are not both on or both off, turn them on.')
        ilock.turnOutletsOn()
        countOff, countOn = ilock.getStatus()
        print('Outlets off: %d outlets on: %d' % (countOff, countOn))

    ilock.close()
