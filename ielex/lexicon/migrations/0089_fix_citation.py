# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import Max

from datetime import datetime


def forwards_func(apps, schema_editor):
    '''
    I accidentially deleted a citation in production.
    This migration adds it again.
    '''
    # Models to work with:
    LexemeCitation = apps.get_model('lexicon', 'LexemeCitation')
    # Add missing citation.
    try:
        LexemeCitation.objects.get_or_create(
            lexeme_id=23793,
            source_id=58,
            pages='',
            reliability='A',
            comment='',
            modified=datetime(2016, 7, 21, 12, 55, 35, 300486))
    except Exception:
        pass


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0088_set_lexical_citation_rel_high')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
