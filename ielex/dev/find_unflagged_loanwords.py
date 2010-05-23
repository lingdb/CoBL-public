#!/usr/bin/env python
"""
Find lexical entries which have the string 'loan' in their notes field, but
which aren't flagged as 'loanword' in the cognate judgement.
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
    lexemes = Lexeme.objects.filter(notes__contains="loan")
    for lexeme in lexemes:
        if not is_loanword(lexeme):
            line = "%s '%s' (%s) /lexeme/%s/" % (lexeme.source_form,
                    lexeme.meaning.gloss,
                    lexeme.language.utf8_name, lexeme.id)
            print line.encode("utf-8")
            print " ", lexeme.notes.strip().encode("utf-8")
            print
    return

def is_loanword(lexeme):
    loanword = False
    for cj in lexeme.cognatejudgement_set.all():
        if cj.is_loanword:
            loanword = True
    return loanword


if __name__ == "__main__":
    main()
