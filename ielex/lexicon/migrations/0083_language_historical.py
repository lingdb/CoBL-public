# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0082_language_fill_originalasciiname'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='historical',
            field=models.BooleanField(default=0),
        ),
    ]
