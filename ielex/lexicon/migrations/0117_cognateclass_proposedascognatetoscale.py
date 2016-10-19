# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0116_cognateclass_proposedascognateto'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='proposedAsCognateToScale',
            field=models.IntegerField(
                default=0,
                choices=[(0, b'1/6=small minority view'),
                         (1, b'2/6=sig. minority view'),
                         (2, b'3/6=50/50 balance'),
                         (3, b'4/6=small majority view'),
                         (4, b'5/6=large majority view')]),
        ),
    ]
