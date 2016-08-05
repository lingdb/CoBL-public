# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0094_auto_20160805_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='dubiousSet',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='cognateclass',
            name='idiophonic',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='cognateclass',
            name='parallelDerivation',
            field=models.BooleanField(default=0),
        ),
    ]
