# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0029_languagebranches_defaults'),
    ]

    operations = [
        migrations.AlterField(
            model_name='languagebranches',
            name='distribution',
            field=models.CharField(
                default=b'_',
                max_length=1,
                choices=[(b'U', b'Uniform'),
                         (b'N', b'Normal'),
                         (b'L', b'Log normal'),
                         (b'O', b'Offset log normal'),
                         (b'_', b'None')]),
        ),
    ]
