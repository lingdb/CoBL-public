#!/usr/bin/env python
import sys
import os
from django.core.management import setup_environ
sys.path.append(os.path.abspath("../../.."))
from ielex import settings
setup_environ(settings)
from ielex.lexicon.models import *

assert False # don't run again

def main():
    source = Source.objects.get(id=63)
    lexemes = Lexeme.objects.filter(language__iso_code="ltz")
    for lexeme in lexemes:
        citation = LexemeCitation.objects.create(lexeme=lexeme,
                source=source,
                reliability="B")
    return

if __name__ == "__main__":
    main()
