# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import json
from django.db import migrations


def forwards_func(apps, schema_editor):
    NexusExport = apps.get_model("lexicon", "NexusExport")
    for export in NexusExport.objects.all():
        settings = json.loads(export.exportSettings)
        for k, v in settings.items():
            setattr(export, k, v)
        export.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0136_auto_20161220_1326')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
