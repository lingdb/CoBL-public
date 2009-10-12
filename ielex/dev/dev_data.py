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
        m = Meaning(description=description, gloss=gloss)
        m.save()
        assert m.id == ludewig_id
    except ValueError:
        pass

# Populate Language and DyenName
print "--> Populating Language and DyenName"
for line in file("dyen_iso.tab"):
    try:
        name, iso_code = line.strip().split("\t")
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
nc_ids = [i+1 for i in range(82)]
nc_ids = ",".join([str(i) for i in nc_ids])
l = LanguageList.objects.create(name="no-creoles", language_ids=nc_ids)
l.save()

# Populate lexical data and link to CognateSet objects vis CognateJudgement
# objects
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
        cognate_class_alias = "%s-%s" % (row[0], row[5])
        l = Lexeme(language=language,
                meaning=meaning,
                source_form=source_form)
        l.save()
        if cognate_class_alias not in cognate_classes:
            c = CognateSet()
            cognate_classes[cognate_class_alias] = c
            c.save()
        else:
            c = cognate_classes[cognate_class_alias]
        j = CognateJudgement.objects.create(lexeme=l, cognate_class=c)
        j.save()


# Make cogset aliases
print "--> Making CognateSet aliases"
cogset_aliases = {}
for cj in CognateJudgement.objects.all():
    cogset_aliases.setdefault(cj.lexeme.meaning.gloss,
            set()).add(cj.cognate_class.id)

for meaning in cogset_aliases:
    print "--->", meaning,
    for i, id in enumerate(sorted(cogset_aliases[meaning])):
        print id,
        c = CognateSet.objects.get(id=id)
        c.alias = int2alpha(i+1)
        c.save()
    print

print "-> Complete (%s seconds)" % int(time.time() - start_time)
