# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations
import datetime


data = [{u'comment': u'From *sw\u012b(s) '
                     'which reflects the PIE acc. 2 pl. *us-we.',
         u'source_id': 273,
         u'reliability': u'A',
         u'pages': u'48-49',
         u'modified': datetime.datetime(2015, 11, 2, 11, 9, 2, 72904)},
        {u'comment': u"1. PIE *i\u032fu\u0301- 'you', "
                     "pronominal stem, 2nd person non-singular, "
                     "only nominative, suppletive oblique stem "
                     "*u\u032fo\u0301-.\r\n2. PIE *u\u032fo\u0301- "
                     "'you', pronominal stem, 2nd person non-singular, "
                     "oblique. Suppletive nominative PIE "
                     "*i\u032fu\u0301- 'you'. ",
         u'source_id': 294,
         u'reliability': u'A',
         u'pages': u'388-90, 855-860',
         u'modified': datetime.datetime(2015, 12, 9, 22, 4, 20, 365304)},
        {u'comment': u'For the Slavic forms: "The anlaut of the pronoun '
                     'was apparently remodelled after the oblique cases. '
                     'This must have occurred before the delabialization '
                     'of \xfc, which was an allophone of /u/ '
                     'after a preceding *j."',
         u'source_id': 81,
         u'reliability': u'A',
         u'pages': u'533',
         u'modified': datetime.datetime(2016, 7, 1, 13, 23, 49, 867057)}]


def forwards_func(apps, schema_editor):
    '''
    This migration was added as a reaction to problems
    with merging cognate classes described by @CasFre in [1].
    https://github.com/lingdb/CoBL/issues/197
    '''
    CognateClass = apps.get_model('lexicon', 'CognateClass')
    CognateClassCitation = apps.get_model('lexicon', 'CognateClassCitation')
    # Id that needs to get CognateClassCitations attached:
    target = 5822
    try:
        cognateClass = CognateClass.objects.get(id=target)
        sourceIds = set([c.source_id for c in
                         cognateClass.cognateclasscitation_set.all()])
        for d in data:
            if d['source_id'] not in sourceIds:
                CognateClassCitation.objects.create(
                    cognate_class_id=target, **d)
    except CognateClass.DoesNotExist:
        pass  # Nothing to do


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0080_fix_cognateClassCitations')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0079_auto_20160629_1150')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
