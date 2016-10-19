# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    LanguageClade = apps.get_model('lexicon', 'LanguageClade')

    def strLC(lc):
        return ''.join([str(lc.clade_id), str(lc.language_id)])

    strLcMap = dict()
    for lc in LanguageClade.objects.all():
        s = strLC(lc)
        if s in strLcMap:
            other = strLcMap[s]
            if other.cladesOrder < lc.cladesOrder:
                strLcMap[s] = lc
        else:
            strLcMap[s] = lc
    # Remove LanguageClade where smaller order exists:
    for lc in strLcMap.values():
        LanguageClade.objects.filter(clade_id=lc.clade_id,
                                     language_id=lc.language_id,
                                     cladesOrder__lt=lc.cladesOrder).delete()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0075_clean_LanguageClade')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0074_update_LanguageClade')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
