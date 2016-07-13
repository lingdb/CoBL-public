# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0083_cognateclass_loanEventTimeDepth'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cognateclasslist',
            name='cognateclasses',
        ),
        migrations.AlterUniqueTogether(
            name='cognateclasslistorder',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='cognateclasslistorder',
            name='cognateclass',
        ),
        migrations.RemoveField(
            model_name='cognateclasslistorder',
            name='cognateclass_list',
        ),
        migrations.DeleteModel(
            name='CognateClassList',
        ),
        migrations.DeleteModel(
            name='CognateClassListOrder',
        ),
    ]
