# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0119_auto_20161007_0103'),
    ]

    operations = [
        migrations.RenameField(
            model_name='source',
            old_name='type',
            new_name='ENTRYTYPE',
        ),
        migrations.RenameField(
            model_name='source',
            old_name='address',
            new_name='bookauthor',
        ),
        migrations.RenameField(
            model_name='source',
            old_name='journal',
            new_name='editora',
        ),
        migrations.RenameField(
            model_name='source',
            old_name='organization',
            new_name='institution',
        ),
        migrations.RenameField(
            model_name='source',
            old_name='url',
            new_name='link',
        ),
        migrations.RenameField(
            model_name='source',
            old_name='abbreviation',
            new_name='shorthand',
        ),
        migrations.AddField(
            model_name='source',
            name='authortype',
            field=models.CharField(max_length=16, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='booksubtitle',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='editoratype',
            field=models.CharField(max_length=16, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='editortype',
            field=models.CharField(max_length=16, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='isbn',
            field=models.CharField(max_length=32, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='journaltitle',
            field=models.CharField(max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='location',
            field=models.CharField(max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='part',
            field=models.CharField(max_length=32, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='subtitle',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='editor',
            field=models.CharField(max_length=128, blank=True),
        ),
    ]
