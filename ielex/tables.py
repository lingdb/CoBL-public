# -*- coding: utf-8 -*-
import django_tables2 as tables
from django.utils.safestring import mark_safe

class CheckBoxColumnDeprecated(tables.CheckBoxColumn):
    @property
    def header(self):
        return u'☓'

    def render(self, value):
        return mark_safe('<input type="checkbox" name="deprecated"%s>'
                         % ({True: u' checked', False: ''}[value]))


class CheckBoxColumnTRS(tables.CheckBoxColumn):
    @property
    def header(self):
        return u'TRS'
    def render(self, value):
        return mark_safe('<input type="checkbox" name="TRS"%s>' \
                         %({True:u' checked', False:''}[value]))

class CellClassColumn(tables.Column):

    def render(self, value):
        if value in [None, '', u'']:
            self.attrs = {}
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
    author = tables.Column(empty_values=[])
    ENTRYTYPE = tables.Column()
    cognacy = tables.Column() # cognate judgment
    cogset = tables.Column() # cognate classification; rename: cog. set
    lexeme = tables.Column() # lexeme citation
    deprecated = CheckBoxColumnDeprecated()  # tables.BooleanColumn()
    TRS = CheckBoxColumnTRS()
    edit = tables.Column()  # link to edit view? / open new frame below ?

    class Meta:
        attrs = {'class': 'paleblue'}

    def __init__(self, *args, **kwargs):
        super(SourcesTable, self).__init__(*args, **kwargs)

    def render_author(self, value, record):
        if value == u'' and record['editor']:
            if record['editor']:
                if len(record['editor'].split(' and ')) > 1:
                    return '%s (eds.)' %(record['editor'])
                return '%s (ed.)' %(record['editor'])
        return value

    def queryset_link(self, value, record, name):
        if len(value)!=0:
            link = u"<a href='/sources/%s/%s'>%s</a>" %(record['pk'],
                                                       name,
                                                       len(value))
            return mark_safe(link)
        return str(len(value))

    def render_cognacy(self, value, record):
        return self.queryset_link(value, record, 'cognacy')

    def render_cogset(self, value, record):
        return self.queryset_link(value, record, 'cogset')
    
    def render_lexeme(self, value, record):
        return self.queryset_link(value, record, 'lexeme')

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
    #respect = CellClassColumn(empty_values=[])
    #deprecated = CellClassColumn(empty_values=[])
    #TRS = CellClassColumn(empty_values=[])

    class Meta:
        attrs = {'class': 'paleblue'}
        row_attrs = {
            'id': lambda record: record['pk']
        }

    def __init__(self, *args, **kwargs):
        super(SourcesUpdateTable, self).__init__(*args, **kwargs)
