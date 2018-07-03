# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0076_remove_source_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cognateclass',
            name='modified',
        ),
        migrations.RemoveField(
            model_name='cognatejudgement',
            name='modified',
        ),
        migrations.RemoveField(
            model_name='lexeme',
            name='modified',
        ),
    ]
