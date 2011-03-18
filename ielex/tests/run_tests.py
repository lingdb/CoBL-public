#!/usr/bin/env python
"""
Ad hoc tests of IELEX setup
"""
import sys
import os
from django.core.management import setup_environ
sys.path.append(os.path.abspath("../.."))
from ielex import settings
setup_environ(settings)
#from ielex.lexicon.models import *
from ielex import urls

def check_unique_url_names():
    names = []
    for u in urls.urlpatterns:
        try:
            assert u.name
            names.append(u.name)
        except(AttributeError,AssertionError):
            pass 
    len_names = len(names) 
    try:
        assert len_names == len(set(names))
        print "url names are unique (%s)" % len_names
    except AssertionError:
        for name in set(names):
            names.remove(name)
        print "Repeated url names:"
        print "\n".join(names)
    return

if __name__ == "__main__":
    check_unique_url_names()
