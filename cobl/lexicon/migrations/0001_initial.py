# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import cobl.lexicon.validators
import cobl.lexicon.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CognateClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('alias', models.CharField(max_length=3)),
                ('notes', models.TextField(blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', cobl.lexicon.models.CharNullField(
                    blank=True, max_length=128,
                    unique=True, null=True,
                    validators=[cobl.lexicon.validators.suitable_for_url])),
            ],
            options={
                'ordering': ['alias'],
            },
        ),
        migrations.CreateModel(
            name='CognateClassCitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('pages', models.CharField(max_length=128, blank=True)),
                ('reliability', models.CharField(
                    max_length=1, choices=[
                        (b'A', b'High'),
                        (b'B', b'Good (e.g. should be double checked)'),
                        (b'C', b'Doubtful'),
                        (b'L', b'Loanword'),
                        (b'X', b'Exclude (e.g. not the Swadesh term)')])),
                ('comment', models.TextField(blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('cognate_class', models.ForeignKey(
                    to='lexicon.CognateClass')),
            ],
        ),
        migrations.CreateModel(
            name='CognateJudgement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('cognate_class', models.ForeignKey(
                    to='lexicon.CognateClass')),
            ],
        ),
        migrations.CreateModel(
            name='CognateJudgementCitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('pages', models.CharField(max_length=128, blank=True)),
                ('reliability', models.CharField(
                    max_length=1, choices=[
                        (b'A', b'High'),
                        (b'B', b'Good (e.g. should be double checked)'),
                        (b'C', b'Doubtful'),
                        (b'L', b'Loanword'),
                        (b'X', b'Exclude (e.g. not the Swadesh term)')])),
                ('comment', models.TextField(blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('cognate_judgement', models.ForeignKey(
                    to='lexicon.CognateJudgement')),
            ],
        ),
        migrations.CreateModel(
            name='DyenCognateSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=8)),
                ('doubtful', models.BooleanField(default=0)),
                ('cognate_class', models.ForeignKey(
                    to='lexicon.CognateClass')),
            ],
        ),
        migrations.CreateModel(
            name='DyenName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('iso_code', models.CharField(max_length=3, blank=True)),
                ('ascii_name', models.CharField(
                    unique=True, max_length=128,
                    validators=[cobl.lexicon.validators.suitable_for_url])),
                ('utf8_name', models.CharField(unique=True, max_length=128)),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ['ascii_name'],
            },
        ),
        migrations.CreateModel(
            name='LanguageList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('name', models.CharField(
                    unique=True, max_length=128,
                    validators=[
                        cobl.lexicon.validators.suitable_for_url,
                        cobl.lexicon.validators.standard_reserved_names])),
                ('description', models.TextField(null=True, blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='LanguageListOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('order', models.FloatField()),
                ('language', models.ForeignKey(to='lexicon.Language')),
                ('language_list', models.ForeignKey(
                    to='lexicon.LanguageList')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Lexeme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('source_form', models.CharField(max_length=128)),
                ('phon_form', models.CharField(max_length=128, blank=True)),
                ('gloss', models.CharField(max_length=128, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('number_cognate_coded', models.IntegerField(
                    default=0, editable=False)),
                ('denormalized_cognate_classes', models.TextField(
                    editable=False, blank=True)),
                ('cognate_class', models.ManyToManyField(
                    to='lexicon.CognateClass',
                    through='lexicon.CognateJudgement', blank=True)),
                ('language', models.ForeignKey(to='lexicon.Language')),
            ],
        ),
        migrations.CreateModel(
            name='LexemeCitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('pages', models.CharField(max_length=128, blank=True)),
                ('reliability', models.CharField(
                    max_length=1, choices=[
                        (b'A', b'High'),
                        (b'B', b'Good (e.g. should be double checked)'),
                        (b'C', b'Doubtful'),
                        (b'L', b'Loanword'),
                        (b'X', b'Exclude (e.g. not the Swadesh term)')])),
                ('comment', models.TextField(blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('lexeme', models.ForeignKey(to='lexicon.Lexeme')),
            ],
        ),
        migrations.CreateModel(
            name='Meaning',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('gloss', models.CharField(
                    max_length=64, validators=[
                        cobl.lexicon.validators.suitable_for_url])),
                ('description', models.CharField(max_length=64, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('percent_coded', models.FloatField(
                    default=0, editable=False)),
            ],
            options={
                'ordering': ['gloss'],
            },
        ),
        migrations.CreateModel(
            name='MeaningList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('name', models.CharField(
                    max_length=128, validators=[
                        cobl.lexicon.validators.suitable_for_url,
                        cobl.lexicon.validators.standard_reserved_names])),
                ('description', models.TextField(null=True, blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MeaningListOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('order', models.FloatField()),
                ('meaning', models.ForeignKey(to='lexicon.Meaning')),
                ('meaning_list', models.ForeignKey(to='lexicon.MeaningList')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False,
                                        auto_created=True, primary_key=True)),
                ('citation_text', models.TextField(unique=True)),
                ('type_code', models.CharField(
                    default=b'P', max_length=1,
                    choices=[(b'P', b'Publication'),
                             (b'U', b'URL'), (b'E', b'Expert')])),
                ('description', models.TextField(blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['type_code', 'citation_text'],
            },
        ),
        migrations.AddField(
            model_name='meaninglist',
            name='meanings',
            field=models.ManyToManyField(
                to='lexicon.Meaning', through='lexicon.MeaningListOrder'),
        ),
        migrations.AddField(
            model_name='lexemecitation',
            name='source',
            field=models.ForeignKey(to='lexicon.Source'),
        ),
        migrations.AddField(
            model_name='lexeme',
            name='meaning',
            field=models.ForeignKey(
                blank=True, to='lexicon.Meaning', null=True),
        ),
        migrations.AddField(
            model_name='lexeme',
            name='source',
            field=models.ManyToManyField(
                to='lexicon.Source',
                through='lexicon.LexemeCitation', blank=True),
        ),
        migrations.AddField(
            model_name='languagelist',
            name='languages',
            field=models.ManyToManyField(
                to='lexicon.Language',
                through='lexicon.LanguageListOrder'),
        ),
        migrations.AddField(
            model_name='dyenname',
            name='language',
            field=models.ForeignKey(to='lexicon.Language'),
        ),
        migrations.AddField(
            model_name='cognatejudgementcitation',
            name='source',
            field=models.ForeignKey(to='lexicon.Source'),
        ),
        migrations.AddField(
            model_name='cognatejudgement',
            name='lexeme',
            field=models.ForeignKey(to='lexicon.Lexeme'),
        ),
        migrations.AddField(
            model_name='cognatejudgement',
            name='source',
            field=models.ManyToManyField(
                to='lexicon.Source',
                through='lexicon.CognateJudgementCitation'),
        ),
        migrations.AddField(
            model_name='cognateclasscitation',
            name='source',
            field=models.ForeignKey(to='lexicon.Source'),
        ),
        migrations.AlterUniqueTogether(
            name='meaninglistorder',
            unique_together=set([('meaning_list', 'order'),
                                 ('meaning_list', 'meaning')]),
        ),
        migrations.AlterUniqueTogether(
            name='lexemecitation',
            unique_together=set([('lexeme', 'source')]),
        ),
        migrations.AlterOrderWithRespectTo(
            name='lexeme',
            order_with_respect_to='language',
        ),
        migrations.AlterUniqueTogether(
            name='languagelistorder',
            unique_together=set([('language_list', 'language'),
                                 ('language_list', 'order')]),
        ),
        migrations.AlterUniqueTogether(
            name='cognatejudgementcitation',
            unique_together=set([('cognate_judgement', 'source')]),
        ),
        migrations.AlterUniqueTogether(
            name='cognateclasscitation',
            unique_together=set([('cognate_class', 'source')]),
        ),
    ]
