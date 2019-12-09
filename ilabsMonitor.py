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
import requests

import ilabsWeb
import ilock

dateFormat = '%Y-%m-%d %H:%M:%S'

statusWord = {True : 'SUCCESSFUL', False : 'FAILED'} 

def checkConnection(url, port, timeout, openSecs):
    '''Try a connection to url on port.'''
    
    if timeout is not None:
        socket.setdefaulttimeout(timeout)
    # Create a TCP socket
    s = socket.socket()
    try:
        logger.debug('Connecting to %s on port %s', url, port)
        s.connect((url, port))
        if openSecs is not None:
            time.sleep(openSecs)
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        return True
    except socket.error as e:
        return False

    
def checkWebSite(url, expectedText, timeout):
    logger.debug('Checking %s', url)
    try:
        r = requests.get(url, timeout=timeout)
    except requests.exceptions.ConnectionError as err:
        logger.debug(err)
        return False
    
    if expectedText in r.text:
        logger.debug('Found expected text "%s"', expectedText)
        return True
    else:
        logger.debug('Did not find expected text "%s"', expectedText)
        return False

def sendEmail(sender, recipients, progName, subject, statusMsgs):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['To'] = ', '.join(recipients)
    msg['From'] = config.sender

    body = ['This is an automated message from %s running on %s.' % (progName, socket.getfqdn()), '']
    body.extend(statusMsgs)

    msg.set_content('\n'.join(body))

    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()

def turnOnInterlocks():
    lockDevices = getLockDevices(config.lockDeviceFile)
    for lockDevice, numOutlets in lockDevices:
        logger.info('ilock devices: %s (%d outlets)', lockDevice, numOutlets)

    worked = 0
    failed = 0
    alreadyOn = 0

    for lockDevice, numOutlets in lockDevices:
        logger.info('Checking %s' % lockDevice)
        ild = ilock.Ilock(lockDevice, logger)
        try:
            ild.open()
            logger.debug('%s: initDevice()', lockDevice)
            ild.initDevice()
            logger.debug('%s: getStatus()', lockDevice)
            countOff, countOn = ild.getStatus()
            logger.info('Before turning on %s: outlets off: %d outlets on: %d', lockDevice, countOff, countOn)
            if countOn < numOutlets:
                ild.turnOutletsOn()
                logger.debug('%s: getStatus()', lockDevice)
                countOff, countOn = ild.getStatus()
                logger.info('After turning on %s: outlets off: %d outlets on: %d', lockDevice, countOff, countOn)
                if countOn == numOutlets:
                    worked += 1
                else:
                    failed += 1
                    logger.error('Expected to turn on %d outlets on %s, turned on %d', numOutlets, lockDevice, countOn)
            else:
                alreadyOn += 1
                logger.info('%s is already on', lockDevice)
            ild.close()
        except (socket.timeout, socket.gaierror) as err:
            failed += 1
            logger.error('Could not communicate with %s.', lockDevice)
            logger.error(err)
            
    return worked, failed, alreadyOn

def getLockDevices(lockDeviceFile):
    '''Get a list of the interlock host names and number of outlets from a file.
    The devices and number of outlets are listed one per line, tab-separated.
    Comments are allowed.'''
    
    lockDevices = []
    f = open(lockDeviceFile)
    for line in f:
        line = line.strip()
        if line.startswith('#'):
            continue
        if not line:
            continue
        fields = line.split('\t')
        if len(fields) != 2:
            logger.error('Expected device name and number of outlets, tab-separated, got: %s', line)
            sys.exit(1)
        try:
            lockDevices.append((fields[0], int(fields[1])))
        except (IndexError, ValueError) as err:
            logger.error('Expected device name and number of outlets, tab-separated, got: %s', line)
            sys.exit(1)
    f.close()
    return lockDevices

def handleOutage(sender, recipients, progName, statusMsgs):
    subject = 'iLabs check %s' % statusWord[False]
    emailMsgs = statusMsgs[:]
    emailMsgs.append('Turning on interlocks.')
    for emailMsg in emailMsgs:
        logger.info(emailMsg)
    
    worked, failed, alreadyOn = turnOnInterlocks()

    statusMsg2 = 'Turned on: %d, failed to turn on: %d, already on: %d.' % (worked, failed, alreadyOn)
    logger.info(statusMsg2)
    emailMsgs.append(statusMsg2)
    sendEmail(sender, recipients, progName, subject, emailMsgs)

def handleRecovery(sender, recipients, progName, statusMsgs):
    subject = 'iLabs check %s' % statusWord[True]
    for statusMsg in statusMsgs:
        logger.info(statusMsg)
    sendEmail(sender, recipients, progName, subject, statusMsgs)

def checkService(config, iterations):
    consecNotOk = {'ilock': 0, 'website': 0, 'login': 0}
    handledOutage = False

    for x in range(iterations):
        logger.info('Iteration: %d', x)

        try:
            ilockOk = checkConnection(config.ilockurl, config.ilockport, config.timeout, config.openSecs)
        except Exception as err:
            logger.error('Error in checkConnection()')
            logger.error(err)
            ilockOk = False
            
        logger.debug('ilockOk: %s', ilockOk)

        try:
            webSiteOk = checkWebSite(config.website, config.expectedText, config.timeout)

            if webSiteOk:
                try:
                    loginOk = ilabsWeb.loginWorks(config, logger, saveHTML=config.saveHTML)
                except Exception as err:
                    logger.error('Error in loginWorks()')
                    logger.error(err)
                    loginOk = False
            else:
                loginOk = True
        except Exception as err:
            logger.error('Error in checkWebSite()')
            logger.error(err)
            webSiteOk = False
            loginOk = False

        logger.debug('webSiteOk: %s', webSiteOk)
        
        logger.debug('loginOk: %s', loginOk)
        
        dt = datetime.datetime.now()

        if ilockOk and webSiteOk and loginOk:
            consecNotOk['ilock'] = 0
            consecNotOk['website'] = 0
            consecNotOk['login'] = 0
            # If there was an outage, send an email after the first successful connection.
            if handledOutage:
                statusMsgs = ['The interlock control and the iLab web site are up.']
                handleRecovery(config.sender, config.recipients, parser.prog, statusMsgs)
            handledOutage = False
        else:
            if not ilockOk:
                consecNotOk['ilock'] += 1
            if not webSiteOk:
                consecNotOk['website'] += 1
            if not loginOk:
                consecNotOk['login'] += 1
                
        logger.debug("consecNotOk['ilock']: %d consecNotOk['website']: %d consecNotOk['login']: %d", consecNotOk['ilock'], consecNotOk['website'], consecNotOk['login'])
        
        statusFmt1 = 'Connection to %s on port %s %s.  Consecutive failures: %d'
        statusFmt2 = 'Web site should contain "%s", %s.  Consecutive failures: %d'
        statusFmt3 = 'Logging into web site %s.  Consecutive failures: %d'
        statusMsgs = []
        statusMsgs.append(statusFmt1 % (config.ilockurl, config.ilockport, statusWord[ilockOk], consecNotOk['ilock']))
        statusMsgs.append(statusFmt2 % (config.expectedText, statusWord[webSiteOk], consecNotOk['website']))
        statusMsgs.append(statusFmt3 % (statusWord[loginOk], consecNotOk['login']))
        
        # If we have reached the failure limit, turn on the interlock devices and send an email.
        
        if (consecNotOk['ilock'] >= config.failureLimit or consecNotOk['website'] >= config.failureLimit or consecNotOk['login'] >= config.failureLimit) and not handledOutage:
            handleOutage(config.sender, config.recipients, parser.prog, statusMsgs)
            handledOutage = True
        else:
            for statusMsg in statusMsgs:
                logger.info(statusMsg)
        time.sleep(config.wait)

if __name__ == '__main__':
    import argparse
    import logging
    from logging import handlers

    import yaml
    import collections

    os.environ['COLUMNS'] = '150'     # For argparse --help

    parser = argparse.ArgumentParser(description='%s' % __doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-c', '--config', default='ilabs-config.yaml', help='Configuration file')

    parser.add_argument('-v', '--verbose', action='store_true', help='Turn on debug messages.')
    
    args = parser.parse_args()

    configFile = open(args.config)
    
    configDict = yaml.load(configFile)

    configFile.close()

    config = collections.namedtuple('Config', configDict.keys())(*configDict.values())
    
    logger = logging.getLogger(parser.prog)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    logPathname = os.path.join(config.logDirectory, config.logFile)
    
    fh = handlers.RotatingFileHandler(logPathname, maxBytes=10*1024*1024, backupCount=100)
    fileFormatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt=dateFormat)
    fh.setFormatter(fileFormatter)
    logger.addHandler(fh)
    if args.verbose:
        fh.setLevel(logging.DEBUG)
    else:
        fh.setLevel(logging.INFO)

    logger.debug('Configuration parameters:')
    for k, v in config._asdict().items():
        logger.debug('%-20s: %s', k, v)

    if config.iterations > 0:
        iterations = config.iterations
    else:
        iterations = 1024 ** 3
    
    checkService(config, iterations)

    sys.exit(1)
