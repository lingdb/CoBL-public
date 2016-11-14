# -*- coding: utf-8 -*-
# Inspired by:
# https://github.com/lingdb/CoBL/issues/223#issuecomment-256815113
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    Lexeme = apps.get_model("lexicon", "Lexeme")

    toRemove = Lexeme.objects.filter(meaning=None).values_list('id', flat=True)

    print('\nRemoving lexemes: %s' % ', '.join([str(r) for r in toRemove]))

    Lexeme.objects.filter(id__in=toRemove).delete()


def reverse_func(apps, schema_editor):
    print('Reverse of 0124_remove_lexemes_without_meaning')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0123_fill_meaning_examplecontext')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
