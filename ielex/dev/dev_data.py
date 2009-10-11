"""
Populate a database with some basic data

From bash::
    $ ^C # stop server
    $ rm db.sqlite
    $ python manage.py syncdb
    $ python manage.py shell

Then from ipython::

    In [1]: %run dev/dev_data.py
"""
import glob
import os.path
import sys
from ielex.lexicon.models import *
from ielex.utilities import int2alpha

# Populate Meaning database
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

# Populate lexical data and link to CognateSet objects vis CognateJudgement
# objects
cognate_sets = {} # alias: CognateSet
for filename in glob.glob("dyen_data/*.csv"):
    dyen_name = filename[10:-4]
    language = DyenName.objects.get(name=dyen_name).language # Language object
    fileobj = file(filename)
    fileobj.next() # skip header
    for line in fileobj:
        row = line.split("\t")
        meaning = Meaning.objects.get(id=int(row[0]))
        source_form = row[1].strip()
        cognate_set_alias = "%s-%s" % (row[0], row[5])
        l = Lexeme(language=language,
                meaning=meaning,
                source_form=source_form)
        l.save()
        if cognate_set_alias not in cognate_sets:
            c = CognateSet()
            cognate_sets[cognate_set_alias] = c
            c.save()
        else:
            c = cognate_sets[cognate_set_alias]
        j = CognateJudgement.objects.create(lexeme=l, cognate_set=c)
        j.save()

