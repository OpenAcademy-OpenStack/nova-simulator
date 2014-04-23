#!/usr/bin/python

import sys
from nova.cmd.simulator import main

def start(host):
    main(host)
    sys.exit()

if __name__ == "__main__":
    start('i do nothing')