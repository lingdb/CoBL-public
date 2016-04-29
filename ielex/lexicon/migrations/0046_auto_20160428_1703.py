# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0045_auto_20160428_1506'),
    ]

    operations = [
        migrations.CreateModel(
            name='LanguageClade',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False,
                                        auto_created=True,
                                        primary_key=True)),
                ('cladesOrder', models.IntegerField(default=0)),
                ('clade', models.ForeignKey(to='lexicon.Clade')),
            ],
            options={
                'ordering': ['cladesOrder'],
            },
        ),
        migrations.AlterModelOptions(
            name='language',
            options={'ordering': ['level0', 'level1', 'level2', 'level3']},
        ),
        migrations.RemoveField(
            model_name='language',
            name='clade',
        ),
        migrations.AddField(
            model_name='languageclade',
            name='language',
            field=models.ForeignKey(to='lexicon.Language'),
        ),
        migrations.AddField(
            model_name='language',
            name='clades',
            field=models.ManyToManyField(
                to='lexicon.Clade',
                through='lexicon.LanguageClade',
                blank=True),
        ),
    ]
