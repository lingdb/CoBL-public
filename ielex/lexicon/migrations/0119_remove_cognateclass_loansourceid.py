# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0118_auto_20161019_1519'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cognateclass',
            name='loanSourceId',
        ),
    ]
