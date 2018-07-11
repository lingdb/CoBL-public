# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0080_fix_cognateClassCitations'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='entryTimeframe',
            field=models.TextField(null=True, blank=True),
        ),
    ]
