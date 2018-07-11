# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    Lexeme = apps.get_model("lexicon", "Lexeme")
    for l in Lexeme.objects.exclude(transliteration='').all():
        # The orthographic field is currently called source_form.
        # This will be renamed in a future migration.
        memo = l.transliteration
        l.transliteration = l.source_form
        l.source_form = memo
        l.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0131_auto_20161213_1124')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
