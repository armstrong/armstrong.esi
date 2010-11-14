from fabric.api import *
from fabric.decorators import task

import os, sys
sys.path[0:0] = [os.path.join(os.path.realpath('.'), '..'), ]

try:
    from d51.django.virtualenv.test_runner import run_tests
except ImportError:
    import sys
    sys.stderr.write("This project requires d51.django.virtualenv.test_runner\n")
    sys.exit(-1)

