# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0096_auto_20160805_1330'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='ideophonic',
            field=models.BooleanField(default=0),
        ),
    ]
