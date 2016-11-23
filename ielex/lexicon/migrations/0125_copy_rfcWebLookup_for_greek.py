# -*- coding: utf-8 -*-
# Inspired by:
# https://github.com/lingdb/CoBL/issues/223#issuecomment-256815113
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    Lexeme = apps.get_model("lexicon", "Lexeme")

    sourceLanguageId = 110
    targetLanguageId = 177

    meaningRfcWebMap = {}

    for lexeme in Lexeme.objects.filter(language_id=sourceLanguageId).all():
        meaningRfcWebMap[lexeme.meaning_id] = lexeme.rfcWebLookup1

    for lexeme in Lexeme.objects.filter(language_id=targetLanguageId).all():
        if lexeme.meaning_id in meaningRfcWebMap:
            lexeme.rfcWebLookup1 = meaningRfcWebMap[lexeme.meaning_id]
            lexeme.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0124_auto_20161114_2012')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
