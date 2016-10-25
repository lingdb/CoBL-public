# -*- coding: utf-8 -*-
import django_tables2 as tables
from django.utils.safestring import mark_safe

class CheckBoxColumnWithName(tables.CheckBoxColumn):
    @property
    def header(self):
        return u'☓'
    def render(self, value):
        return mark_safe('<input type="checkbox" name="deprecated"%s>' \
                         %({True:u' checked', False:''}[value]))

class CellClassColumn(tables.Column):
    def render(self, value):
        if value is None:
            return value
        value, clss = value
        self.attrs = {"td": {"class": clss}}
        return mark_safe(value)

class SourcesTable(tables.Table):

    # Details	Name (author-year-letter)	Title	Year	Author	BibTeX type
    # see http://wals.info/refdb for related info
    
    details = tables.Column()  # link to full view? / open new frame below ?
    title = tables.Column()
    year = tables.Column()
    author = tables.Column()
    ENTRYTYPE = tables.Column()
    cognacy = tables.Column()  # cognate judgment
    cogset = tables.Column()  # cognate classification; rename: cog. set
    lexeme = tables.Column()  # lexeme citation
    deprecated = CheckBoxColumnWithName()  # tables.BooleanColumn()
    edit = tables.Column()  # link to edit view? / open new frame below ?

    class Meta:
        attrs = {'class': 'paleblue'}

    def __init__(self, *args, **kwargs):
        super(SourcesTable, self).__init__(*args, **kwargs)

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
