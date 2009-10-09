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
import sys
import os.path
from ielex.lexicon.models import *

# Populate Meaning database
for line in file("../../ludewig_terms.tab"):
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
    if iso_code not in ("xto", "hit", "txb"):
        d = DyenName(language=l, name=name)
        d.save()
