# From  Ipython, do
# %run setup_environment.py
import sys
import os
from django.core.management import setup_environ
sys.path.append(os.path.abspath(".."))
from ielex import settings
setup_environ(settings)
from ielex.lexicon.models import *
name = settings.project_short_name
print "+%s+" % ("-" * (len(name) + 2))
print "|", name, "|"
print "+%s+" % ("-" * (len(name) + 2))
