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

  
