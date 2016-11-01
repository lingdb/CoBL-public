# -*- coding: utf-8 -*-
# Inspired by:
# https://github.com/lingdb/CoBL/issues/223#issuecomment-256815113
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    Language = apps.get_model("lexicon", "Language")
    Meaning = apps.get_model("lexicon", "Meaning")
    Lexeme = apps.get_model("lexicon", "Lexeme")

    hindi = Language.objects.get(ascii_name='Hindi')
    urdu = Language.objects.get(ascii_name='Urdu')

    for meaning in Meaning.objects.all():
        hLexemes = Lexeme.objects.filter(language=hindi, meaning=meaning).all()
        uLexemes = Lexeme.objects.filter(language=urdu, meaning=meaning).all()

        if len(hLexemes) != 1 or len(uLexemes) != 1:
            continue

        hLex = hLexemes[0]
        uLex = uLexemes[0]

        if uLex.transliteration == '' and hLex.transliteration != '':
            uLex.transliteration = hLex.transliteration
            uLex.save()


def reverse_func(apps, schema_editor):
    print('Reverse of 0121_copy_hindi_transliteration_to_urdu does nothing.')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '306_0127_fix_issue_223')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
