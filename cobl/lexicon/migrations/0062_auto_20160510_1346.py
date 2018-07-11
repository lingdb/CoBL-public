# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0061_remove_languagelist_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='notProtoIndoEuropean',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='cognateclass',
            name='parallelLoanEvent',
            field=models.BooleanField(default=0),
        ),
    ]
