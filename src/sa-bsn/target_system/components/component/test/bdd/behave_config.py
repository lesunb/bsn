#!/usr/bin/env python2

import sys
from behave.__main__ import main as behave_main

if __name__ == '__main__':
    sys.exit(behave_main("features"))
