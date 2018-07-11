# -*- coding: utf-8 -*-
# Inspired by:
# https://docs.djangoproject.com/en/1.9/ref/migration-operations/#runpython
# http://clld.org/2015/11/13/glottocode-to-isocode.html
from __future__ import unicode_literals
from django.db import migrations

# A map from iso codes to glottocodes:
isoToGlottoMap = {
    "aae": "arbe1236",
    "aat": "arva1236",
    "afr": "afri1274",
    "aln": "gheg1238",
    "als": "tosk1239",
    "als": "tosk1239",
    "als": "tosk1239",
    "ang": "olde1238",
    "ask": "ashk1246",
    "asm": "assa1263",
    "ave": "aves1237",
    "bel": "bela1254",
    "bel": "bela1254",
    "ben": "beng1280",
    "bgp": "east2304",
    "bho": "bhoj1244",
    "bos": "bosn1245",
    "bre": "bret1244",
    "bre": "bret1244",
    "bre": "bret1244",
    "bsh": "kati1270",
    "bul": "bulg1262",
    "bul": "bulg1262",
    "cat": "stan1289",
    "ces": "czec1258",
    "ces": "czec1258",
    "ces": "czec1258",
    "chu": "chur1257",
    "cor": "corn1251",
    "cym": "wels1247",
    "dan": "dani1285",
    "deu": "stan1295",
    "diq": "diml1238",
    "dsb": "lowe1385",
    "ell": "mode1248",
    "eng": "stan1293",
    "fao": "faro1244",
    "fra": "stan1290",
    "frs": "east2288",
    "fur": "friu1240",
    "gla": "scot1245",
    "gle": "iris1253",
    "glv": "manx1243",
    "goh": "oldh1241",
    "got": "goth1244",
    "grc": "anci1242",
    "grc": "anci1242",
    "gsw": "swis1247",
    "guj": "guja1252",
    "hat": "hait1244",
    "hin": "hind1269",
    "hrv": "croa1245",
    "hsb": "uppe1395",
    "hye": "nucl1235",
    "hye": "nucl1235",
    "isl": "icel1247",
    "ita": "ital1282",
    "kas": "kash1277",
    "kho": "khot1251",
    "kmr": "nort2641",
    "lat": "lati1261",
    "lav": "latv1249",
    "lit": "lith1251",
    "lld": "ladi1250",
    "ltz": "luxe1241",
    "mag": "maga1260",
    "mai": "mait1250",
    "mar": "mara1378",
    "mkd": "mace1250",
    "mkd": "mace1250",
    "nep": "east1436",
    "nep": "east1436",
    "nld": "dutc1256",
    "nob": "norw1259",
    "non": "oldn1244",
    "non": "oldn1244",
    "ori": "nucl1284",
    "osc": "osca1245",
    "oss": "osse1243",
    "oss": "osse1243",
    "oss": "osse1243",
    "pan": "panj1256",
    "pdc": "penn1240",
    "peo": "oldp1254",
    "pes": "west2369",
    "pli": "pali1273",
    "plq": "pala1331",
    "pnb": "west2386",
    "pol": "poli1260",
    "pol": "poli1260",
    "por": "port1283",
    "prg": "prus1238",
    "prn": "pras1239",
    "prv": "prov1247",
    "pst": "cent1973",
    "pus": "nucl1276",
    "rmy": "vlax1238",
    "roh": "roma1326",
    "ron": "roma1327",
    "rup": "arom1237",
    "rus": "russ1263",
    "rus": "russ1263",
    "rwr": "marw1260",
    "san": "sans1269",
    "sga": "oldi1245",
    "sgh": "shug1248",
    "sin": "sinh1246",
    "slk": "slov1269",
    "slk": "slov1269",
    "slv": "slov1268",
    "slv": "slov1268",
    "snd": "sind1272",
    "sog": "sogd1245",
    "spa": "stan1288",
    "sqi": "alba1267",
    "src": "logu1236",
    "src": "logu1236",
    "srh": "sari1246",
    "srn": "sran1240",
    "sro": "camp1261",
    "srp": "serb1264",
    "swe": "swed1254",
    "tgk": "taji1245",
    "tsd": "tsak1248",
    "txb": "tokh1243",
    "ukr": "ukra1253",
    "ukr": "ukra1253",
    "urd": "urdu1245",
    "vls": "vlaa1240",
    "wbl": "wakh1245",
    "wln": "wall1255",
    "xcl": "clas1249",
    "xlc": "lyci1241",
    "xlu": "cune1239",
    "xtg": "tran1282",
    "xto": "tokh1242",
    "xum": "umbr1253"}


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Language = apps.get_model("lexicon", "Language")
    for lang in Language.objects.all():
        if lang.iso_code in isoToGlottoMap:
            lang.altname['glottocode'] = isoToGlottoMap[lang.iso_code]
            lang.save()


def reverse_func(apps, schema_editor):
    Language = apps.get_model("lexicon", "Language")
    for lang in Language.objects.all():
        if lang.iso_code in isoToGlottoMap:
            lang.altname['glottocode'] = ''
            lang.save()


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0010_cognateclass_root_form')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
