# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0047_update_languageClade'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='sortRankInClade',
            field=models.IntegerField(default=0),
        ),
    ]
