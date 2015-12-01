# -*- coding: utf-8 -*-

import django_tables2 as tables
from ielex.lexicon.models import *



class LexemeTable(tables.Table):
    language = tables.Column(verbose_name="Language")
    meaning = tables.Column(verbose_name="Meaning")
    source_form = tables.Column(verbose_name="Source Form")
    phon_form = tables.Column(verbose_name="Phonological Form")
    gloss = tables.Column(verbose_name="Gloss")
    cognate_class = tables.Column(verbose_name="Cognate Class")
    number_cognate_coded = tables.Column(verbose_name="nCog")
    
    class Meta:
        model = Lexeme
        exclude = ['modified', '_order']
        # add class="paleblue" to <table> tag
        #attrs = {"class": "paleblue"}
