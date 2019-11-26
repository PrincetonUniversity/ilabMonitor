#!/bin/env python

'''Test if we can log into iLab.'''

import os
import requests
import lxml.html
import datetime
import logging

username = 'matthew.cahn@gmail.com'
password = '2Monitor|Not'

data={'login': username,
      'password': password}

loginPage = 'https://princeton.corefacilities.org/account/login#'
loggedInPage = 'https://princeton.corefacilities.org'

successMsg = 'Logged in successfully'

logDir = '/var/log/ilabs'
loginPageFilename = 'ilab-login-page'
loginResponseFilename = 'ilab-login-response'
loggedInFilename = 'ilab-logged-in-page'

def loginWorks(logger, saveHTML=False):
    '''Return True or False depending on whether we can log into iLab.
    If saveHTML is True, the HTML from the iLab pages will be saved.  Otherwise
    only response to the login attempt will be saved, and only if it fails.'''

    logger.debug('Trying to log into %s as %s', loginPage, username)
    
    timeStamp = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d-%H%M%S')

    loginPagePathname = '{}_{}'.format(os.path.join(logDir, loginPageFilename), timeStamp)
    loginResponsePathname  = '{}_{}'.format(os.path.join(logDir, loginResponseFilename), timeStamp)
    loggedInPathname  = '{}_{}'.format(os.path.join(logDir, loggedInFilename), timeStamp)
    
    s = requests.session()

    try:
        loginPageResponse = s.get(loginPage)
    except requests.exceptions.ConnectionError as err:
        logger.error(err)
        return False
    
    if saveHTML:
        f = open(loginPagePathname, 'w')
        f.write(loginPageResponse.text)
        f.close()

    # Make a dictionary of all the hidden inputs in the form on the login page.
    
    login_html = lxml.html.fromstring(loginPageResponse.text)
    hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')
    form = {}
    for hi in hidden_inputs:
        try:
            form[hi.attrib["name"]] = hi.attrib["value"]
        except KeyError:
            pass

    # Add our username and password
    
    form.update(data)
    
    # Log in.  The response should contain the successMsg

    try:
        loginResponse = s.post(loginPage, data=form)
    except requests.exceptions.ConnectionError as err:
        logger.error(err)
        return False

    if successMsg in loginResponse.text:
        logger.info('Found "%s" in response to login.', successMsg)
    else:
        logger.error('Failed to find "%s" in response to login.', successMsg)
        
    if not successMsg in loginResponse.text or saveHTML:
        f = open(loginResponsePathname, 'w')
        f.write(loginResponse.text)
        f.close()

    # It's not necessary to do this, but if you do, the resulting page
    # should have the user's name in it.

    if saveHTML:
        try:
            loggedInResponse = s.get(loggedInPage)
        except requests.exceptions.ConnectionError as err:
            logger.error(err)
            return False

        f = open(loggedInPathname, 'w')
        f.write(loggedInResponse.text)
        f.close()

    return successMsg in loginResponse.text

if __name__ == '__main__':

    logger = logging.getLogger()
    
    status = loginWorks(logger, saveHTML=True)

    print('status: {}'.format(status))
