#!/usr/bin/env python
from __future__ import division, print_function
import sys
import os
from BeautifulSoup import BeautifulSoup

from django.core.management import setup_environ
sys.path.append(os.path.abspath("../../.."))
from ielex import settings
setup_environ(settings)
from ielex.lexicon.models import *

assert False # don't run again

iso_code = "urd"
base_url = "http://ialtrust.com/swadeshlanguagelist"
page_url = "/swadeshLanguageTable.php?language4=Urdu&language5=Urdu+(IPA)&Submit=Go"

def main():
    data = []
    soup = BeautifulSoup(file("urdu-raw.html"))
    for row in soup.table.findAll("tr"):
        row_data = [None,None,None,None]
        for i, cell in enumerate(row.findAll("td")):
            row_data[i] = cell.find(text=True)
        if row_data[0]:
            data.append(row_data)

    ielex_ids = get_ielex_id()

    language = Language.objects.get(iso_code=iso_code)
    source = Source.objects.get(id=64)

    for row in data:
        wiki_id = int(row[0])
        meaning_id = ielex_ids[wiki_id]
        source_form = row[2]
        phon_form = row[3]

        meaning = Meaning.objects.get(id=meaning_id)
        lexeme = Lexeme.objects.create(meaning=meaning,
                language=language,
                source_form=source_form,
                phon_form=phon_form)
        citation = LexemeCitation.objects.create(lexeme=lexeme,
                source=source,
                pages=base_url+page_url,
                reliability="B")
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
