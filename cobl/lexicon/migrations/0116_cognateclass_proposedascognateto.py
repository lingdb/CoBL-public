# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0115_emptySourceYears'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='proposedAsCognateTo',
            field=models.ForeignKey(
                related_name='+', to='lexicon.CognateClass', null=True),
        ),
    ]
