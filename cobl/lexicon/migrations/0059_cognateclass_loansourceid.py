# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0058_auto_20160504_1500'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='loanSourceId',
            field=models.IntegerField(null=True),
        ),
    ]
