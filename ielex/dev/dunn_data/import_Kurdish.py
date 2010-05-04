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

assert False # don't run me again

sw2mid = {}
fileobj = file("../ielex-wiki-swadesh-ids.csv")
fileobj.next()
for line in fileobj:
    row = line.strip().split("\t")
    try:
        sw100Id = int(row[2])
        mId = int(row[0])
        sw2mid[sw100Id] = mId
    except ValueError:
        pass
assert len(sw2mid) == 100

language = Language.objects.get(iso_code="kmr")
source = Source.objects.get(id=64)

def main():
    data = []
    soup = BeautifulSoup(file("kurdish-raw.html"))
    header = False
    for row in soup.table("tr"):
        if not header:
            header = row("th")
            for i, cell in enumerate(header):
                # print(i, cell.string, "", sep="|")
                if cell.string == "Kurdish":
                    kurdish_idx = i
                elif cell.string == "English":
                    english_idx = i
                else: 
                    pass
            number_idx = 0
            assert kurdish_idx
            assert english_idx
        else:
            for i, cell in enumerate(row("td")):
                if i == number_idx:
                    number = cell.string
                elif i == english_idx:
                    english = tidy(cell.string)
                elif i == kurdish_idx:
                    for elem in cell.contents:
                        if elem.string:
                            kurdish = tidy(elem.string)
                            meaning_id = sw2mid[int(number)]
                            #print(meaning_id, english, kurdish, sep=" | ")
                            meaning = Meaning.objects.get(id=meaning_id)
                            lexeme = Lexeme.objects.create(meaning=meaning,
                                    language=language,
                                    source_form=kurdish)
                            citation = LexemeCitation.objects.create(lexeme=lexeme,
                                    source=source,
                                    reliability="B")

    return


def tidy(s):
    return s.replace("[","").replace("]", "")

if __name__ == "__main__":
    main()
