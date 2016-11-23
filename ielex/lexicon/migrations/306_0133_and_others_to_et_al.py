# -*- coding: utf-8 -*-
# Inspired by:
# https://github.com/lingdb/CoBL/issues/223#issuecomment-256815113
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):

    """
    Replace 'and others' with 'et al.' in Source
    author and editor fields.
    """

    from ielex.lexicon.models import Source
    for obj in Source.objects.all():
        if 'and others' in obj.author:
            obj.author = obj.author.replace('and others', 'et al.')
            obj.save()
        if 'and others' in obj.editor:
            obj.editor = obj.editor.replace('and others', 'et al.')
            obj.save()
        if 'and others' in obj.bookauthor:
            obj.bookauthor = obj.bookauthor.replace('and others', 'et al.')
            obj.save()
        if 'and others' in obj.editora:
            obj.editora = obj.editora.replace('and others', 'et al.')
            obj.save()


def reverse_func(apps, schema_editor):
    print('Reverse of 306_0133_and_others_to_et_al does nothing.')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0126_remove_languages_without_list')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
