# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0099_remove_cognateclass_idiophonic'),
    ]

    operations = [
        migrations.CreateModel(
            name='NexusExport',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False,
                                        auto_created=True,
                                        primary_key=True)),
                ('lastTouched', models.DateTimeField(auto_now=True)),
                ('lastEditedBy', models.CharField(default=b'unknown',
                                                  max_length=32)),
                ('exportName', models.CharField(max_length=256, blank=True)),
                ('exportSettings', models.TextField(blank=True)),
                ('exportData', models.BinaryField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
