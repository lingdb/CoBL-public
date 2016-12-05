# -*- coding: utf-8 -*-
# Inspired by:
# https://github.com/lingdb/CoBL/issues/223#issuecomment-256815113
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    Language = apps.get_model("lexicon", "Language")
    hindi = Language.objects.get(ascii_name='Hindi')
    urdu = Language.objects.get(ascii_name='Urdu')
    Lexeme = apps.get_model("lexicon", "Lexeme")
    hindiMeaningLexemeMap = dict(
        Lexeme.objects.filter(
            language=hindi).values_list(
            'meaning_id', 'transliteration'))
    for lexeme in Lexeme.objects.filter(language=urdu).all():
        if lexeme.meaning_id in hindiMeaningLexemeMap:
            lexeme.transliteration = hindiMeaningLexemeMap[lexeme.meaning_id]
            lexeme.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0129_link_author_user')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
