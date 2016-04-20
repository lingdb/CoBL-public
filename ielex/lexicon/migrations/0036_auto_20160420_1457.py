# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0035_clone_to_clade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clade',
            name='family_ix',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='clade',
            name='level1_branch_ix',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name='clade',
            name='level2_branch_ix',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name='clade',
            name='level3_branch_ix',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
