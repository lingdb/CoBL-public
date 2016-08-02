# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0060_auto_20160506_1434'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='languagelist',
            name='data',
        ),
    ]
