# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0018_fix_cognateclass_aliases'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='languageBranch',
            field=models.ForeignKey(to='lexicon.LanguageBranches', null=True),
        ),
    ]
