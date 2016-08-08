# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0049_update_languageClade'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='language',
            options={'ordering': ['level0',
                                  'level1',
                                  'level2',
                                  'level3',
                                  'sortRankInClade']},
        ),
    ]
