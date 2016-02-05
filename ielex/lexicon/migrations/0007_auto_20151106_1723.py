# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ielex.lexicon.validators


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0006_auto_20151106_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meaninglist',
            name='name',
            field=models.CharField(
                unique=True, max_length=128,
                validators=[
                    ielex.lexicon.validators.suitable_for_url,
                    ielex.lexicon.validators.standard_reserved_names]),
        ),
    ]
