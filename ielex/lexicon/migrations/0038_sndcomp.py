# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0037_auto_20160420_1501'),
    ]

    operations = [
        migrations.CreateModel(
            name='SndComp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lgSetName', models.TextField(unique=True, blank=True)),
                ('lv0', models.IntegerField(default=0)),
                ('lv1', models.IntegerField(default=0)),
                ('lv2', models.IntegerField(default=0)),
                ('lv3', models.IntegerField(default=0)),
                ('cladeLevel0', models.IntegerField(default=0)),
                ('cladeLevel1', models.IntegerField(default=0)),
                ('cladeLevel2', models.IntegerField(default=0)),
                ('cladeLevel3', models.IntegerField(default=0)),
            ],
        ),
    ]
