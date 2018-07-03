# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    '''
    BhojpuriNew is missing some lexemes present in Bhojpuri,
    so we move them there and leave Bhojpuri empty.
    '''
    # Models to work with:
    Language = apps.get_model('lexicon', 'Language')
    Lexeme = apps.get_model('lexicon', 'Lexeme')
    # Data to work with:
    try:
        source = Language.objects.get(ascii_name='Bhojpuri')
        target = Language.objects.get(ascii_name='BhojpuriNew')
        # Mapping meaning.id -> Lexeme
        mIdLexemeMap = {}
        for l in Lexeme.objects.filter(language=target).all():
            mIdLexemeMap[l.meaning_id] = l
        # Replacing lexemes in target:
        for l in Lexeme.objects.filter(language=source).all():
            mId = l.meaning_id
            if mId in mIdLexemeMap:
                mIdLexemeMap[mId].delete()
                l.language_id = target.id
                l.save()
    except Language.DoesNotExist:
        pass


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0090_remove_meaninglist_data')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
