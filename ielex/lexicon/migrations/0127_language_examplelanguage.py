# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '306_0133_and_others_to_et_al'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='exampleLanguage',
            field=models.BooleanField(default=0),
        ),
    ]
