#!/bin/env python

import telnetlib
import time

sleepSecs = 1
encoding = 'utf-8'
commands = {'all outlets on': 'ps 1',
            'all outlets off': 'ps 0',
            'status': 'pshow'}
    
host = 'ilocka04'
banner = 'Synaccess Inc. Telnet Session V6.1.'.encode(encoding) + b'\n\r'

def display(b):
    '''Convert the bytes from a telnet read to unicode,
    and display each line.'''
    
    s = b.decode(encoding)
    lines = s.split('\n')
    for line in lines:
        line = line.strip('\r')
        if line == '>' or line in commands:  # Don't print the prompt or the echo of our commands.
            continue
        print(line)
        
def parseStatus(b):
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

def init(tn):
    time.sleep(sleepSecs)
    tn.write(b'\n')
    time.sleep(sleepSecs)
    reply = tn.read_until(banner)
    tn.write(b'\r\n')

def turnOutletsOff(tn):
    print('Turning off outlets')
    time.sleep(sleepSecs)
    tn.write('ps 0'.encode(encoding) + b'\r\n')
    time.sleep(sleepSecs)
    reply = tn.read_very_eager()
    return reply

def turnOutletsOn(tn):
    print('Turning on outlets')
    time.sleep(sleepSecs)
    tn.write('ps 1'.encode(encoding) + b'\r\n')
    time.sleep(sleepSecs)
    reply = tn.read_very_eager()
    return reply

def getStatus(tn):
    print('Getting status')
    time.sleep(sleepSecs)
    tn.write('pshow'.encode(encoding) + b'\r\n')
    time.sleep(sleepSecs)
    reply = tn.read_very_eager()
    countOff, countOn = parseStatus(reply)
    return countOff, countOn

tn = telnetlib.Telnet(host)

init(tn)

turnOutletsOff(tn)

countOff, countOn = getStatus(tn)
print('Outlets off: %d outlets on: %d' % (countOff, countOn))

turnOutletsOn(tn)

countOff, countOn = getStatus(tn)
print('Outlets off: %d outlets on: %d' % (countOff, countOn))

tn.close()
