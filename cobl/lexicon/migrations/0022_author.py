# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0021_fix_jena200'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False,
                                        auto_created=True,
                                        primary_key=True)),
                ('surname', models.TextField(blank=True)),
                ('firstNames', models.TextField(blank=True)),
                ('email', models.TextField(blank=True)),
                ('website', models.TextField(blank=True)),
                ('initials', models.TextField(blank=True)),
            ],
        ),
    ]
