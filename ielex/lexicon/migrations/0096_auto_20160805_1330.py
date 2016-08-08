# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0095_auto_20160805_1247'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='revisedBy',
            field=models.CharField(default=b'', max_length=10),
        ),
        migrations.AddField(
            model_name='cognateclass',
            name='revisedYet',
            field=models.BooleanField(default=0),
        ),
    ]
