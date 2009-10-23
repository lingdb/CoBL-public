#!/usr/bin/env python
"""
Populate a database with some basic data

From bash::
    $ rm db.sqlite
    $ python manage.py syncdb

Then run this script (will only work from its base directory)
"""
import glob
import os
import sys
import time
import re

start_time = time.time()
print "-> I E L E X"
print "->"
print "-> Setting up environment"
from django.core.management import setup_environ
sys.path.append(os.path.abspath("../.."))
from ielex import settings
setup_environ(settings)
from ielex.lexicon.models import *
from ielex.utilities import int2alpha

POLYSEMY = file("polysemy.txt", "w")

def is_empty(l):
    empty = True
    for e in l:
        if e.strip():
            empty = False
    return empty

# Populate Meaning database
print "--> Populating Meaning Database"
for line in file("ludewig_terms.tab"):
    ludewig_id, description = line.strip().split("\t")
    try:
        ludewig_id = int(ludewig_id)
        if description.startswith("TO "):
            gloss = description.split()[1].lower()
        else:
            gloss = description.split()[0].lower()
        m = Meaning.objects.create(description=description, gloss=gloss)
        assert m.id == ludewig_id
    except ValueError:
        pass

# Populate Language and DyenName
print "--> Populating Language and DyenName"
for line in file("dyen_iso.tab"):
    line = line.strip()
    if line:
        try:
            name, iso_code = line.split("\t")
            l = Language(iso_code=iso_code, 
                    ascii_name=name.title(),
                    utf8_name=name.title().replace("_"," "))
        except ValueError:
            name = line.strip()
            l = Language(ascii_name=name.title(),
                    utf8_name=name.title().replace("_"," "))
        l.save()

        d = DyenName(language=l, name=name)
        d.save()

# Change a couple of names
for (code, name) in [("nld", "Dutch"), ("eng", "English")]:
    l = Language.objects.get(iso_code=code)
    l.ascii_name = name
    l.save()
l = Language.objects.get(ascii_name="Penn_Dutch")
l.ascii_name = "Pennsylvania Dutch"
l.utf8_name = "Pennsylvania Dutch"
l.save()

# Make some default id lists
# gray atkinson
ga_ids = ",".join([str(i) for i in [i+1 for i in range(87)]])
l = LanguageList.objects.create(name="GA2003", language_ids=ga_ids)
l.save()
# dyen kruskal black
dkb_ids = [i+1 for i in range(87)]
for n in [80,81,82]:
    dkb_ids.remove(n)
dkb_ids = ",".join([str(i) for i in dkb_ids])
l = LanguageList.objects.create(name="DKB1992", language_ids=dkb_ids)
l.save()
# no creoles
# nc_ids = [i+1 for i in range(82)]
# nc_ids = ",".join([str(i) for i in nc_ids])
# l = LanguageList.objects.create(name="no-creoles", language_ids=nc_ids)
# l.save()

dkb_text = "Dyen, Isidore Kruskal, Joseph and Black, Paul (1992). An "\
        "Indoeuropean Classification, a Lexicostatistical Experiment. "\
        "Transactions of the American Philosophical Society 82/5."
dkb1992 = Source.objects.create(citation_text=dkb_text, type_code="P")

# Populate lexical data
# - link to CognateSet objects vis CognateJudgement objects
# - link to Source via LexemeCitation objects
print "--> Populating lexical data"
cognate_classes = {} # alias: CognateSet
for filename in glob.glob("dyen_data/*.csv"):
    dyen_name = filename[10:-4]
    print "--->", dyen_name
    language = DyenName.objects.get(name=dyen_name).language # Language object
    fileobj = file(filename)
    fileobj.next() # skip header
    for line in fileobj:
        row = line.split("\t")
        meaning = Meaning.objects.get(id=int(row[0]))
        source_form = row[1].strip()
        cognate_class_alias = row[5]
        cognate_reliability = row[6]
        if not row[5]:
            lexeme_reliability = row[6]
        else:
            lexeme_reliability = "A"
        l = Lexeme.objects.create(language=language,
                meaning=meaning,
                source_form=source_form)
        lc = LexemeCitation.objects.create(lexeme=l,
                source=dkb1992,
                reliability=lexeme_reliability)
        if row[5]: # lexeme belongs to a cognate set 
            if cognate_class_alias not in cognate_classes:
                c = CognateSet()
                cognate_classes[cognate_class_alias] = c
                c.save()
            else:
                c = cognate_classes[cognate_class_alias]
            j = CognateJudgement.objects.create(lexeme=l,
                    cognate_class=c)
            cjc = CognateJudgementCitation.objects.create(cognate_judgement=j,
                    source=dkb1992,
                    reliability=cognate_reliability)

import pprint
pprint.pprint(sorted(cognate_classes))

print "--> note doubtful codings"
for line in file("dyen_data/doubtful_identity.txt"):
    alias1, alias2 = line.strip().split()
    try:
        c1 = cognate_classes[alias1]
        c2 = cognate_classes[alias2]
        c1.notes += "DKB: Doubtful identify with /cognate/%s/\n" % c2.id
        c2.notes += "DKB: Doubtful identify with /cognate/%s/\n" % c1.id
        c1.save()
        c2.save()
    except KeyError:
        print "---> *error*: failed to match", alias1, "or", alias2

# Make cogset aliases
print "--> Making CognateSet aliases"
cogset_aliases = {}
for cj in CognateJudgement.objects.all():
    cogset_aliases.setdefault(cj.lexeme.meaning.gloss,
            set()).add(cj.cognate_class.id)
print

for meaning in cogset_aliases:
    print "--->", meaning,
    for i, id in enumerate(sorted(cogset_aliases[meaning])):
        print id,
        c = CognateSet.objects.get(id=id)
        c.alias = int2alpha(i+1)
        c.save()
    print


# Load up sources

print "--> making source dictionary"
source_dict = {}
for line in file("bibliography.csv"):
    key, value = line.split("\t")
    key, value = key.strip().replace(" ",""), value.strip()
    if "http" in value:
        type_code = "U"
    else:
        type_code = "P"
    source = Source.objects.create(type_code=type_code,
            citation_text=value)
    source_dict[key] = source

print "--> reading ludewig data"
for filename in glob.glob("ludewig_data/*.tab"):
    name = filename.split("/")[1][:-4]
    print "--->", name,
    try:
        language = Language.objects.get(ascii_name=name)
        print "(append)"
    except Language.DoesNotExist:
        language = Language.objects.create(ascii_name=name,
                utf8_name=name.replace("_"," "))
        print "(create)"
    fileobj = file(filename)
    header = fileobj.next().strip()
    # assert header == "ID\tsource_form\tphon_form\tnotes/ altern. Forms (AF)"\
    #         "\tsource\tcognate_set"
    for i, line in enumerate(fileobj):
        if not is_empty(line):
            (meaning_id, source_form, phon_form, notes, raw_sources) = \
                    [e.strip().strip('"').strip() for e in line.split("\t")[:5]]
            meaning_id = int(meaning_id)
            try:
                assert source_form or phon_form
            except AssertionError:
                # raise AssertionError("error: no lexical forms on line %s" % \
                #         (i+2))
                print >>POLYSEMY, "\t".join([name, str(meaning_id), notes,
                        raw_sources])
            if not source_form:
                source_form = phon_form
            meaning = Meaning.objects.get(id=meaning_id)
            lexeme = Lexeme.objects.create(language=language,
                    meaning=meaning,
                    source_form=source_form,
                    phon_form=phon_form,
                    notes=notes)

            for source in raw_sources.split(","):
                source = re.split(r"(?<!http):", source)
                if len(source) == 2:
                    source, pages = source
                    pages = pages.strip()
                else:
                    source = source[0]
                    pages = ""
                source = source.strip()
                source = source.replace(" ","")
                try:
                    assert source in source_dict
                except AssertionError:
                    raise AssertionError("error in source `%s' line %s" % \
                            (source, i+2))
                citation = LexemeCitation.objects.create(lexeme=lexeme,
                        source=source_dict[source],
                        reliability="C",
                        pages=pages)

print "-->", "making sort keys"
# for i, row in enumerate(file("sorted_langs.csv")):
#     row = row.split("\t")
#     lang_id = int(row[2])
#     l = Language.objects.get(id=lang_id)
#     l.sort_key = i+1
#     l.save()
languages = Language.objects.all().order_by("utf8_name")
for i, language in enumerate(languages):
    language.sort_key = i + 1
    language.save()

print "-> Complete (%s seconds)" % int(time.time() - start_time)
ll = LanguageList.objects.get(name="all")
assert len(ll.language_id_list) == Language.objects.count()
