# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ielex.lexicon.models as models

import json


def forwards_func(apps, schema_editor):
    Lexeme = apps.get_model('lexicon', 'Lexeme')
    Language = apps.get_model('lexicon', 'Language')
    with open('./ielex/lexicon/migrations/0028_weblinks_data.json') as f:
        data = json.load(f)
        print('0028_weblinks_data.json loaded.')
        print('Checking %s lexemes..' % len(data['lexemes']))
        for ldata in data['lexemes']:
            lexeme = Lexeme.objects.get(id=ldata['id'])
            changed = False
            for f in ['rfcWebLookup1', 'rfcWebLookup1']:
                if lexeme.data.get(f, '') == '':
                    if ldata.get(f, '') != '':
                        lexeme.data[f] = ldata[f]
                        changed = True
            if changed:
                lexeme.save()
                print('Changed lexeme: ', lexeme.id)
            else:
                print('Ignored lexeme: ', lexeme.id)
        print('Checking %s languages..' % len(data['languages']))
        for ldata in data['languages']:
            language = Language.objects.get(id=ldata['id'])
            changed = False
            for f in ['rfcWebPath1', 'rfcWebPath2']:
                if language.altname.get(f, '') == '':
                    if ldata.get(f, '') != '':
                        language.altname[f] = ldata[f]
                        changed = True
            if changed:
                language.save()
                print('Changed language:', language.id)
            else:
                print('Ignored language:', language.id)


def reverse_func(apps, schema_editor):
    print('Nothing to do for 0028_weblinks_data')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0027_auto_20160415_1345')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
