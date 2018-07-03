# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0134_auto_20161219_1055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='ENTRYTYPE',
            field=models.CharField(
                max_length=32,
                choices=[(b'book', b'book'),
                         (b'article', b'article'),
                         (b'expert', b'expert'),
                         (b'online', b'online'),
                         (b'inbook', b'inbook'),
                         (b'misc', b'misc')]),
        ),
    ]
