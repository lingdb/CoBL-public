# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0044_auto_20160428_1403'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clade',
            old_name='level1_branch_name',
            new_name='cladeName',
        ),
        migrations.RemoveField(
            model_name='clade',
            name='family_ix',
        ),
        migrations.RemoveField(
            model_name='clade',
            name='level1_branch_ix',
        ),
        migrations.RemoveField(
            model_name='clade',
            name='level2_branch_ix',
        ),
        migrations.RemoveField(
            model_name='clade',
            name='level3_branch_ix',
        ),
    ]
