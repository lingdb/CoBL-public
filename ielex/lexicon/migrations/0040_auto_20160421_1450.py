# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0039_languagebranches_to_sndcomp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='language',
            name='languageBranch',
        ),
        migrations.AddField(
            model_name='language',
            name='clade',
            field=models.ForeignKey(to='lexicon.Clade', null=True),
        ),
        migrations.DeleteModel(
            name='LanguageBranches',
        ),
    ]
