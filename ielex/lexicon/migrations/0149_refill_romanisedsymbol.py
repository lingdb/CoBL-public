# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    RomanisedSymbol = apps.get_model("lexicon", "RomanisedSymbol")
    RomanisedSymbol.objects.all().delete()
    approved = [b'a', b'\\u0101', b'\\u0103', b'\\xe1', b'\\xe0', b'\\xe2',
                b'\\xe5', b'\\u1e01', b'\\xe4', b'\\xe3', b'\\u0105',
                b'\\u0251', b'\\xe6', b'\\u01e3', b'e', b'\\u0113', b'\\u0115',
                b'\\xe9', b'\\xe8', b'\\xea', b'\\u011b', b'\\u0117', b'\\xeb',
                b'\\u1ebd', b'\\u0119', b'\\u1e17', b'\\u025c', b'\\u0259',
                b'\\u025b', b'i', b'\\u012b', b'\\u012d', b'\\xed', b'\\xec',
                b'\\xee', b'\\xef', b'\\u0129', b'\\u012f', b'\\u1e2f',
                b'\\u026a', b'\\u0268', b'y', b'\\u0233', b'\\xfd', b'\\u0177',
                b'\\u1e8f', b'\\xff', b'\\u1ef9', b'o', b'\\u014d', b'\\xf3',
                b'\\xf2', b'\\xf4', b'\\u1ecd', b'\\xf6', b'\\xf5', b'\\u01eb',
                b'\\u1e53', b'\\xf8', b'\\u0254', b'\\u0153', b'u', b'\\u016b',
                b'\\u016d', b'\\xfa', b'\\xf9', b'\\xfb', b'\\u01d4',
                b'\\u016f', b'\\xfc', b'\\u0169', b'\\u0173', b'\\u01d6',
                b'\\u01d8', b'\\u0289', b'\\u028a', b'\\u028c', b'w',
                b'\\u0175', b'r', b'\\u0155', b'\\u0159', b'\\u1e59',
                b'\\u1e5b', b'\\u0157', b'\\u0281', b'l', b'\\u013e',
                b'\\u1e37', b'\\u0142', b'\\u026b', b'\\u028e', b'm',
                b'\\u1e41', b'\\u1e43', b'n', b'\\u0144', b'\\u0148',
                b'\\u1e45', b'\\u1e47', b'\\xf1', b'\\u0146', b'\\u014b',
                b'\\u03b2', b'\\u0278', b'v', b'f', b'z', b'\\u017e',
                b'\\u017a', b'\\u017c', b'\\u1e93', b'\\u0292', b's',
                b'\\u015b', b'\\u015d', b'\\u0161', b'\\u1e61', b'\\u1e63',
                b'\\u015f', b'\\xdf', b'\\u017f', b'\\u1e9b', b'x', b'\\u03c7',
                b'h', b'\\u1e25', b'\\u1e2b', b'\\u1e96', b'\\u0195', b'b',
                b'p', b'\\u1e55', b'd', b'\\u010f', b'\\u1e0d', b'\\u0111',
                b'\\xf0', b't', b'\\u0165', b'\\u1e6d', b'\\u1e6f',
                b'\\u0288', b'\\u03b8', b'\\xfe', b'j', b'\\u01f0', b'c',
                b'\\u0107', b'\\u010d', b'\\u010b', b'\\xe7', b'g',
                b'\\u01f5', b'\\u01e7', b'\\u0121', b'\\u0123', b'\\u0261',
                b'\\u0263', b'k', b'\\u1e31', b'\\u0137', b'q', b'\\u044a',
                b'\\u044b', b', ', b'-', b'(', b')', b',', b"'", b'*', b'?',
                b'\\u2260', b'/', b'\\u02d0', b';', b'\\xb7', b'\\u2032',
                b'\\u2033']
    RomanisedSymbol.objects.bulk_create([
        RomanisedSymbol(symbol=a.decode('unicode_escape')) for a in approved
    ])


def reverse_func(apps, schema_editor):
    RomanisedSymbol = apps.get_model("lexicon", "RomanisedSymbol")
    RomanisedSymbol.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0148_fill_romanisedsymbol')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
