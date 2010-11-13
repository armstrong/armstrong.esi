from fabric.api import *
from fabric.decorators import task

import os, sys
sys.path[0:0] = [os.path.join(os.path.realpath('.'), '..'), ]
