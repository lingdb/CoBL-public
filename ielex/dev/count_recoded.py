#!/usr/bin/env python
import sys
import os
print "-> I E L E X"
from django.core.management import setup_environ
sys.path.append(os.path.abspath("../.."))
from ielex import settings
setup_environ(settings)
from ielex.lexicon.models import *

print """
Checking the number of words from the Dyen database which are no longer
cognate-coded by the Dyen team (i.e. we have recoded them).
"""

def main():
    dkb = Source.objects.get(id=1)

    n_cj = Lexeme.objects.filter(source=dkb).distinct().count()
    print "Words from DKB:",  n_cj
    n_cj_dkb = CognateJudgement.objects.filter(source=dkb).distinct().count()
    print "  Coded by DKB:", n_cj_dkb
    print "%s%% of the original coding is preserved" % (n_cj_dkb * 100 / n_cj)
    print
    print "Missing sources:"
    for cj in CognateJudgement.objects.filter(source__isnull=True):
        print " ", cj.lexeme.meaning.gloss, cj.lexeme, cj.lexeme.id
    return

if __name__ == "__main__":
    main()
