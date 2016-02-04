# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models

def dyenname_to_languagedata(apps, schema_editor):
    # move (possible) contents of the DyenName table to
    # Language.data["dyen_name"] in preparation for dropping
    # DyenName table
    DyenName = apps.get_model("lexicon", "DyenName")
    for dnobj in DyenName.objects.all():
        dnobj.language.data["dyen_name"] = dnobj.name
        dnobj.language.save()

class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0002_add_JSON_fields'),
    ]

    operations = [
        migrations.RunPython(dyenname_to_languagedata)
    ]
