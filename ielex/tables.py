# -*- coding: utf-8 -*-
import django_tables2 as tables

class SourcesTable(tables.Table):

    #Details	Name (author-year-letter)	Title	Year	Author	BibTeX type

    details = tables.Column() #link to full view? / open new frame below ? s. http://wals.info/refdb
    title = tables.Column()
    year = tables.Column()
    author = tables.Column()
    ENTRYTYPE = tables.Column()
    cognacy = tables.Column()#cognate judgment
    cogset = tables.Column() #cognate classification; rename: cog. set
    lexeme = tables.Column() #lexeme citation
    deprecated = tables.CheckBoxColumn() #tables.BooleanColumn()
    edit = tables.Column() #link to edit view? / open new frame below ? s. http://wals.info/refdb
    
    class Meta:
        attrs = {'class': 'paleblue'}
    
    def __init__(self, *args, **kwargs):
        super(SourcesTable, self).__init__(*args, **kwargs)

class CellClassColumn(tables.Column):
    def render(self, value):
        if value == None:
            return value
        value, clss = value
        self.attrs = {"td": {"class": clss}}
        return mark_safe(value)

class SourcesUpdateTable(tables.Table):

    citation_text = CellClassColumn()

    ENTRYTYPE = CellClassColumn()
    citation_text = CellClassColumn()
    author = CellClassColumn()
    year = CellClassColumn()
    title = CellClassColumn()
    booktitle = CellClassColumn()
    editor = CellClassColumn()
    pages = CellClassColumn()
    edition = CellClassColumn()
    journaltitle = CellClassColumn()
    location = CellClassColumn()
    link = CellClassColumn()
    note = CellClassColumn()
    number = CellClassColumn()
    series = CellClassColumn()
    volume = CellClassColumn()
    publisher = CellClassColumn()
    institution = CellClassColumn()
    chapter = CellClassColumn()
    howpublished = CellClassColumn()

    class Meta:
        attrs = {'class': 'paleblue'}
    
    def __init__(self, *args, **kwargs):
        super(SourcesUpdateTable, self).__init__(*args, **kwargs)
