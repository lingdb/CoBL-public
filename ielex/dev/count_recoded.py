#!/usr/bin/env python
"""
Checking the number of words from the Dyen database which are no longer
cognate-coded by the Dyen team (i.e. we have recoded them).
"""
import sys
import os
# print "-> I E L E X"
from django.core.management import setup_environ
sys.path.append(os.path.abspath("../.."))
from ielex import settings
setup_environ(settings)
from ielex.lexicon.models import *


def main():
    print __doc__
    dkb = Source.objects.get(id=1)

    n_cj = Lexeme.objects.filter(source=dkb).distinct().count()
    print "Words from DKB:",  n_cj
    n_cj_dkb = CognateJudgement.objects.filter(source=dkb).distinct().count()
    print "  Coded by DKB:", n_cj_dkb
    print "%.1f%% of the DKB coding has been changed" % ((n_cj - n_cj_dkb) * \
            100.0 / n_cj)
    print
    missing_sources_flag = False
    for cj in CognateJudgement.objects.filter(source__isnull=True):
        if not missing_sources_flag:
            missing_sources_flag = True
            print "Missing sources:"
        print " ", cj.lexeme.meaning.gloss, cj.lexeme, cj.lexeme.id
    if missing_sources_flag:
        print
    return

if __name__ == "__main__":
    main()
