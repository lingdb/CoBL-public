# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '306_0113_sourceauthor'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SourceAuthor',
        ),
        migrations.AddField(
            model_name='source',
            name='author',
            field=models.ManyToManyField(
                related_name='author', to='lexicon.Author', blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='editor',
            field=models.ManyToManyField(
                related_name='editor', to='lexicon.Author', blank=True),
        ),
    ]
