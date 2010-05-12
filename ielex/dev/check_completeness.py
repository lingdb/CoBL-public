#!/usr/bin/env python
from __future__ import print_function
import sys
import os
from django.core.management import setup_environ
sys.path.append(os.path.abspath("../.."))
from ielex import settings
setup_environ(settings)
from ielex.lexicon.models import *

logfile = file("completeness_report.log", "w")

def main():
    ml = MeaningList.objects.get(id=2)
    print("Gloss", "Sw100", "Perc", "(New)", sep="\t", file=logfile)
    for meaning in Meaning.objects.all().extra(select={'lower_gloss':
            'lower(gloss)'}).order_by('lower_gloss'):
        lang_ids = set(["urd", "ltz", "gla"])
        n_coded, n_uncoded, stars = 0, 0, 0
        print()
        print(meaning.gloss)
        for cs in CognateSet.objects.filter(lexeme__meaning=meaning
                ).distinct().order_by("alias"):
            for lexeme in Lexeme.objects.filter(cognate_class=cs):
                n_coded += 1
                print(cs.alias, lexeme.phon_form.encode("utf-8") or
                        lexeme.source_form.encode("utf-8"),
                        lexeme.language.ascii_name, sep="\t")
                try:
                    lang_ids.remove(lexeme.language.iso_code)
                    stars += 1
                except KeyError:
                    pass
        for lexeme in Lexeme.objects.filter(cognate_class=None,
                meaning=meaning):
            n_uncoded += 1
            print("?", lexeme.phon_form.encode("utf-8") or 
                    lexeme.source_form.encode("utf-8"), 
                    lexeme.language.ascii_name, sep="\t")
        complete = 100.0 * n_coded / (n_coded + n_uncoded)
        s100 = "+" if meaning.id in ml.meaning_id_list else ""
        print(meaning.gloss, s100, round(complete, 2), "*"*stars, sep="\t", file=logfile)

    return

if __name__ == "__main__":
    main()
