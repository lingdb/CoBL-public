# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    '''
    Marking Lexemes as not_swadesh_term where appropriate.
    See https://github.com/lingdb/CoBL/issues/229
    '''
    # Models to work with:
    Lexeme = apps.get_model('lexicon', 'Lexeme')
    for lexeme in Lexeme.objects.all():
        reliabilities = set([lc.reliability for lc
                             in lexeme.lexemecitation_set.all()])
        if 'X' in reliabilities:
            if not lexeme.not_swadesh_term:
                lexeme.not_swadesh_term = True
                lexeme.save()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func '
          'of 0087_mark_excluded_lexemes_notSwh')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0086_add_LateVedic_to_current')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
