# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    '''
    Fixing a typo where I wrote Idiophonic instead of Ideophonic.
    Relates to #263
    '''
    # Models to work with:
    CognateClass = apps.get_model('lexicon', 'CognateClass')
    for c in CognateClass.objects.all():
        if c.idiophonic != c.ideophonic:
            c.ideophonic = c.idiophonic
            c.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0097_cognateclass_ideophonic')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
