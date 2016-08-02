# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0031_language_progress'),
    ]

    operations = [
        migrations.RenameField(
            model_name='languagebranches',
            old_name='sndcompLevel0',
            new_name='cladeLevel0',
        ),
        migrations.RenameField(
            model_name='languagebranches',
            old_name='sndcompLevel1',
            new_name='cladeLevel1',
        ),
        migrations.RenameField(
            model_name='languagebranches',
            old_name='sndcompLevel2',
            new_name='cladeLevel2',
        ),
        migrations.RenameField(
            model_name='languagebranches',
            old_name='sndcompLevel3',
            new_name='cladeLevel3',
        ),
    ]
