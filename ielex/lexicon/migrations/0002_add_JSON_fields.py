# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='data',
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='cognatejudgement',
            name='data',
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='language',
            name='data',
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='languagelist',
            name='data',
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='lexeme',
            name='data',
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='meaning',
            name='data',
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='meaninglist',
            name='data',
            field=jsonfield.fields.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='source',
            name='data',
            field=jsonfield.fields.JSONField(default=dict),
        ),
    ]
