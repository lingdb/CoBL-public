# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0121_auto_20161021_0109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='citation_text',
            field=models.TextField(),
        ),
    ]
