# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import Max

import ielex.lexicon.models as models


def forwards_func(apps, schema_editor):
    '''
    Fixing LateVedic for #41.
    See https://github.com/lingdb/CoBL/issues/41
    '''
    # Models to work with:
    Language = apps.get_model('lexicon', 'Language')
    LanguageList = apps.get_model('lexicon', 'LanguageList')
    LanguageListOrder = apps.get_model('lexicon', 'LanguageListOrder')
    # Data to work with:
    language = Language.objects.get(ascii_name='LateVedic')
    languageList = LanguageList.objects.get(name='Current')
    N = LanguageListOrder.objects.filter(
        language_list=languageList).aggregate(Max("order")).values()[0]
    # Appending to 'Current' list:
    LanguageListOrder.objects.create(language=language,
                                     language_list=languageList,
                                     order=(N + 1))


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func '
          'of 0086_add_LateVedic_to_current')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0085_language_historical_init')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
