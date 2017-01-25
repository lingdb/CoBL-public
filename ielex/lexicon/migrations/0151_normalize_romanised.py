# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import unicodedata
from django.db import migrations


def forwards_func(apps, schema_editor):
    Lexeme = apps.get_model("lexicon", "Lexeme")
    for lexeme in Lexeme.objects.all():
        newRomanised = unicodedata.normalize('NFC', lexeme.romanised)
        if newRomanised != lexeme.romanised:
            lexeme.romanised = newRomanised
            lexeme.save()

def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0150_clean_lexeme_romanised_4')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
