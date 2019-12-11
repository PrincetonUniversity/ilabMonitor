# ilabMonitor

## Overview



This program is for use by core facilities that use [Agilent's iLab Core Facility Management](https://www.agilent.com/en/products/lab-management-software/core-facility-management/ilab-core-facility-management) system.

The program monitors:
* Is the interlock control at Agilent reachable?
* Is the iLab web site running?
* Can a user log in to the iLab web site?

If any of these fail, the program will turn on your interlocks so your users can use the instruments in your facility. It sends an email to notify you of the outage, and another email when the problem is resolved.  (Note that the monitor does not turn off your interlocks when the problem is resolved, because it does not know which interlocks should be on or off).

## Requirements

* Python 3.x -- The program has been tested with Python 3.5.2.  It should work with any version of Python 3.x.  It will not work with Python 2.x.
* Operating sytem -- The program has been run under Red Hat Enterprise Linux versions 6 and 7.  It should work under any operating system that can run Python.
* Interlocks -- The program can control the interlocks made by Synaccess.
* The system that runs the monitor must be able to:
  * Communicate with the iLab interlock control which is at kiosk-access.ilabsolutions.com on port 22 (the SSH) port.
  * Communicate with the interlocks in your facility on port 23 (the telnet port).
  * Browse the iLab web site with https (port 443).
  * Communicate with an SMTP mail server.  If the system running the monitor is running a mail server process, such as Postfix, the mail server can be "localhost".
* An **external** iLab account -- You will need an account and password for the test of whether users can log into the iLab web site.  This must be an external account, that is it must use the login screen for iLab, and not communicate back to your institution for authentication.  This will probably be an "independent user", that is, one who is not a member of your institution.

## Installation

* Install Python 3.x.  The distribution from www.anaconda.org is recommended.
* Download the files from this repository.
* Customize files for your institution and installation:
  * ilab-config.yaml -- This configuration file contains parameters such as how often to check the iLab services, how many failures to allow before turning on the interlocks, and the email addresses that should be notified in the event of a failure and recovery.  Edit this file and change the parameters as needed.  The is in YAML format, which is fairly obvious.  (No tabs allowed!)  There is a version of this file called ilab-config-test.yaml.  Use this for testing your installation.
  * ilabMonitorNanny.sh -- This file can be used to check if the monitor is running and start it if it isn't.  You will have to modify this file for your environment.  There is a version called ilabMonitorNanny-test.sh that you can use for testing.  (It uses the test version of the configuration file).
  * ilabInterlockDevices -- This is a list of the host names or IP addresses of your interlock devices.  There are two columns: the hostname or IP address, and the number of outlets on the interlock device.  These must be separated by a TAB.  There is a version of this file called ilabInterlockDevices-test that you can use for testing.  (The test version of the configuration file references it).
* Create the log directory, which is specified in ilab-config.yaml (currently /var/log/ilab).  Be sure this directory has read/write/search (rwx under Linux) permission for the user that will be running the monitor.
* Other files:
  * echoServer.py -- this script listens on a port.  You can run this to simulate the iLab interlock control port, and quit it (with control-c) to simulate a failure.
  
 ## Testing
 
Customize the files described above.  To simluate everything working:

* Change "ilockurl" and "ilock" port in ilab-config-test to match echoServer.py.  The default is that echoServer.py runs on the same machine as the monitor (so ilockurl would be localhost), and listens on port 8080.
* Change "website" and "expectedText" to a URL you can browse, and some text that web site is expected to contain.
* Change "username" and "password" to the correct external user and password for iLab.

Assuming your are using a Linux system, run the echo server to simulate the iLab interlock control:
 ```
 ./echoServer.py
 ```
 
 And start the monitor:
 ```
 ./ilabMonitorNanny-test.sh
 ```
 
 Watch the log directory (the location and filename of the log file are specified in the config file):
 ```
 tail -f ilabMonitor.log
 ```
 
 You can simulate a failure by quitting the echo server (type control-c).  If you have edit access to the web site specified by the "website" parameter in the config ifle, you can delete the "expectedText" from the web site.  After you have reached the allowed number of failures ("failureLImit" in the config file), you can similute a recovery by starting the echo server again and/or putting the expected text back on the web site.  When there is a failure, all the interlocks listed in ilabInterlockDevices-test should go on.  The log file will list how many devices were turned on, were already on, or could not be turned on.  When there is a recovery, another email is sent.
 
 ## Production
 
 Under Linux you can use crontab to periodically run ilabMonitorNanny.sh to check that the monitor is running, and to start it if it isn't.
 
 
  
