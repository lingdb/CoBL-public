# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0112_auto_20160929_1340'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='meaning',
            options={'ordering': ['gloss']},
        ),
        migrations.RenameField(
            model_name='meaning',
            old_name='elicitation',
            new_name='meaningSetIx',
        ),
        migrations.AddField(
            model_name='meaning',
            name='meaningSetMember',
            field=models.IntegerField(default=0),
        ),
    ]
