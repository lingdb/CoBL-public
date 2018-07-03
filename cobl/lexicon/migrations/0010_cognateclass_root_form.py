# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0009_languagebranches'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='root_form',
            field=models.TextField(blank=True),
        ),
    ]
