# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ielex.lexicon.validators


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0011_glottocodes'),
    ]

    operations = [
        migrations.CreateModel(
            name='CognateClassList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, validators=[ielex.lexicon.validators.suitable_for_url, ielex.lexicon.validators.standard_reserved_names])),
                ('description', models.TextField(null=True, blank=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CognateClassListOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.FloatField()),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.AddField(
            model_name='cognateclass',
            name='root_language',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='cognateclasslistorder',
            name='cognateclass',
            field=models.ForeignKey(to='lexicon.CognateClass'),
        ),
        migrations.AddField(
            model_name='cognateclasslistorder',
            name='cognateclass_list',
            field=models.ForeignKey(to='lexicon.CognateClassList'),
        ),
        migrations.AddField(
            model_name='cognateclasslist',
            name='cognateclasses',
            field=models.ManyToManyField(to='lexicon.CognateClass', through='lexicon.CognateClassListOrder'),
        ),
        migrations.AlterUniqueTogether(
            name='cognateclasslistorder',
            unique_together=set([('cognateclass_list', 'cognateclass'), ('cognateclass_list', 'order')]),
        ),
    ]
