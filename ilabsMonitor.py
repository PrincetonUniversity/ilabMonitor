#!/usr/bin/env python

'''Monitor the iLabs URL and port that is used to turn on the interlock
devices.  This is the URL and port that the iLabs bridge talks to.

If we cannot connect for a certain number of consecutive attempts,
turn all the interlock devices on, and send an email.  If the connection
recovers, send an email.'''


import socket
import sys
import os
import datetime
import time
from email.message import EmailMessage
import smtplib

import ilock

defaultUrl = 'kiosk-access.ilabsolutions.com'
defaultPort = 22
defaultTimeoutSecs = 10
defaultOpenSocketSecs = None
defaultSender = 'mcahn@princeton.edu'
defaultRecipients = ['mcahn@princeton.edu']
defaultIterations = 0   # Forever-ish
defaultFailureLimit = 5
defaultWaitSecs = 60.0
defaultLockDeviceFile = '/usr/local/etc/ilabsInterlockDevices'
defaultLogFile = '/var/log/ilabs/ilabsMonitor.log'

dateFormat = '%Y-%m-%d %H:%M:%S'

statusWord = {True : 'SUCCESSFUL', False : 'FAILED'} 

def checkConnection(url, port, timeout, opensecs):
    '''Try a connection to url on port.'''
    
    if timeout is not None:
        socket.setdefaulttimeout(timeout)
    # Create a TCP socket
    s = socket.socket()
    try:
        s.connect((url, port))
        if opensecs is not None:
            time.sleep(opensecs)
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        return True
    except socket.error as e:
        return False

def sendEmail(sender, recipients, progName, subject, statusMsgs):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['To'] = ', '.join(recipients)
    msg['From'] = args.sender

    body = ['This is an automated message from %s running on %s.' % (progName, socket.gethostname()), '']
    body.extend(statusMsgs)

    msg.set_content('\n'.join(body))

    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()

def turnOnInterlocks():
    lockDevices = getLockDevices(args.lockdevicefile)
    logger.info('ilock devices: %s', ', '.join(lockDevices))

    worked = 0
    failed = 0
    alreadyOn = 0

    for lockDevice in lockDevices:
        logger.info('Checking %s' % lockDevice)
        ild = ilock.Ilock(lockDevice)
        ild.open()
        ild.initDevice()
        countOff, countOn = ild.getStatus()
        logger.info('Before turning on %s: outlets off: %d outlets on: %d', lockDevice, countOff, countOn)
        if countOn < ilock.numOutlets:
            ild.turnOutletsOn()
            countOff, countOn = ild.getStatus()
            logger.info('After turning on %s: outlets off: %d outlets on: %d', lockDevice, countOff, countOn)
            if countOn == ilock.numOutlets:
                worked += 1
            else:
                failed += 1
                logger.error('Expected to turn on %d outlets on %s, turned on %d', ilock.numOutlets, lockDevice, countOn)
        else:
            alreadyOn += 1
            logger.info('%s is already on', lockDevice)
        ild.close()
        
        return worked, failed, alreadyOn

def getLockDevices(lockDeviceFile):
    '''Get a list of the interlock host names from a file.
    The devices are listed one per line.  Comments are allowed.'''
    
    lockDevices = []
    f = open(lockDeviceFile)
    for line in f:
        line = line.strip()
        if line.startswith('#'):
            continue
        if not line:
            continue
        lockDevices.append(line)
    f.close()
    return lockDevices

def handleOutage(sender, recipients, progName, statusMsg):
    subject = 'iLabs check %s' % statusWord[False]
    statusMsg1 = statusMsg + ' Turning on interlocks.  '
    emailMsgs = [statusMsg, 'Turning on interlocks.']
    logger.info(statusMsg1)

    worked, failed, alreadyOn = turnOnInterlocks()

    statusMsg2 = 'Turned on: %d, failed to turn on: %d, already on: %d.' % (worked, failed, alreadyOn)
    logger.info(statusMsg2)
    emailMsgs.append(statusMsg2)
    sendEmail(sender, recipients, progName, subject, emailMsgs)

def handleRecovery(sender, recipients, progName, statusMsg):
    subject = 'iLabs check %s' % statusWord[True]
    logger.info(statusMsg)
    sendEmail(sender, recipients, progName, subject, [statusMsg])

def checkService(args):
    consecNotOk = 0
    handledOutage = False

    for x in range(iterations):
        ok = checkConnection(args.url, args.port, args.timeout, args.opensecs)

        dt = datetime.datetime.now()

        if ok:
            consecNotOk = 0
            # If there was an outage, send an email after the first successful connection.
            if handledOutage:
                statusMsg = '%s Connection to %s on port %s %s.' % (dt.strftime(dateFormat), args.url, args.port, statusWord[ok])
                handleRecovery(args.sender, args.recipient, parser.prog, statusMsg)
            handledOutage = False
        else:
            consecNotOk += 1

        statusMsg = '%s Connection to %s on port %s %s.  Consecutive failures: %d.' % (dt.strftime(dateFormat), args.url, args.port, statusWord[ok], consecNotOk)

        # If we have reached the failure limit, turn on the interlock
        # devices and send an email.
        if consecNotOk >= args.failure_limit and not handledOutage:
            handleOutage(args.sender, args.recipient, parser.prog, statusMsg)
            handledOutage = True
        else:
            logger.info(statusMsg)

        time.sleep(args.wait)

if __name__ == '__main__':
    import argparse
    import logging
    from logging import handlers

    os.environ['COLUMNS'] = '150'     # For argparse --help

    parser = argparse.ArgumentParser(description='%s' % __doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-u', '--url', default=defaultUrl, help='URL (or IP address) to check.')
    
    parser.add_argument('-p', '--port', type=int, default=defaultPort, help='Port to check.')

    parser.add_argument('-t', '--timeout', type=float, default=defaultTimeoutSecs, help='Socket timeout in seconds.')

    parser.add_argument('-o', '--opensecs', type=float, default=defaultOpenSocketSecs, help='Keep socket open for this many seconds.')

    parser.add_argument('-s', '--sender', default=defaultSender, help='Mail "From" address.')

    parser.add_argument('-r', '--recipient', action='append', default=defaultRecipients,
                help='Email "To" address (may be specified multiple times).')

    parser.add_argument('-i', '--iterations', type=int, default=defaultIterations, help='Number of iterations (0 = run forever).')

    parser.add_argument('-w', '--wait', type=float, default=defaultWaitSecs, help='Wait time between tries in seconds.')

    parser.add_argument('-f', '--failure_limit', type=int, default=defaultFailureLimit, help='Turn on interlocks after this many failures.')

    parser.add_argument('-l', '--lockdevicefile', default=defaultLockDeviceFile,
                        help='File listing interlock device host names, one per line.')

    parser.add_argument('--logfile', default=defaultLogFile, help='Log file name.')

    args = parser.parse_args()

    if args.iterations > 0:
        iterations = args.iterations
    else:
        iterations = 1024 ** 3

    logger = logging.getLogger(parser.prog)
    logger.setLevel(logging.DEBUG)
    fh = handlers.RotatingFileHandler(args.logfile, maxBytes=10*1024*1024, backupCount=100)
    fileFormatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt=dateFormat)
    fh.setFormatter(fileFormatter)
    logger.addHandler(fh)
    fh.setLevel(logging.DEBUG)

    checkService(args)

    sys.exit(1)
