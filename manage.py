#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ielex.settings")
    from django.core.management import execute_from_command_line
    if sys.argv[1] == 'bibtex':
        from ielex.bibtex_import import *
        bibtex_update(sys.argv[2])
    if sys.argv[1] == 'updsources':
        from ielex.handle_duplicate_sources import *
        dic = {'merge': {78: [39], 33:[71], 93:[94], 236:[298], 44:[45], 365:[366], 368:[370], 84:[400], 423:[424, 425, 461]},
               'delete': [21],
               'deprecate': [42, 43, 44, 57, 58, 61, 64, 87, 88, 89, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 117, 118, 119, 120, 123, 139, 233]
               }
        handle_sources(dic)
    else:
        execute_from_command_line(sys.argv)
