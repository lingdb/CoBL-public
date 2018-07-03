# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '306_0127_fix_issue_223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='shorthand',
            field=models.CharField(max_length=128, blank=True),
        ),
    ]
