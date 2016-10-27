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
        if value in [None, '', u'']:
            self.attrs = {}
            return value
        value, clss = value
        self.attrs = {"td": {"class": clss}}
        return mark_safe(value)

class QueryColumn(tables.Column):
    def render(self, value):       
        value = len(value)
        return mark_safe(value)
    
class SourcesTable(tables.Table):

    # Details	Name (author-year-letter)	Title	Year	Author	BibTeX type
    # see http://wals.info/refdb for related info
    
    details = tables.Column()  # link to full view? / open new frame below ?
    title = tables.Column()
    year = tables.Column()
    author = tables.Column(empty_values=[])
    ENTRYTYPE = tables.Column()
    cognacy = QueryColumn()  # cognate judgment
    cogset = tables.Column()  # cognate classification; rename: cog. set
    lexeme = QueryColumn()  # lexeme citation
    deprecated = CheckBoxColumnWithName()  # tables.BooleanColumn()
    edit = tables.Column()  # link to edit view? / open new frame below ?

    class Meta:
        attrs = {'class': 'paleblue'}

    def __init__(self, *args, **kwargs):
        super(SourcesTable, self).__init__(*args, **kwargs)

    def render_author(self, value, record):
        if value == u'' and record['editor']:
            if record['editor']:
                if len(record['editor'].split(' and ')) > 1:
                    return '%s (edd.)' %(record['editor'])
                return '%s (ed.)' %(record['editor'])
        return value
        
        

class SourcesUpdateTable(tables.Table):

    citation_text = CellClassColumn(empty_values=[])

    ENTRYTYPE = CellClassColumn(empty_values=[])
    citation_text = CellClassColumn(empty_values=[])
    author = CellClassColumn(empty_values=[])
    year = CellClassColumn(empty_values=[])
    title = CellClassColumn(empty_values=[])
    booktitle = CellClassColumn(empty_values=[])
    editor = CellClassColumn(empty_values=[])
    pages = CellClassColumn(empty_values=[])
    edition = CellClassColumn(empty_values=[])
    journaltitle = CellClassColumn(empty_values=[])
    location = CellClassColumn(empty_values=[])
    link = CellClassColumn(empty_values=[])
    note = CellClassColumn(empty_values=[])
    number = CellClassColumn(empty_values=[])
    series = CellClassColumn(empty_values=[])
    volume = CellClassColumn(empty_values=[])
    publisher = CellClassColumn(empty_values=[])
    institution = CellClassColumn(empty_values=[])
    chapter = CellClassColumn(empty_values=[])
    isbn = CellClassColumn(empty_values=[])
    howpublished = CellClassColumn(empty_values=[])
    #deprecated = CellClassColumn(empty_values=[])

    class Meta:
        attrs = {'class': 'paleblue'}
        row_attrs = {
            'id': lambda record: record['pk']
        }
    def __init__(self, *args, **kwargs):
        super(SourcesUpdateTable, self).__init__(*args, **kwargs)
