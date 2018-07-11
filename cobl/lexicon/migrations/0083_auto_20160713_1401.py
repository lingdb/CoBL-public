# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0082_fix_language_originalasciiname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cognateclass',
            name='loanEventTimeDepthBP',
            field=models.TextField(blank=True),
        ),
    ]
