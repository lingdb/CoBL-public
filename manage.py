#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ielex.settings")
    from django.core.management import execute_from_command_line
    if sys.argv[1] == 'bibtex':
        from ielex.source_scripts.bibtex_import import *
        bibtex_update(sys.argv[2])
    else:
        execute_from_command_line(sys.argv)
