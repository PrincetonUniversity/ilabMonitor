#!/bin/bash

export PATH=".:/molbio2/mcahn/anaconda3-python3.5.2/bin:$PATH"

dir=/molbio2/mcahn/ilabMonitor

monitor_stdout=/var/log/ilab/ilabMonitor-stdout-test.log
nanny_logfile=/var/log/ilab/ilabMonitorNanny-test.log

pid=`pgrep -f 'python.*ilabMonitor.py'`

echo -n `date "+%Y-%m-%d %H:%M:%S"`": " >> $nanny_logfile

if [[ -z $pid ]]; then
    echo The iLab monitor is not running, starting it. >> $nanny_logfile

    tail -1 $nanny_logfile | mail -s "iLab monitor restarted" mcahn@princeton.edu

    cd $dir
    nohup ilabMonitor.py --config ilab-config-test.yaml > $monitor_stdout 2>&1 &
    
else
    words=( $pid )
    if [ ${#words[@]} == 1 ]; then
        echo The iLab monitor is running. >> $nanny_logfile
    else
        echo ${#words[@]} iLab monitors are running.  There should only be one. >> $nanny_logfile

        tail -1 $nanny_logfile | mail -s "multiple iLab monitors running" mcahn@princeton.edu
    fi
fi
