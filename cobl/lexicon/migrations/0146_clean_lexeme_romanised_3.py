# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    Lexeme = apps.get_model("lexicon", "Lexeme")
    replaceMap = {
        'λ': 'ʎ',
        'φ': 'ɸ'
        }
    for lexeme in Lexeme.objects.all():
        if len(set(replaceMap.keys()) & set(lexeme.romanised)):
            for k, v in replaceMap.items():
                lexeme.romanised = lexeme.romanised.replace(k, v)
            lexeme.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0145_fix_language_distributions')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
