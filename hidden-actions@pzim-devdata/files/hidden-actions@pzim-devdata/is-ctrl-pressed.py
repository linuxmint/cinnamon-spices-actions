#!/usr/bin/env python3
from Xlib import X, display
import sys

d = display.Display()
root = d.screen().root
ptr = root.query_pointer()

if ptr.mask & X.ControlMask:
    sys.exit(0)
else:
    sys.exit(1)
