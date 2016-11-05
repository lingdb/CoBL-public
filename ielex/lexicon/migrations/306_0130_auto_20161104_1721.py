# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '306_0129_import_source_citation_forms'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='source',
            options={'ordering': ['shorthand']},
        ),
        migrations.AddField(
            model_name='source',
            name='TRS',
            field=models.BooleanField(default=False, help_text=b'Traditional reference source (dated).'),
        ),
        migrations.AddField(
            model_name='source',
            name='respect',
            field=models.TextField(help_text=b'A brief summary of the nature of the source its utility.', blank=True),
        ),
    ]
