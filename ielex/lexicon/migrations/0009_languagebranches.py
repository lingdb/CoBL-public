# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0008_auto_20151202_1146'),
    ]

    operations = [
        migrations.CreateModel(
            name='LanguageBranches',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('family_ix', models.IntegerField(blank=True)),
                ('level1_branch_ix', models.IntegerField(blank=True)),
                ('level1_branch_name', models.TextField(unique=True, blank=True)),
            ],
        ),
    ]
