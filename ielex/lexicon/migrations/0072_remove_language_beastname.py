# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0071_auto_20160510_1846'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='language',
            name='beastName',
        ),
    ]
