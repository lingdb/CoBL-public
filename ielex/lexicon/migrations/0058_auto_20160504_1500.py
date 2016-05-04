# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0057_auto_20160504_1312'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='loanEventTimeDepthBP',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='cognateclass',
            name='loanSourceCognateClass',
            field=models.ForeignKey(to='lexicon.CognateClass', null=True),
        ),
        migrations.AddField(
            model_name='cognateclass',
            name='sourceFormInLoanLanguage',
            field=models.TextField(blank=True),
        ),
    ]
