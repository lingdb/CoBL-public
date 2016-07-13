# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ielex.lexicon.models as models

data = {5514: "501",
        5103: "1250",
        975: "800"}


def forwards_func(apps, schema_editor):
    '''
    Saving original entries of loanEventTimeDepthBP.
    See https://github.com/lingdb/CoBL/issues/202
    '''
    CognateClass = apps.get_model('lexicon', 'CognateClass')
    for c in CognateClass.objects.filter(id__in=data.keys()).all():
        c.loanEventTimeDepthBP = data[c.id]
        c.save()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of '
          '0083_cognateclass_loanEventTimeDepth')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0083_auto_20160713_1401')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
