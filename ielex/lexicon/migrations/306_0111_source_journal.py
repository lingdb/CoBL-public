# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '306_0110_auto_20160923_0208'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='journal',
            field=models.ForeignKey(blank=True, to='lexicon.Journal', null=True),
        ),
    ]
