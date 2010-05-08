# From  Ipython, do
# %run setup_environment.py
import sys
import os
print "-> I E L E X"
from django.core.management import setup_environ
sys.path.append(os.path.abspath("../.."))
from ielex import settings
setup_environ(settings)
from ielex.lexicon.models import *
