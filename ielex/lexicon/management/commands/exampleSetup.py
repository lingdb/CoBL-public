# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.core.management import BaseCommand
from django.contrib.auth.models import User

from ielex.lexicon.models import LanguageList, \
    MeaningList, Language, Meaning, Lexeme, CognateClass, CognateJudgement


class Command(BaseCommand):

    help = "Creates some example data in the database." \
           "This makes it possible to experience the site without a dump."

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
            print('Creating example Meaning.')
            example = Meaning.objects.create(
                gloss=Meaning.DEFAULT,
                description='This meaning is essentially a placeholder.',
                notes='Note that this meaning is just a placeholder.',
                tooltip='Examples have tooltips, too!',
                exampleContext='Used in "This example".')
            mList = MeaningList.objects.get(name=MeaningList.DEFAULT)
            mList.append(example)

        if Language.objects.count() == 0:
            print('Creating example Language.')
            example = Language.objects.create(
                ascii_name=Language.DEFAULT,
                utf8_name=Language.DEFAULT,
                description='This language should not remain.')
            lList = LanguageList.objects.get(name=LanguageList.DEFAULT)
            lList.append(example)

        if Lexeme.objects.count() == 0:
            print('Creating example Lexeme.')
            Lexeme.objects.create(
                language=Language.objects.all()[0],
                meaning=Meaning.objects.all()[0],
                source_form='foo',
                phon_form='bar',
                gloss='baz',
                notes='The names "foo", "bar" and "baz" are placeholders. '
                      'See https://en.wikipedia.org/wiki/Foobar',
                phoneMic='foobar',
                transliteration='raboof'
            )

        if CognateClass.objects.count() == 0:
            print('Creating example CognateClass.')
            cc = CognateClass.objects.create(
                alias='A',
                notes='Example cognate class',
                name='exampleCcName',
                root_form='root_form',
                root_language='root_language',
                gloss_in_root_lang='foo'
            )
            CognateJudgement.objects.create(
                cognate_class=cc,
                lexeme=Lexeme.objects.all()[0]
            )

        if User.objects.filter(is_superuser=True).count() == 0:
            print('Creating login admin:admin.')
            User.objects.create_superuser(
                'admin', email='ab@c.de', password='admin')
