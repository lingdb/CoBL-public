# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import json

from django.core.management import BaseCommand
from django.contrib.auth.models import User

from ielex.lexicon.models import LanguageList, \
    MeaningList, Language, Meaning, Lexeme, CognateClass, CognateJudgement


class Command(BaseCommand):

    help = "Creates some example data in the database." \
           "This makes it possible to experience the site without a dump."

    exampleMeanings = \
        './ielex/lexicon/management/commands/exampleMeanings.json'
    exampleLanguage = \
        './ielex/lexicon/management/commands/exampleLanguage.json'

    def handle(self, *args, **options):
        for name in [LanguageList.ALL, LanguageList.DEFAULT]:
            if not LanguageList.objects.filter(name=name).exists():
                print('Creating LanguageList %s.' % name)
                LanguageList.objects.create(name=name)

        for name in [MeaningList.ALL, MeaningList.DEFAULT]:
            if not MeaningList.objects.filter(name=name).exists():
                print('Creating MeaningList %s.' % name)
                MeaningList.objects.create(name=name)

        if Meaning.objects.count() == 0:
            print('Creating example Meanings.')
            with open(self.exampleMeanings) as f:
                mData = json.load(f)
            Meaning.objects.bulk_create([Meaning(**mArgs) for mArgs in mData])
            mList = MeaningList.objects.get(name=MeaningList.DEFAULT)
            for meaning in Meaning.objects.all():
                mList.append(meaning)

        if Language.objects.count() == 0:
            print('Creating example Language.')
            with open(self.exampleLanguage) as f:
                lData = json.load(f)
            language = Language.objects.create(**lData)
            lList = LanguageList.objects.get(name=LanguageList.DEFAULT)
            lList.append(language)

        if Lexeme.objects.count() == 0:
            print('Creating example Lexemes.')
            language = Language.objects.all()[0]
            mList = MeaningList.objects.get(name=MeaningList.DEFAULT)
            Lexeme.objects.bulk_create([
                Lexeme(meaning=m, language=language, _order=i)
                for i, m in enumerate(mList.meanings.all())])

        if User.objects.filter(is_superuser=True).count() == 0:
            print('Creating login admin:admin.')
            User.objects.create_superuser(
                'admin', email='ab@c.de', password='admin')
