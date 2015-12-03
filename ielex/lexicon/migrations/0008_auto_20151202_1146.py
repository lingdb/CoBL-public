# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0007_auto_20151106_1723'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cognateclass',
            name='data',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='cognatejudgement',
            name='data',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='language',
            name='altname',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='languagelist',
            name='data',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='lexeme',
            name='data',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='meaning',
            name='data',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='meaninglist',
            name='data',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='data',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
    ]
