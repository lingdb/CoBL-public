# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0113_auto_20161004_1315'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='proposedAsCognateTo',
            field=models.ForeignKey(
                related_name='+', to='lexicon.CognateClass', null=True),
        ),
    ]
