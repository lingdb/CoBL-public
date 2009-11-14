import sys, os, getpass, datetime
from django.core.management import setup_environ
sys.path.append(os.path.abspath("../.."))
from ielex import settings
setup_environ(settings)
from ielex.lexicon.models import *
from django.test.client import Client

# login clients
micdunn = Client()
micdunn.login(username="micdunn", password=getpass.getpass(
    "[micdunn] password: "))
dkb = Client()
dkb.login(username="DKB", password="password")
jullud = Client()
jullud.login(username="jullud", password="password")

# meaning objects
print >> sys.stderr, "--> Meaning"
for meaning in Meaning.objects.all():
    url = "/touch/Meaning/%s/" % meaning.id
    micdunn.get(url)

# language objects
print >> sys.stderr, "--> Language"
for language in Language.objects.all().order_by("id"):
    url = "/touch/Language/%s/" % language.id
    if language.id in (80,81,82) or language.id > 98:
        jullud.get(url)
    else:
        dkb.get(url)

# dkb: < 2009-10-26 09:20:00
dkb_end = datetime.datetime(2009, 10, 26, 9, 20, 0)
# jullud: in between
# micdunn: > 2009-11-01
micdunn_start = datetime.datetime(2009, 11, 1)
# other objects
models = {
        # "Language":Language,
        # "Meaning":Meaning,
        "CognateJudgement":CognateJudgement,
        "CognateJudgementCitation":CognateJudgementCitation,
        "CognateSet":CognateSet,
        "LanguageList":LanguageList,
        "Lexeme":Lexeme,
        "LexemeCitation":LexemeCitation,
        "Source":Source,
        }
for model_name in sorted(models):
    print >> sys.stderr, "-->", model_name
    model = models[model_name]
    for obj in model.objects.all():
        url = "/touch/%s/%s/" % (model_name, obj.id)
        modified = obj.modified
        if modified < dkb_end:
            owner = dkb
        elif modified > micdunn_start:
            owner = micdunn
        else:
            owner = jullud
        owner.get(url)
