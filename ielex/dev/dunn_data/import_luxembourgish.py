#!/usr/bin/env python
import sys
import os
from django.core.management import setup_environ
sys.path.append(os.path.abspath("../../.."))
from ielex import settings
setup_environ(settings)
from ielex.lexicon.models import *

sys.exit("Exited: this script shouldn't need to be run again")

iso_code = "ltz"

def main():
    data = []
    ielex_ids = get_ielex_id()
    for line in file("Luxembourgish.csv"):
        row = line.strip().split("\t")
        wiki_id = int(row[0])
        lexeme = row[1]
        try:
            note = row[2]
        except IndexError:
            note = ""
        data.append((ielex_ids[wiki_id], lexeme, note))
    language=Language.objects.get(iso_code=iso_code)
    for meaning_id, source_form, note in data:
        meaning = Meaning.objects.get(id=meaning_id)
        lexeme = Lexeme.objects.create(meaning=meaning,
                language=language,
                source_form=source_form,
                notes=note)
        #lexeme.save()
    return

def get_ielex_id():
    wiki2ielex = {}
    fo = file("../ielex-wiki-swadesh-ids.csv")
    fo.next() # skip header
    for line in fo:
        row = line.strip().split("\t")
        wiki2ielex[int(row[1])] = int(row[0])
    return wiki2ielex

if __name__ == "__main__":
    main()
