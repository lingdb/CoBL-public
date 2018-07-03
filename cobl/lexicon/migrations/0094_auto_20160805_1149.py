# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0093_fix_oldPersian'),
    ]

    operations = [
        migrations.AddField(
            model_name='meaning',
            name='doubleCheck',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='meaning',
            name='exclude',
            field=models.BooleanField(default=0),
        ),
    ]
