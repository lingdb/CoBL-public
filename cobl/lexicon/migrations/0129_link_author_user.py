# -*- coding: utf-8 -*-
# Inspired by:
# https://github.com/lingdb/CoBL/issues/223#issuecomment-256815113
from __future__ import unicode_literals, print_function
from django.db import migrations

relations = [{"authorId": 22, "userId": 20},
             {"authorId": 1, "userId": 15},
             {"authorId": 21, "userId": 26},
             {"authorId": 28, "userId": 9},
             {"authorId": 9, "userId": 37},
             {"authorId": 7, "userId": 17},
             {"authorId": 23, "userId": 45},
             {"authorId": 20, "userId": 31},
             {"authorId": 8, "userId": 40},
             {"authorId": 2, "userId": 13},
             {"authorId": 3, "userId": 29},
             {"authorId": 16, "userId": 22},
             {"authorId": 11, "userId": 18},
             {"authorId": 24, "userId": 36},
             {"authorId": 5, "userId": 27},
             {"authorId": 18, "userId": 58},
             {"authorId": 12, "userId": 44},
             {"authorId": 6, "userId": 23},
             {"authorId": 14, "userId": 43},
             {"authorId": 17, "userId": 65},
             {"authorId": 25, "userId": 28},
             {"authorId": 10, "userId": 35},
             {"authorId": 4, "userId": 21},
             {"authorId": 19, "userId": 25},
             {"authorId": 26, "userId": 24},
             {"authorId": 27, "userId": 71},
             {"authorId": 15, "userId": 48}]


def forwards_func(apps, schema_editor):
    authorUserMap = {r['authorId']: r['userId'] for r in relations}
    Author = apps.get_model("lexicon", "Author")
    for author in Author.objects.filter(id__in=authorUserMap.keys()).all():
        author.user_id = authorUserMap[author.id]
        author.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0128_author_user')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
