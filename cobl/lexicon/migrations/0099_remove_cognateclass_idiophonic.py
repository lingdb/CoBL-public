# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0098_fix_ideophoic'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cognateclass',
            name='idiophonic',
        ),
    ]
