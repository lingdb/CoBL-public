# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0004_drop_table_DyenName'),
    ]

    operations = [
        migrations.RenameField(
            model_name='language',
            old_name='data',
            new_name='altname',
        ),
    ]
