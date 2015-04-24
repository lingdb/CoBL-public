# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SemanticDomain',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=999)),
                ('description', models.TextField(null=True, blank=True)),
                ('relation_ids', models.CommaSeparatedIntegerField(max_length=999, blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='SemanticExtension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('lexeme', models.ForeignKey(to='lexicon.Lexeme')),
            ],
        ),
        migrations.CreateModel(
            name='SemanticExtensionCitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pages', models.CharField(max_length=128, blank=True)),
                ('reliability', models.CharField(max_length=1, choices=[(b'A', b'High'), (b'B', b'Good (e.g. should be double checked)'), (b'C', b'Doubtful'), (b'L', b'Loanword'), (b'X', b'Exclude (e.g. not the Swadesh term)')])),
                ('comment', models.TextField(blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('extension', models.ForeignKey(to='extensional_semantics.SemanticExtension')),
                ('source', models.ForeignKey(to='lexicon.Source')),
            ],
        ),
        migrations.CreateModel(
            name='SemanticRelation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('relation_code', models.CharField(max_length=64)),
                ('long_name', models.CharField(max_length=128)),
                ('description', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='semanticextension',
            name='relation',
            field=models.ForeignKey(to='extensional_semantics.SemanticRelation'),
        ),
        migrations.AddField(
            model_name='semanticextension',
            name='source',
            field=models.ManyToManyField(to='lexicon.Source', through='extensional_semantics.SemanticExtensionCitation'),
        ),
        migrations.AlterUniqueTogether(
            name='semanticextensioncitation',
            unique_together=set([('extension', 'source')]),
        ),
    ]
