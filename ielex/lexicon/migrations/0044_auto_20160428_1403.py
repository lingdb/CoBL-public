# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0043_remove_language_altname'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clade',
            options={'ordering': ['cladeLevel0',
                                  'cladeLevel1',
                                  'cladeLevel2',
                                  'cladeLevel3']},
        ),
        migrations.AlterModelOptions(
            name='sndcomp',
            options={'ordering': ['lv0', 'lv1', 'lv2', 'lv3']},
        ),
    ]
