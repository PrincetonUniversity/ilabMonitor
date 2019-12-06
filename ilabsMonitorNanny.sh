#!/bin/bash

export PATH=".:/molbio2/mcahn/anaconda3-python3.5.2/bin:$PATH"

dir=/molbio2/mcahn/ilabs

monitor_stdout=/var/log/ilabs/ilabsMonitor-stdout.log
nanny_logfile=/var/log/ilabs/ilabsMonitorNanny.log

pid=`pgrep -f 'python.*ilabsMonitor.py'`

echo -n `date "+%Y-%m-%d %H:%M:%S"`": " >> $nanny_logfile

if [[ -z $pid ]]; then
    echo The ilabs monitor is not running, starting it. >> $nanny_logfile

    tail -1 $nanny_logfile | mail -s "ilabs monitor restarted" mcahn@princeton.edu

    cd $dir
    nohup ilabsMonitor.py -r mcahn@princeton.edu -r glaevsky@princeton.edu -r cdecoste@princeton.edu -r kr7@princeton.edu -r azerdoum@princeton.edu -r ilab-support@agilent.com> $monitor_stdout 2>&1 &

else
    words=( $pid )
    if [ ${#words[@]} == 1 ]; then
        echo The ilabs monitor is running. >> $nanny_logfile
    else
        echo ${#words[@]} ilabs monitors are running.  There should only be one. >> $nanny_logfile

        tail -1 $nanny_logfile | mail -s "multiple ilabs monitors running" mcahn@princeton.edu
    fi
fi

