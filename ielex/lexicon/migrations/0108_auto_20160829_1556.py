# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0107_meaningLists'),
    ]

    operations = [
        migrations.RenameField(
            model_name='nexusexport',
            old_name='exportData',
            new_name='_exportData',
        ),
    ]
