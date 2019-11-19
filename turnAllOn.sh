#!/bin/bash

# Turn on all the iLabs interlocks by trying to contact
# a machine:port that's not listening.

export PATH=".:/molbio2/mcahn/anaconda3-python3.5.2/bin:$PATH"

ilabsMonitor.py -u molbio5 -p 12345 -r mcahn@princeton.edu -f 1 -w 3 -t 5 -i 1
