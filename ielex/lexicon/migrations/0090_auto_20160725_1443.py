# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0089_fix_citation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cognateclasscitation',
            name='reliability',
            field=models.CharField(
                default=b'A',
                max_length=1,
                choices=[(b'A', b'High'),
                         (b'B', b'Good (e.g. should be double checked)'),
                         (b'C', b'Doubtful'),
                         (b'L', b'Loanword'),
                         (b'X', b'Exclude (e.g. not the Swadesh term)')]),
        ),
        migrations.AlterField(
            model_name='cognatejudgementcitation',
            name='reliability',
            field=models.CharField(
                default=b'A',
                max_length=1,
                choices=[(b'A', b'High'),
                         (b'B', b'Good (e.g. should be double checked)'),
                         (b'C', b'Doubtful'),
                         (b'L', b'Loanword'),
                         (b'X', b'Exclude (e.g. not the Swadesh term)')]),
        ),
        migrations.AlterField(
            model_name='lexemecitation',
            name='reliability',
            field=models.CharField(
                default=b'A',
                max_length=1,
                choices=[(b'A', b'High'),
                         (b'B', b'Good (e.g. should be double checked)'),
                         (b'C', b'Doubtful'),
                         (b'L', b'Loanword'),
                         (b'X', b'Exclude (e.g. not the Swadesh term)')]),
        ),
    ]
