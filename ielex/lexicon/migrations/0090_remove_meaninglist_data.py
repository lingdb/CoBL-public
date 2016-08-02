# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0089_fix_citation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='meaninglist',
            name='data',
        ),
    ]
