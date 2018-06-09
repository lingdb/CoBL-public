# -*- coding: utf-8 -*-
from __future__ import division
import json
import os.path
import datetime
from collections import defaultdict
from string import ascii_uppercase, ascii_lowercase
import inspect
import codecs
import re

import reversion
from django.db import models, transaction
from django.db.models import Max
from django.core.urlresolvers import reverse
from django.utils.safestring import SafeString
from django.utils.encoding import python_2_unicode_compatible
from django.utils.http import urlquote
from django.http import HttpResponse
from django.utils.html import format_html
from django.db.utils import DataError, IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User
import bibtexparser
from bibtexparser.bibdatabase import BibDatabase

from ielex.utilities import two_by_two, compressedField
from ielex.lexicon.validators import suitable_for_url, standard_reserved_names

def disable_for_loaddata(signal_handler):
    """The signals to update denormalized data should not be called
    during loaddata management command (can raise an IntegrityError)"""
    def wrapper(*args, **kwargs):
        for fr in inspect.stack():
            if inspect.getmodulename(fr[1]) == 'loaddata':
                return
        signal_handler(*args, **kwargs)
    return wrapper
# end

TYPE_CHOICES = (
    ("P", "Publication"),
    ("U", "URL"),
    ("E", "Expert"))

RELIABILITY_CHOICES = (  # used by Citation classes
    # ("X", "Unclassified"), # change "X" to "" will force users to make
    ("A", "High"),         # a selection upon seeing this form
    ("B", "Good (e.g. should be double checked)"),
    ("C", "Doubtful"),
    ("L", "Loanword"),
    ("X", "Exclude (e.g. not the Swadesh term)"))

DISTRIBUTION_CHOICES = (  # used by Clade
    ("U", "Uniform"),
    ("N", "Normal"),
    ("L", "Log normal"),
    ("O", "Offset log normal"),
    ("_", "None"))

LANGUAGE_PROGRESS = (  # used by Languages
    (0, 'No data'),
    (1, 'Highly problematic'),
    (2, 'Limited revision, still unreliable'),
    (3, 'Revision underway'),
    (4, 'Revision complete'),
    (5, 'Second review complete'))

ENTRYTYPE_CHOICES = (  # used by Sources
    ('book', 'book'),
    ('article', 'article'),
    ('expert', 'expert'),
    ('online', 'online'),
    ('inbook', 'inbook'),
    ('misc', 'misc'))

YEAR_CHOICES = []  # used by Source
for r in reversed(range(1800, (datetime.datetime.now().year + 1))):
    YEAR_CHOICES.append((r, r))

SOURCE_TYPE_CHOICES = (  # used by Source
    ('article', 'article'),
    ('book', 'book'),
    ('booklet', 'booklet'),
    ('conference', 'conference'),
    ('inbook', 'in book'),
    ('incollection', 'in collection'),
    ('inproceedings', 'in proceedings'),
    ('manual', 'manual'),
    ('mastersthesis', 'masters thesis'),
    ('misc', 'misc'),
    ('phdthesis', 'phd thesis'),
    ('proceedings', 'proceedings'),
    ('unpublished', 'unpublished'),
)

PROPOSED_AS_COGNATE_TO_SCALE = (  # Used by CognateClass
    (0, '1/6=small minority view'),
    (1, '2/6=sig. minority view'),
    (2, '3/6=50/50 balance'),
    (3, '4/6=small majority view'),
    (4, '5/6=large majority view'))

NEXUS_DIALECT_CHOICES = (
    ("BP", "BayesPhylogenies"),
    ("NN", "NeighborNet"),
    ("MB", "MrBayes"))

# http://south.aeracode.org/docs/customfields.html#extending-introspection
# add_introspection_rules([], ["^ielex\.lexicon\.models\.CharNullField"])


class CharNullField(models.CharField):
    """CharField that stores NULL but returns ''
    This is important for uniqueness checks where multiple null values
    are allowed (following ANSI SQL standard). For example, if
    CognateClass objects have an explicit name, it must be unique, but
    having a name is optional."""

    def to_python(self, value):
        if isinstance(value, models.CharField):
            return value
        if value is None:
            return ""
        return value

    def get_prep_value(self, value):
        # this was get_db_prep_value, but that is for database specific things
        if value == "":
            return None
        return value


class AbstractTimestamped(models.Model):
    """
    This model is created as a mixin that adds
    fields and functionality to other models.
    It aims to solve the problems observed in #111.
    """
    lastTouched = models.DateTimeField(auto_now=True, blank=True)
    lastEditedBy = models.CharField(max_length=32, default="unknown")

    class Meta:
        abstract = True

    def timestampedFields(self):
        """
        timestampedFields shall be overwritten by children
        and return a set of field names that are
        allowed to be considered by the AbstractTimestamped
        {isChanged,setDelta} methods.
        """
        return set()

    def isChanged(self, **vdict):
        """
        Returns True iff any of the fields in vdict
        that are also specified in timestampedFields
        and are one of the models fields stored in the db
        has changed. Returns False otherwise.
        """
        tFields = self.timestampedFields()

        for f in self._meta.fields:
            if f.name in tFields and f.name in vdict:
                if getattr(self, f.name) != vdict[f.name]:
                    return True
        return False

    def setDelta(self, request=None, **vdict):
        """
        setDelta allows to alter a model with a dict of field names.
        vdict must have a lastTouched field
        that is the same as the current lastTouched.
        If no lastTouched field is given or lastTouched is older than
        the current value setDelta will return a dict
        listing the current differences to the model.
        If no problem arises from lastTouched
        setDelta will check for a current user login to update
        the lastEditedBy field and will then proceed updating
        the model.
        The request parameter is used to update lastEditedBy.
        It's possible to omit the request so that setDelta
        can be used independent of it.
        """
        # Guarding for correct lastTouched:
        if 'lastTouched' not in vdict:
            return self.getDelta(**vdict)
        if not self.checkTime(vdict['lastTouched']):
            return self.getDelta(**vdict)
        # Updating lastEditedBy:
        self.bump(request)
        # Writing delta:
        tFields = self.timestampedFields()
        for f in self._meta.fields:
            if f.name in tFields and f.name in vdict:
                setattr(self, f.name, vdict[f.name])

    def getDelta(self, **vdict):
        """
        Produces a dict that lists all the fields of vdict
        that are valid fields for self in the sense that
        they are mentioned in timestampedFields and
        that are different than the current entries.
        """
        tFields = self.timestampedFields()
        return {k: vdict[k] for k in vdict
                if k in tFields and
                vdict[k] != getattr(self, k)}

    def checkTime(self, t):
        """
        Returns true if the given datetime t is
        less then a second different from the current
        lastTouched value.
        """
        if self.lastTouched is None:
            return True

        def make_aware(time):
            if time.tzinfo is None:
                return timezone.make_aware(
                    time, timezone.get_current_timezone())
            return time

        self.lastTouched = make_aware(self.lastTouched)
        t = make_aware(t)
        return abs(t - self.lastTouched).seconds == 0

    def bump(self, request, t=None):
        """
        Updates the lastEditedBy field of an AbstractTimestamped.
        If a t :: datetime is given, bump uses checkTime on that.
        """
        if t is not None and not self.checkTime(t):
            raise Exception('Refusing bump because of failed checkTime.')
        if request is not None:
            if not request.user.is_authenticated:
                raise Exception('Refusing bump with unauthenticated user.')
            self.lastEditedBy = ' '.join([request.user.first_name,
                                          request.user.last_name])

    def toDict(self):
        """
        Returns a dict carrying the timestampedFields.
        """
        return {k: getattr(self, k) for k in self.timestampedFields()}


class AbstractDistribution(models.Model):
    """
    This model describes the types of distributions
    we use for clades and languages.
    """
    # Distribution type used:
    distribution = models.CharField(
        max_length=1, choices=DISTRIBUTION_CHOICES, default="_")
    # For [offset] log normal distribution:
    logNormalOffset = models.IntegerField(null=True)
    logNormalMean = models.IntegerField(null=True)
    logNormalStDev = models.DecimalField(
        null=True, max_digits=19, decimal_places=10)
    # For normal distribution:
    normalMean = models.IntegerField(null=True)
    normalStDev = models.IntegerField(null=True)
    # For uniform distribution:
    uniformUpper = models.IntegerField(null=True)
    uniformLower = models.IntegerField(null=True)

    class Meta:
        abstract = True

    def timestampedFields(self):
        return set(['distribution', 'logNormalOffset', 'logNormalMean',
                    'logNormalStDev', 'normalMean', 'normalStDev',
                    'uniformUpper', 'uniformLower'])


@reversion.register
class Source(models.Model):

    """
    Used for bibliographical references.
    """
    # OLD FIELDS:
    citation_text = models.TextField()
    description = models.TextField(blank=True)  # keep for now
    # in fact, when was added; keep for now
    modified = models.DateTimeField(auto_now=True)

    # NEW FIELDS:
    ENTRYTYPE = models.CharField(max_length=32, choices=ENTRYTYPE_CHOICES)
    author = models.CharField(max_length=128, blank=True)
    authortype = models.CharField(max_length=16, blank=True)
    year = models.CharField(max_length=16, blank=True,
                            null=True)  # choices=YEAR_CHOICES
    title = models.TextField(blank=True)
    subtitle = models.TextField(blank=True)
    booktitle = models.TextField(blank=True)
    booksubtitle = models.TextField(blank=True)
    bookauthor = models.CharField(max_length=128, blank=True)
    editor = models.CharField(max_length=128, blank=True)
    editora = models.CharField(max_length=128, blank=True)
    editortype = models.CharField(max_length=16, blank=True)
    editoratype = models.CharField(max_length=16, blank=True)
    pages = models.CharField(max_length=32, blank=True)
    part = models.CharField(max_length=128, blank=True)
    edition = models.CharField(max_length=128, blank=True)
    journaltitle = models.CharField(max_length=128, blank=True)
    location = models.CharField(max_length=128, blank=True)
    link = models.URLField(blank=True)
    note = models.TextField(blank=True)
    number = models.CharField(max_length=128, blank=True)
    series = models.CharField(max_length=128, blank=True)
    volume = models.CharField(max_length=128, blank=True)
    publisher = models.CharField(max_length=128, blank=True)
    institution = models.CharField(max_length=128, blank=True)
    chapter = models.TextField(blank=True)
    howpublished = models.TextField(blank=True)
    shorthand = models.CharField(max_length=128, blank=True)
    isbn = models.CharField(max_length=32, blank=True)

    # status:
    deprecated = models.BooleanField(default=False)

    """
    Traditional reference source (dated).
    S. https://github.com/lingdb/CoBL/issues/332#issuecomment-255142824
    """
    TRS = models.BooleanField(
        default=False, help_text="""Traditional reference source (dated).""")

    """
    A brief summary of the nature of the source and how its utility
    (or otherwise) is general perceived nowadays within Indo-European studies.
    S. https://github.com/lingdb/CoBL/issues/332#issuecomment-255142824
    """
    respect = models.TextField(
        blank=True,
        help_text="""A brief summary of the nature """
                  """of the source its utility.""")

    bibtex_attr_lst = ['citation_text', 'ENTRYTYPE', 'author',
                       'year', 'title', 'booktitle',
                       'booksubtitle', 'bookauthor', 'editor',
                       'editortype', 'editora',
                       'pages', 'part', 'edition',
                       'journaltitle', 'location', 'link',
                       'note', 'number', 'series', 'volume',
                       'publisher', 'institution', 'chapter',
                       'howpublished', 'shorthand', 'isbn',
                      ]
    cobl_attr_lst = ['authortype', 'editortype', 'editoratype',
                     'deprecated', 'TRS', 'respect']
    source_attr_lst = bibtex_attr_lst + cobl_attr_lst

    class Meta:
        ordering = ['shorthand']

    def __str__(self):
        return self.shorthand

    @property
    def name_short(self):
        author = ''
        names = []
        if self.author != '':
            names = self.author.split(' and ')
        elif self.editor != '':
            names = self.editor.split(' and ')
        if names:
            author = names[0].split(', ')[0]
            if len(names) > 1:
                author = u'%s et al.' % (author)
        year = self.year  # .replace('--', '–').replace('/', '–')
        short_name = u'%s %s' % (author, year)
        if short_name in [u' ']:
            if self.ENTRYTYPE == 'online':
                short_name = self.link
        return short_name

    @property
    def name_short_with_unique_siglum(self):
        name = self.name_short
        siglum = ''
        counter = {'before': 0, 'after': 0}
        if name not in [u'', u' ']:
            query = self.__class__.objects.all().exclude(
                pk=self.pk).filter(year=self.year)
            for obj in query:
                if obj.name_short == name:
                    if obj.pk < self.pk:
                        counter['before'] += 1
                    else:
                        counter['after'] += 1
        if counter['before'] > 0:
            siglum = chr(counter['before'] + ord('a'))
        elif counter['after'] > 0:
            siglum = 'a'
        return u'%s%s' % (name, siglum)

    def get_absolute_url(self):
        return "/sources/%s/" % self.id

    @property
    def edit_link(self):
        return format_html(
            '<a href="%sedit" title="Edit this source" '
            'class="pull-right">Edit</a>' % (self.get_absolute_url()))

    @property
    def bibtex_dictionary(self):
        bibtex_dictionary = {}
        bibtex_dictionary['ID'] = str(self.pk)
        for key in self.bibtex_attr_lst:
            if str(getattr(self, key)) != u'':
                bibtex_dictionary[key] = str(getattr(self, key))
        return bibtex_dictionary

    @property
    def bibtex(self):
        db = BibDatabase()
        db.entries.append(self.bibtex_dictionary)
        return bibtexparser.dumps(db)

    @property
    def COinS(self):
        bibtex_rft_dict = {'ENTRYTYPE': 'genre', 'title': 'title',
                           'year': 'date', 'author': 'au',
                           'booktitle': 'btitle', 'publisher': 'pub',
                           'journaltitle': 'jtitle', 'location': 'place',
                           'chapter': 'atitle', 'pages': 'pages',
                           'series': 'series', 'volume': 'volume',
                           'institution': 'aucorp', 'isbn': 'isbn',
                           'number': 'issue', 'part': 'part',
                           'edition': 'edition', 'editor': 'editor'}
        rft_attrs_lst = []
        rft_val_dict = {'book': 'book', 'article': 'article',
                        'expert': 'document', 'online': 'webpage',
                        'inbook': 'bookitem', 'misc': 'document'}
        for key in bibtex_rft_dict:
            try:
                typ = rft_val_dict[self.ENTRYTYPE]
            except KeyError:
                typ = self.ENTRYTYPE
            rft_attrs_lst.append('rft_val_fmt=info:ofi/fmt:kev:mtx:%s'
                                 % (typ))
            rft_attrs_lst.append('rfr_id=%s' % (self.pk))
            rft_attrs_lst.append('rft.identifier=%s'
                                 % (self.get_absolute_url()))
            if getattr(self, key):
                rft_attrs_lst.append('rft.%s=%s' % (
                    bibtex_rft_dict[key],
                    urlquote(getattr(self, key))
                ))

        return '<span class="Z3988" ' \
               'title="ctx_ver=Z39.88-2004&%s" />' \
               % ('&'.join(rft_attrs_lst))

    def populate_from_bibtex(self, bibtex_dict):
        for key in bibtex_dict.keys():
            if key not in ['ID', 'date']:
                setattr(self, key, bibtex_dict[key])
        try:
            self.save()
        except DataError as e:
            print(e, bibtex_dict)

    def merge_with(self, pk):
        obj = self.__class__.objects.get(pk=pk)
        for cj_obj in obj.cognacy:
            try:
                with transaction.atomic():
                    cj_obj.source = self
                    cj_obj.save()
            except IntegrityError:
                pass
        for cc_obj in obj.cogset:
            try:
                cc_obj.source = self
                cc_obj.save()
            except IntegrityError:
                pass
        for lc_obj in obj.lexeme:
            try:
                with transaction.atomic():
                    lc_obj.source = self
                    lc_obj.save()
            except IntegrityError:
                pass
        obj.delete()

    def timestampedFields(self):
        return set(source_attr_lst)


@reversion.register
class SndComp(AbstractTimestamped):
    """
    Introduced for #153.
    This model tracks the correspondence of clades to sndComp sets.
    """
    lgSetName = models.TextField(blank=True, unique=True)
    # Corresponding to SndComp fields:
    lv0 = models.IntegerField(default=0, null=False)
    lv1 = models.IntegerField(default=0, null=False)
    lv2 = models.IntegerField(default=0, null=False)
    lv3 = models.IntegerField(default=0, null=False)
    # For linking against clades:
    cladeLevel0 = models.IntegerField(default=0)
    cladeLevel1 = models.IntegerField(default=0)
    cladeLevel2 = models.IntegerField(default=0)
    cladeLevel3 = models.IntegerField(default=0)

    def getClade(self):
        """
        This method tries to find the clade closest to a SndComp.
        @return clade :: Clade | None
        """

        wanted = [('cladeLevel0', self.cladeLevel0),
                  ('cladeLevel1', self.cladeLevel1),
                  ('cladeLevel2', self.cladeLevel2),
                  ('cladeLevel3', self.cladeLevel3)]

        for i in range(len(wanted), 0, -1):
            try:
                d = dict(wanted[:i])
                return Clade.objects.get(**d)
            except Exception:
                pass

        return None

    class Meta:
        ordering = ["lv0", "lv1", "lv2", "lv3"]

    def timestampedFields(self):
        return set(['lgSetName', 'lv0', 'lv1', 'lv2', 'lv3', 'cladeLevel0',
                    'cladeLevel1', 'cladeLevel2', 'cladeLevel3'])

    def deltaReport(self, **kwargs):
        return 'Could not update SndComp: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.id, kwargs, self.lastEditedBy, self.lastTouched)


@reversion.register
class Clade(AbstractTimestamped, AbstractDistribution):
    """
    This model was added for #153
    and shall be used to track clade constraints.
    """
    cladeLevel0 = models.IntegerField(default=0, null=False)
    cladeLevel1 = models.IntegerField(default=0, null=False)
    cladeLevel2 = models.IntegerField(default=0, null=False)
    cladeLevel3 = models.IntegerField(default=0, null=False)
    cladeName = models.TextField(blank=True, unique=True)
    hexColor = models.CharField(max_length=6, blank=True)
    shortName = models.CharField(max_length=5, blank=True)
    # Level names:
    level0Name = models.CharField(max_length=64, blank=True)
    level1Name = models.CharField(max_length=64, blank=True)
    level2Name = models.CharField(max_length=64, blank=True)
    level3Name = models.CharField(max_length=64, blank=True)
    # Will decide wether to include this in the export:
    export = models.BooleanField(default=0)
    # Will decide wether to include the date in the export:
    exportDate = models.BooleanField(default=0)
    # No spaces allowed in the following:
    taxonsetName = models.CharField(max_length=100, blank=True)
    # Latest plausible date divergence had not yet begun:
    atMost = models.IntegerField(null=True)
    # Earliest plausible date divergence could have begun by:
    atLeast = models.IntegerField(null=True)

    def __str__(self):
        return self.cladeName

    class Meta:
        ordering = ['cladeLevel0',
                    'cladeLevel1',
                    'cladeLevel2',
                    'cladeLevel3']

    @property
    def languageIds(self):
        return [cl.language_id for cl in self.languageclade_set]

    def timestampedFields(self):
        fs = set(['cladeName', 'shortName', 'hexColor', 'export',
                  'exportDate', 'taxonsetName', 'atMost', 'atLeast',
                  'cladeLevel0', 'cladeLevel1', 'cladeLevel2', 'cladeLevel3',
                  'level0Name', 'level1Name', 'level2Name', 'level3Name'])
        return fs | AbstractDistribution.timestampedFields(self)

    def deltaReport(self, **kwargs):
        return 'Could not update Clade: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.id, kwargs, self.lastEditedBy, self.lastTouched)

    # Memo for computeCognateClassConnections:
    _cognateClassConnections = []  # [Boolean]

    def computeCognateClassConnections(self, cognateclasses, languageList):
        # Reset memo:
        self._cognateClassConnections = []
        # lIds that warrant a connection:
        clIds = set(self.languageclade_set.filter(
            language__languagelistorder__language_list=languageList
        ).values_list('language_id', flat=True))
        # Fill memo with entries for given cognateclasses:
        for cc in cognateclasses:
            lIds = set(cc.lexeme_set.filter(
                not_swadesh_term=False).values_list(
                    'language_id', flat=True))
            self._cognateClassConnections.append(bool(clIds & lIds))

    def connectsToNextCognateClass(self):
        # :: self._cognateClassConnections[0] | False
        if self._cognateClassConnections:
            return self._cognateClassConnections.pop(0)
        return False

    @property
    def cladePath(self):
        return ','.join([str(l) for l in [self.cladeLevel0,
                                          self.cladeLevel1,
                                          self.cladeLevel2,
                                          self.cladeLevel3] if l != 0])

    def queryChildren(self):
        # Used in stats236.py
        subSelection = [('cladeLevel0', self.cladeLevel0),
                        ('cladeLevel1', self.cladeLevel1),
                        ('cladeLevel2', self.cladeLevel2),
                        ('cladeLevel3', self.cladeLevel3)]
        subSelection = {k: v for k, v in subSelection if v != 0}
        return Clade.objects.filter(**subSelection).exclude(id=self.id)


def getCladeFromLanguageIds(languageIds):
    '''
    getCladeFromLanguageIds :: Clade | None
    Tries to find the most specific clade that contains all given languageIds.
    If no such clade can be found returns None.
    '''
    # Calculating clade
    lIdToCladeOrders = defaultdict(dict)  # lId -> cId -> cladesOrder
    for lId, cladeId, cladesOrder in LanguageClade.objects.filter(
            language_id__in=languageIds).values_list(
                'language_id', 'clade_id', 'cladesOrder'):
        lIdToCladeOrders[lId][cladeId] = cladesOrder
    # Intersecting clades:
    cladeIdOrderMap = None
    for _, newcIdOrderMap in lIdToCladeOrders.items():
        if cladeIdOrderMap is None:
            cladeIdOrderMap = newcIdOrderMap
        else:
            intersection = newcIdOrderMap.keys() & \
                cladeIdOrderMap.keys()
            cladeIdOrderMap.update(newcIdOrderMap)
            cladeIdOrderMap = {k: v for k, v in cladeIdOrderMap.items()
                               if k in intersection}
    # Retrieving the Clade:
    if cladeIdOrderMap:
        # https://stackoverflow.com/a/3282904/448591
        cId = min(cladeIdOrderMap, key=cladeIdOrderMap.get)
        return Clade.objects.get(id=cId)
    return None


@reversion.register
class Language(AbstractTimestamped, AbstractDistribution):
    DEFAULT = 'AncientGreek'

    iso_code = models.CharField(max_length=3, blank=True)
    ascii_name = models.CharField(
        max_length=128, unique=True, validators=[suitable_for_url])
    utf8_name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True, null=True)
    clades = models.ManyToManyField(Clade, through="LanguageClade", blank=True)
    earliestTimeDepthBound = models.IntegerField(null=True)  # #128
    latestTimeDepthBound = models.IntegerField(null=True)  # #128
    progress = models.IntegerField(default=0, choices=LANGUAGE_PROGRESS)
    # Former JSON fields:
    glottocode = models.CharField(max_length=8, null=True)
    variety = models.CharField(max_length=64, null=True)
    soundcompcode = models.CharField(max_length=64, null=True)
    level0 = models.IntegerField(default=0, null=True)
    level1 = models.IntegerField(default=0, null=True)
    level2 = models.IntegerField(default=0, null=True)
    level3 = models.IntegerField(default=0, null=True)
    foss_stat = models.BooleanField(default=0)
    low_stat = models.BooleanField(default=0)
    representative = models.BooleanField(default=0)
    rfcWebPath1 = models.TextField(blank=True, null=True)
    rfcWebPath2 = models.TextField(blank=True, null=True)
    # to be replaced with ForeignKey, see below
    author = models.CharField(max_length=256, null=True)
    # to be replaced with ForeignKey, see below
    reviewer = models.CharField(max_length=256, null=True)
    # Added for #153:
    sortRankInClade = models.IntegerField(default=0, null=False)
    # Backup of level entries that still correspond to SndComp levels:
    sndCompLevel0 = models.IntegerField(default=0, null=True)
    sndCompLevel1 = models.IntegerField(default=0, null=True)
    sndCompLevel2 = models.IntegerField(default=0, null=True)
    sndCompLevel3 = models.IntegerField(default=0, null=True)
    # Added for #209:
    entryTimeframe = models.TextField(blank=True, null=True)
    # Added for #218:
    originalAsciiName = models.CharField(
        max_length=128, validators=[suitable_for_url])
    historical = models.BooleanField(default=0)
    # Added for #401
    fragmentary = models.BooleanField(default=0)
    # Added for #300:
    notInExport = models.BooleanField(default=1)
    # Lat/Lon:
    latitude = models.DecimalField(
        null=True, max_digits=19, decimal_places=10)
    longitude = models.DecimalField(
        null=True, max_digits=19, decimal_places=10)
    # Added for #217:
    exampleLanguage = models.BooleanField(default=0)
    # author = models.ForeignKey(author, related_name="author", null=True)
    # reviewer = models.ForeignKey(author, related_name="reviewer", null=True)

    #Added for #424 2
    nativeScriptIsRtl = models.BooleanField(default=0)

    def get_absolute_url(self):
        return "/language/%s/" % self.ascii_name

    def __str__(self):
        return self.utf8_name

    class Meta:
        ordering = ['level0',
                    'level1',
                    'level2',
                    'level3',
                    'sortRankInClade']

    def getCsvRow(self, *fields):
        """
        @return row :: [str]
        """
        fieldSet = self.timestampedFields()

        row = []
        for f in fields:
            if f in fieldSet:
                row.append(str(getattr(self, f)))
        return row

    _computeCounts = {}  # Memo for computeCounts

    def computeCounts(self, meaningList=None, exportMethod=''):
        """
        computeCounts calculates some of the properties of this model.
        It uses self._computeCounts for memoization.
        """
        if not self._computeCounts:
            # Making sure we've got a meaningList:
            if meaningList is None:
                meaningList = MeaningList.objects.get(name=MeaningList.ALL)

            if exportMethod=='onlyexport':
                meaningIdSet = set([m.id for m in meaningList.meanings.filter(exclude=False)])
            elif exportMethod=='onlynotexport':
                meaningIdSet = set([m.id for m in meaningList.meanings.filter(exclude=True)])
            else:
                meaningIdSet = set([m.id for m in meaningList.meanings.all()])

            setattr(meaningList, '_language__computeCounts', meaningIdSet)

            lexemeMeaningIdSet = set([l.meaning_id for l
                                      in self.lexeme_set.all()])
            lexemeMeaningIdSetOnlySwadesh = set([l.meaning_id for l
                                      in self.lexeme_set.filter(not_swadesh_term=False)])
            # Computing base counts:
            mergedIdSet = meaningIdSet & lexemeMeaningIdSet
            meaningCount = len(mergedIdSet)
            mergedIdOnlySwadeshSet = meaningIdSet & lexemeMeaningIdSetOnlySwadesh
            meaningCountNotSwadeshTerm = meaningCount-len(mergedIdSet & mergedIdOnlySwadeshSet)

            meaningsMarkedAsNotSwadeshList = ''

            if meaningCountNotSwadeshTerm == 1:
                meaningsMarkedAsNotSwadeshList = Meaning.objects.get(
                    id=list(mergedIdSet ^ mergedIdOnlySwadeshSet)[0]).gloss
            elif meaningCountNotSwadeshTerm > 1 and meaningCountNotSwadeshTerm < 21:
                meaningsMarkedAsNotSwadeshList = ", ".join(Meaning.objects.filter(
                    id__in=tuple(mergedIdSet ^ mergedIdOnlySwadeshSet)).order_by(
                        'gloss').values_list('gloss', flat=True))
            elif meaningCountNotSwadeshTerm > 20:
                meaningsMarkedAsNotSwadeshList = ", ".join(Meaning.objects.filter(
                    id__in=tuple(mergedIdSet ^ mergedIdOnlySwadeshSet)).order_by(
                        'gloss')[:20].values_list('gloss', flat=True))
                meaningsMarkedAsNotSwadeshList += ", ..."

            lexemes = self.lexeme_set.filter(meaning__in=mergedIdSet)
            entryCount = len(lexemes)
            nonLexCount = len(lexemes.filter(not_swadesh_term=True))

            # Computing dependant counts:
            lexCount = entryCount - nonLexCount
            excessCount = lexCount - meaningCount + meaningCountNotSwadeshTerm
            # Computing blanks (#398 1)
            targetLexemes = lexemes.filter(not_swadesh_term=False)
            blankCount = len(targetLexemes.filter(romanised=u''))
            # Computing blanks (#398 2)
            noPhoneMicCount = len(targetLexemes.filter(phoneMic=u''))
            # Computing blanks (#398 3)
            noPhoneTicCount = len(targetLexemes.filter(phon_form=u''))
            if lexCount == 0:
                # Computing blanks (#398 4)
                dicLinkCount = 0
                # Computing blanks (#398 5)
                haveCitCount = 0
            else:
                # Computing blanks (#398 4)
                dicLinkCount = int(len(targetLexemes.exclude(rfcWebLookup1=u''))/lexCount*100)
                # Computing blanks (#398 5)
                haveCitCount = int(len(set(l.lexeme_id for l in 
                    LexemeCitation.objects.filter(lexeme_id__in=targetLexemes)))/lexCount*100)
            # Computing unassigned count (#255):
            unassignedCount = len(targetLexemes.filter(cognate_class=None))

            # Cognate classes to iterate:
            ccs = CognateClass.objects.filter(
                lexeme__language_id=self.id,
                lexeme__meaning_id__in=meaningIdSet).order_by(
                    'id').distinct('id').all()
            # Setup to count stuff:
            cogLoanCount = 0
            cogParallelLoanCount = 0
            cogIdeophonicCount = 0
            cogPllDerivationCount = 0
            cogDubSetCount = 0
            # Iterating ccs to calculate counts:
            for cc in ccs:
                if cc.loanword:
                    cogLoanCount += 1
                if cc.parallelLoanEvent:
                    cogParallelLoanCount += 1
                if cc.ideophonic:
                    cogIdeophonicCount += 1
                if cc.parallelDerivation:
                    cogPllDerivationCount += 1
                if cc.dubiousSet:
                    cogDubSetCount += 1

            # Setting counts:
            self._computeCounts = {
                'meaningCount': meaningCount,
                'entryCount': entryCount,
                'nonLexCount': nonLexCount,
                'lexCount': lexCount,
                'excessCount': excessCount,
                'unassignedCount': unassignedCount,
                'orphansCount': meaningCountNotSwadeshTerm,
                'orphansList': meaningsMarkedAsNotSwadeshList,
                'cogLoanCount': cogLoanCount,
                'cogIdeophonicCount': cogIdeophonicCount,
                'cogPllDerivationCount': cogPllDerivationCount,
                'cogDubSetCount': cogDubSetCount,
                'blankCount': blankCount,
                'noPhoneTicCount': noPhoneTicCount,
                'dicLinkCount': dicLinkCount,
                'haveCitCount': haveCitCount,
                'noPhoneMicCount': noPhoneMicCount,
                'cogParallelLoanCount': cogParallelLoanCount}
        return self._computeCounts

    def cladeByOrder(self, order):
        try:
            for lc in self.languageclade_set.all():
                if lc.cladesOrder == order:
                    # Iterating clades is faster than querying db.
                    for c in self.clades.all():
                        if c.id == lc.clade_id:
                            return c
        except:
            return None

    def cladePropertyByOrder(self, order, p, fallback):
        c = self.cladeByOrder(order)
        if c is None:
            return fallback
        return getattr(c, p, fallback)

    @property
    def meaningCount(self):
        return self.computeCounts()['meaningCount']

    @property
    def orphansCount(self):
        return self.computeCounts()['orphansCount']

    @property
    def blankCount(self):
        return self.computeCounts()['blankCount']

    @property
    def noPhoneMicCount(self):
        return self.computeCounts()['noPhoneMicCount']

    @property
    def noPhoneTicCount(self):
        return self.computeCounts()['noPhoneTicCount']

    @property
    def dicLinkCount(self):
        return self.computeCounts()['dicLinkCount']

    @property
    def haveCitCount(self):
        return self.computeCounts()['haveCitCount']

    @property
    def cogLoanCount(self):
        return self.computeCounts()['cogLoanCount']

    @property
    def cogParallelLoanCount(self):
        return self.computeCounts()['cogParallelLoanCount']

    @property
    def cogIdeophonicCount(self):
        return self.computeCounts()['cogIdeophonicCount']

    @property
    def cogPllDerivationCount(self):
        return self.computeCounts()['cogPllDerivationCount']

    @property
    def cogDubSetCount(self):
        return self.computeCounts()['cogDubSetCount']

    @property
    def orphansList(self):
        return self.computeCounts()['orphansList']

    @property
    def entryCount(self):
        return self.computeCounts()['entryCount']

    @property
    def nonLexCount(self):
        return self.computeCounts()['nonLexCount']

    @property
    def lexCount(self):
        return self.computeCounts()['lexCount']

    @property
    def excessCount(self):
        return self.computeCounts()['excessCount']

    @property
    def unassignedCount(self):
        return self.computeCounts()['unassignedCount']

    @property
    def level0Tooltip(self):
        return self.cladePropertyByOrder(3, 'cladeName', '')

    @property
    def level1Tooltip(self):
        return self.cladePropertyByOrder(2, 'cladeName', '')

    @property
    def level2Tooltip(self):
        return self.cladePropertyByOrder(1, 'cladeName', '')

    @property
    def level3Tooltip(self):
        return self.cladePropertyByOrder(0, 'cladeName', '')

    @property
    def level0Color(self):
        return self.cladePropertyByOrder(3, 'hexColor', '777777')

    @property
    def level1Color(self):
        return self.cladePropertyByOrder(2, 'hexColor', '777777')

    @property
    def level2Color(self):
        return self.cladePropertyByOrder(1, 'hexColor', '777777')

    @property
    def level3Color(self):
        return self.cladePropertyByOrder(0, 'hexColor', '777777')

    @property
    def hexColor(self):
        for c in reversed(self.clades.all()):
            if c is not None:
                if c.hexColor != '':
                    return c.hexColor
        return '777777'

    @property
    def cladePath(self):
        return ','.join([str(self.level0),
                         str(self.level1),
                         str(self.level2),
                         str(self.level3)])

    def timestampedFields(self):
        fs = set(['iso_code', 'ascii_name', 'utf8_name', 'glottocode',
                  'variety', 'foss_stat', 'low_stat', 'soundcompcode',
                  'level0', 'level1', 'level2', 'level3', 'representative',
                  'rfcWebPath1', 'rfcWebPath2', 'author', 'reviewer',
                  'earliestTimeDepthBound', 'latestTimeDepthBound',
                  'progress', 'sortRankInClade', 'entryTimeframe',
                  'historical', 'fragmentary', 'notInExport', 'exampleLanguage',
                  'latitude', 'longitude', 'nativeScriptIsRtl'])
        return fs | AbstractDistribution.timestampedFields(self)

    def deltaReport(self, **kwargs):
        return 'Could not update language: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.ascii_name, kwargs, self.lastEditedBy, self.lastTouched)

    @property
    def progressPercentage(self):
        percentages = {
            0: 0,
            1: 20,
            2: 40,
            3: 60,
            4: 80,
            5: 100
        }
        return percentages[self.progress]

    @property
    def progressBarClass(self):
        # Return class string to color progress bar
        percentages = {
            0: 'progress-bar-danger',
            1: 'progress-bar-danger',
            2: 'progress-bar-warning',
            3: 'progress-bar-info',
            4: 'progress-bar-info',
            5: 'progress-bar-success'
        }
        return percentages[self.progress]


@reversion.register
class LanguageClade(models.Model):
    language = models.ForeignKey(Language)
    clade = models.ForeignKey(Clade)
    # Order in which Language.getClades found these entries:
    cladesOrder = models.IntegerField(default=0, null=False)

    class Meta:
        ordering = ['cladesOrder']


@reversion.register
class Meaning(AbstractTimestamped):
    DEFAULT = 'ash'

    gloss = models.CharField(
        max_length=64, unique=True, validators=[suitable_for_url])
    description = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    percent_coded = models.FloatField(editable=False, default=0)
    doubleCheck = models.BooleanField(default=0)
    exclude = models.BooleanField(default=0)
    tooltip = models.TextField(blank=True)
    meaningSetMember = models.IntegerField(default=0, null=False)
    meaningSetIx = models.IntegerField(default=0, null=False)
    exampleContext = models.CharField(max_length=128, blank=True)
    ixElicitation = models.IntegerField(default=0, null=False)
    concepticon_id = models.IntegerField(default=0, null=False)

    def get_absolute_url(self):
        return "/meaning/%s/" % self.gloss

    def set_percent_coded(self):
        """called by a post_save signal on CognateJudgement"""
        old_value = self.percent_coded
        uncoded = self.lexeme_set.filter(cognate_class=None).count()
        total = self.lexeme_set.count()
        try:
            self.percent_coded = 100.0 * (total - uncoded) / total
        except ZeroDivisionError:
            self.percent_coded = 0
        if self.percent_coded != old_value:
            self.save()

    def __str__(self):
        return self.gloss.upper()

    class Meta:
        ordering = ["gloss"]

    def timestampedFields(self):
        return set(['gloss', 'description',
                    'notes', 'doubleCheck',
                    'exclude', 'tooltip',
                    'meaningSetMember', 'meaningSetIx',
                    'exampleContext', 'ixElicitation', 'concepticon_id'])

    def deltaReport(self, **kwargs):
        return 'Could not update meaning: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.gloss, kwargs, self.lastEditedBy, self.lastTouched)

    _computeCounts = {}  # Memo for computeCounts

    def computeCounts(self, languageList=None):
        """
        computeCounts calculates some of the properties of this model.
        It uses self._computeCounts for memoization.
        """
        if not self._computeCounts:
            # Making sure we have a languageList:
            if languageList is None:
                languageList = LanguageList.objects.get(name='all')
            # Cognate classes to iterate:
            lIds = languageList.languagelistorder_set.values_list(
                "language_id", flat=True)
            ccs = CognateClass.objects.filter(
                lexeme__meaning_id=self.id,
                lexeme__language_id__in=lIds).distinct()
            # Setup to count stuff:
            cog_count = len(ccs)
            cogRootFormCount = 0
            cogRootLanguageCount = 0
            cogLoanCount = 0
            cogParallelLoanCount = 0
            cogRevised = 0
            # Iterating ccs to calculate counts:
            for cc in ccs:
                if cc.root_form != '':
                    cogRootFormCount += 1
                if cc.root_language != '':
                    cogRootLanguageCount += 1
                if cc.loanword:
                    cogLoanCount += 1
                if cc.parallelLoanEvent:
                    cogParallelLoanCount += 1
                if cc.revisedYet:
                    cogRevised += 1
            # Computing percentages:
            cogRootFormPercentage = cogRootFormCount / cog_count \
                if cog_count > 0 else float('nan')
            cogRootFormPercentage *= 100
            cogRootLanguagePercentage = cogRootLanguageCount / cog_count \
                if cog_count > 0 else float('nan')
            cogRootLanguagePercentage *= 100
            cog_truecount = cog_count - cogLoanCount
            if cog_count > 0:
                cogRevisedPercentage = cogRevised / cog_count * 100
            else:
                cogRevisedPercentage = 0
            # Filling memo with data:
            self._computeCounts = {
                'cog_count': cog_count,
                'cog_truecount': cog_truecount,
                'cogRevisedPercentage': cogRevisedPercentage,
                'cogRootFormCount': cogRootFormCount,
                'cogRootFormPercentage': cogRootFormPercentage,
                'cogRootLanguageCount': cogRootLanguageCount,
                'cogRootLanguagePercentage': cogRootLanguagePercentage,
                'cogLoanCount': cogLoanCount,
                'cogParallelLoanCount': cogParallelLoanCount}
        return self._computeCounts

    @property
    def meaningId(self):
        return self.id

    @property
    def lex_count(self):
        return len(self.lexeme_set.all())

    @property
    def cog_count(self):
        return self.computeCounts()['cog_count']

    @property
    def cog_truecount(self):
        return self.computeCounts()['cog_truecount']

    @property
    def cogRevisedPercentage(self):
        return self.computeCounts()['cogRevisedPercentage']

    @property
    def cogRootFormCount(self):
        return self.computeCounts()['cogRootFormCount']

    @property
    def cogRootFormPercentage(self):
        return '%.1f' % self.computeCounts()['cogRootFormPercentage']

    @property
    def cogRootLanguageCount(self):
        return self.computeCounts()['cogRootLanguageCount']

    @property
    def cogRootLanguagePercentage(self):
        return '%.1f' % self.computeCounts()['cogRootLanguagePercentage']

    @property
    def cogLoanCount(self):
        return self.computeCounts()['cogLoanCount']

    @property
    def cogParallelLoanCount(self):
        return self.computeCounts()['cogParallelLoanCount']


@reversion.register
@python_2_unicode_compatible
class CognateClass(AbstractTimestamped):
    """
    1.  `name` field: This is optional, for manually given names.
    2.  `root_form` field:
        Using decorator to ensure Python 2 unicode compatibility.
        For details see
        `django.utils.encoding.python_2_unicode_compatible` at:
        https://docs.djangoproject.com/en/dev/ref/utils/
    """
    alias = models.CharField(max_length=3)
    notes = models.TextField(blank=True)
    justificationDiscussion = models.TextField(blank=True)
    alsoUsedInOtherMeanings = models.TextField(blank=True)
    root_form = models.TextField(blank=True)
    root_language = models.TextField(blank=True)
    # Former JSON fields:
    gloss_in_root_lang = models.TextField(blank=True)
    loanword = models.BooleanField(default=0)
    loan_source = models.TextField(blank=True)
    loan_notes = models.TextField(blank=True)
    # Fields added for #162:
    loanEventTimeDepthBP = models.TextField(blank=True)
    sourceFormInLoanLanguage = models.TextField(blank=True)
    loanSourceCognateClass = models.ForeignKey("self", null=True)
    # Fields added for #176:
    parallelLoanEvent = models.BooleanField(default=0)
    notProtoIndoEuropean = models.BooleanField(default=0)
    # Added when mobbing 2016-08-04:
    ideophonic = models.BooleanField(default=0)
    parallelDerivation = models.BooleanField(default=0)
    dubiousSet = models.BooleanField(default=0)
    # Added for #263:
    revisedYet = models.BooleanField(default=0)
    revisedBy = models.CharField(max_length=10, default='')
    # Added for #319:
    proposedAsCognateTo = models.ForeignKey(
        "self", null=True, related_name='+')
    proposedAsCognateToScale = models.IntegerField(
        default=0, choices=PROPOSED_AS_COGNATE_TO_SCALE)

    def update_alias(self, save=True):
        """Reset alias to the first unused letter"""
        codes = set(ascii_uppercase) | \
            set([i + j for i in ascii_uppercase for j in ascii_lowercase])
        meanings = Meaning.objects.filter(
            lexeme__cognate_class=self).distinct()
        current_aliases = CognateClass.objects.filter(
            lexeme__meaning__in=meanings).distinct().exclude(
                id=self.id).values_list("alias", flat=True)
        codes -= set(current_aliases)
        self.alias = sorted(codes, key=lambda i: (len(i), i))[0]
        if save:
            self.save()

    def get_meanings(self):
        # some cognate classes have more than one meaning, e.g. "right" ~
        # "rightside", "in" ~ "at"
        meanings = Meaning.objects.filter(
            lexeme__cognate_class=self).distinct()
        return meanings

    def get_meaning(self):
        # for nexus files it doesn't matter what gloss we use, so long as there
        # is only one per cognate set
        try:
            return self.get_meanings().order_by("gloss")[0]
        except IndexError:
            return None

    def get_absolute_url(self):
        return "/cognate/%s/" % self.id

    def __str__(self):
        if self.alias:
            return "%s (%s)" % (self.id, self.alias)
        return "%s" % self.id

    class Meta:
        ordering = ["alias"]

    def timestampedFields(self):
        return set(['alias', 'notes', 'justificationDiscussion', 'root_form', 'root_language',
                    'gloss_in_root_lang', 'loanword', 'loan_source',
                    'loan_notes', 'loanSourceCognateClass',
                    'loanEventTimeDepthBP', 'sourceFormInLoanLanguage',
                    'parallelLoanEvent', 'notProtoIndoEuropean', 'ideophonic',
                    'parallelDerivation', 'dubiousSet',
                    'revisedYet', 'revisedBy', 'alsoUsedInOtherMeanings',
                    'proposedAsCognateTo', 'proposedAsCognateToScale'])

    def deltaReport(self, **kwargs):
        return 'Could not update cognate class: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.id, kwargs, self.lastEditedBy, self.lastTouched)

    _computeCounts = {}  # Memo for computeCounts

    def computeCounts(self, languageList=None, 
                        lgSet=None, isCladeCountNeeded=True, clades=None):
        """
        computeCounts calculates the lexeme* properties.
        It uses self._computeCounts for memoization.
        """
        if not self._computeCounts:
            # Use languageList to build lSet to filter lexemes:
            if lgSet is None:
                if languageList is not None:
                    lgSet = set(languageList.languagelistorder_set.all().values_list(
                        'language_id', flat=True))
                else:
                    lgSet = set()
            # Gather counts:
            theLexemes = self.lexeme_set.filter(language__in=lgSet).all()
            targetLexemes = theLexemes.filter(not_swadesh_term=False)

            # True if all lexemes are not_swadesh_term.
            onlyNotSwh = (len(targetLexemes) == 0)
            lexemeCount = len(theLexemes)
            # Computing cladeCount:
            languageIds = targetLexemes.exclude(
                    language__level0=0).values_list(
                        'language_id', flat=True)
            cladeCount = 0
            if isCladeCountNeeded:
                if clades is not None:
                    cladeCount = clades.filter(
                        languageclade__language__id__in=languageIds).distinct().count()
                else:
                    cladeCount = Clade.objects.filter(
                        languageclade__language__id__in=languageIds).exclude(
                            hexColor='').exclude(
                                shortName='').distinct().count()
            # Filling memo with data:
            self._computeCounts = {
                'lexemeCount': lexemeCount,
                'onlyNotSwh': onlyNotSwh,
                'cladeCount': cladeCount}
        return self._computeCounts

    @property
    def root_form_compare(self):
        return 'root_form' + str(self.id)

    @property
    def root_language_compare(self):
        return 'root_language' + str(self.id)

    @property
    def idField(self):
        return self.id

    @property
    def lexemeCount(self):
        return self.computeCounts()['lexemeCount']

    @property
    def citationCount(self):
        return self.cognateclasscitation_set.count()

    @property
    def hasOnlyNotSwadesh(self):
        return self.computeCounts()['onlyNotSwh']

    @property
    def cladeCount(self):
        return self.computeCounts()['cladeCount']

    @property
    def loanSourceCognateClassTitle(self):
        cc = self.loanSourceCognateClass
        return ' '.join([cc.alias, cc.root_form, cc.root_language])

    @property
    def rootFormOrPlaceholder(self):
        if self.root_form != '':
            return self.root_form
        # If single lexeme in cognate class, use romanised:
        if self.lexeme_set.count() == 1:
            return self.lexeme_set.get().romanised
        # Do we have a loanword?
        if self.loanword:
            if self.sourceFormInLoanLanguage != '':
                return "(%s)" % self.sourceFormInLoanLanguage
        # Branch lookup for #364:
        affectedLanguageIds = set(self.lexeme_set.filter(
            cognate_class=self).values_list('language_id', flat=True))
        commonCladeIds = Clade.objects.filter(
            language__id__in=affectedLanguageIds
            ).distinct().order_by(
                'languageclade__cladesOrder'
                ).values_list('id', flat=True)
        if commonCladeIds:
            findQuery = Language.objects.filter(
                languageclade__clade__id=commonCladeIds[0],
                id__in=affectedLanguageIds)

            def getOrthographics(cognateClass, languageIds):
                return Lexeme.objects.filter(
                    language__id__in=languageIds,
                    cognate_class=cognateClass).exclude(
                        romanised='').order_by(
                        'language__sortRankInClade').values_list(
                            'romanised', flat=True)

            idFinders = [lambda: findQuery.filter(
                            representative=True).values_list('id', flat=True),
                         lambda: findQuery.filter(
                            exampleLanguage=True).values_list('id', flat=True),
                         lambda: affectedLanguageIds]

            for idFinder in idFinders:
                languageIds = idFinder()
                if languageIds:
                    orthographics = getOrthographics(self, languageIds)
                    if orthographics:
                        return orthographics[0]
        # Nothing left to try:
        return ''

    @property
    def rootLanguageOrPlaceholder(self):
        # Added for #246
        # If we have a root_language, we try to enrich it:
        if self.root_language != '':
            return self.root_language
        # Maybe only one lexeme in cognate class:
        if self.lexeme_set.count() == 1:
            return self.lexeme_set.values_list(
                'language__utf8_name', flat=True)[0]
        # Maybe we can find a clade specific to the related languages:
        parentClade = getCladeFromLanguageIds(set(
            self.lexeme_set.values_list('language_id', flat=True)))
        if parentClade is not None:
            return "(%s)" % parentClade.taxonsetName
        # Maybe we can use loan_source:
        if self.loanword and self.loan_source != '':
            return "(%s)" % self.loan_source
        # Nothing left to try:
        return ''

    @property
    def combinedRootPlaceholder(self):
        # Added for #246
        # Calculating part 1:
        p1 = ' IN '.join(
            [s for s in [self.rootFormOrPlaceholder,
                         self.rootLanguageOrPlaceholder]
             if s != ''])
        # Calculating part 2:
        p2 = ''
        if self.loanword:
            if self.sourceFormInLoanLanguage != '' and self.loan_source != '':
                p2 = "%s IN %s" % (self.sourceFormInLoanLanguage,
                                   self.loan_source)
            elif self.sourceFormInLoanLanguage != '':
                p2 = self.sourceFormInLoanLanguage
            elif self.loan_source != '':
                p2 = self.loan_source
        # Composing parts:
        if self.loanword:
            return u"%s ≤ %s" % (p1, p2)
        return p1


class DyenCognateSet(models.Model):
    cognate_class = models.ForeignKey(CognateClass)
    name = models.CharField(max_length=8)
    doubtful = models.BooleanField(default=0)

    def __str__(self):
        if self.doubtful:
            qmark = " ?"
        else:
            qmark = ""
        return "%s%s" % (self.name, qmark)


@reversion.register
class Lexeme(AbstractTimestamped):
    language = models.ForeignKey(Language)
    meaning = models.ForeignKey(Meaning)
    cognate_class = models.ManyToManyField(
        CognateClass, through="CognateJudgement", blank=True)
    romanised = models.CharField(max_length=128)
    phon_form = models.CharField(max_length=128, blank=True)
    gloss = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    source = models.ManyToManyField(
        Source, through="LexemeCitation", blank=True)
    phoneMic = models.TextField(blank=True)
    nativeScript = models.TextField(blank=True)
    not_swadesh_term = models.BooleanField(default=0)
    rfcWebLookup1 = models.TextField(blank=True)
    rfcWebLookup2 = models.TextField(blank=True)
    dubious = models.BooleanField(default=0)

    def get_cognate_class_links(self):
        def format_link(cc_id, alias):
            if alias.startswith("(") and alias.endswith(")"):
                template = '(<a href="/cognate/%s/">%s</a>)'
                alias = alias[1:-1]
            else:
                template = '<a href="/cognate/%s/">%s</a>'
            return template % (cc_id, alias)
        parts = [format_link(cc_id, alias) for cc_id, alias in
                 two_by_two(self.denormalized_cognate_classes.split(","))]
        return SafeString(", ".join(parts))

    def get_absolute_url(self, anchor=None):
        """The absolute urls of LexemeCitation, CognateJudgement and
        CognateJudgementCitation are also on the Lexeme page, but with
        anchors of the format:
            #lexemecitation_ID
            #cognatejudgement_ID
            #cognatejudgementcitation_ID
        """
        if anchor:
            return "/lexeme/%s/#%s" % (self.id, anchor.strip("#"))
        return "/lexeme/%s/" % self.id

    def __str__(self):
        return self.phon_form or self.romanised or ("Lexeme %s" % self.id)

    class Meta:
        order_with_respect_to = "language"

    def checkLoanEvent(self):
        """
        This method was added for #29 and shall return one of three values:
        * In case that there is exactly one CognateClass linked to this lexeme:
          * Return .data.get('loanword', False)
        * Otherwise return None.
        """
        if self.cognate_class.count() == 1:
            for c in self.cognate_class.all():
                return c.loanword
        return None

    def checkPllLoanEvent(self):
        """
        This method was added for #463 and shall return one of three values:
        * In case that there is exactly one CognateClass linked to this lexeme:
          * Return .data.get('loanword', False)
        * Otherwise return None.
        """
        if self.cognate_class.count() == 1:
            for c in self.cognate_class.all():
                return c.parallelLoanEvent
        return None

    def getCognateClassData(self):
        """
        This method was added for #90 and shall return
        gathered cc data for a lexeme.
        @return {id: .., root_form: .., root_language: ..}
        """
        ccs = self.cognate_class.all()
        ids = [str(cc.id) for cc in ccs]
        if not ids:
            return None
        ccdata = {}
        ccdata['id'] = ','.join(ids)
        rfs = [cc.root_form for cc in ccs]
        tmp = ','.join(rfs)
        if len(tmp) > 0:
            ccdata['root_form'] = tmp
        rls = [cc.root_language for cc in ccs]
        tmp = ','.join(rls)
        if len(tmp) > 0:
            ccdata['root_language'] = tmp
        return ccdata

    def timestampedFields(self):
        return set(['romanised', 'phon_form', 'gloss', 'notes', 'phoneMic',
                    'nativeScript', 'not_swadesh_term',
                    'rfcWebLookup1', 'rfcWebLookup2', 'dubious'])

    def deltaReport(self, **kwargs):
        return 'Could not update Lexeme entry: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.romanised, kwargs, self.lastEditedBy, self.lastTouched)

    @property
    def denormalized_cognate_classes(self):
        """
        Creates a sequence of 'cc1.id, cc1.alias, cc2.id, cc2.alias'
        for each CognateClass related to self.
        To have fast access to CognateJudgements necessary to
        display exclusion correctly we build a map
        from CognateClass.id to CognateJudgement named cJMap.
        """
        cJMap = {cj.cognate_class_id: cj for cj
                 in self.cognatejudgement_set.all()}
        data = []
        for cc in self.cognate_class.all():
            data.append(cc.id)
            judgement = cJMap[cc.id]
            if judgement.is_excluded:
                data.append("(%s)" % cc.alias)
            else:
                data.append(cc.alias)
        return ",".join(str(e) for e in data)

    @property
    def is_excluded_lexeme(self):
        # Tests is_exc for #88
        return 'X' in self.reliability_ratings

    @property
    def is_excluded_cognate(self):
        # Tests is_exc for #29
        for j in self.cognatejudgement_set.all():
            if j.is_excluded:
                if not j.is_loanword:
                    return True
        return False

    @property
    def is_loan_cognate(self):
        # Tests is_loan for #29
        for j in self.cognatejudgement_set.all():
            if j.is_excluded:
                if j.is_loanword:
                    return True
        return False

    @property
    def reliability_ratings(self):
        return set([lc.reliability for lc in self.lexemecitation_set.all()])

    @property
    def show_loan_event(self):
        return self.checkLoanEvent is not None

    @property
    def show_pllloan_event(self):
        return self.checkPllLoanEvent is not None

    @property
    def loan_event(self):
        return self.checkLoanEvent()

    @property
    def pllloan_event(self):
        return self.checkPllLoanEvent()

    @property
    def language_asciiname(self):
        return self.language.ascii_name

    @property
    def language_utf8name(self):
        return self.language.utf8_name

    @property
    def language_color(self):
        return self.language.hexColor

    @property
    def cognate_class_links(self):
        return self.get_cognate_class_links()

    @property
    def allCognateClasses(self):
        return self.cognate_class.all()

    @property
    def number_cognate_coded(self):
        # Added for #178
        return self.cognate_class.count()

    @property
    def selectionJSON(self):
        # Added for #219 to describe lexeme and cognate classes.
        return json.dumps({'lexemeId': self.id,
                           'cognateClassIds': list(
                               self.cognate_class.values_list(
                                   'id', flat=True))})

    @property
    def combinedCognateClassAssignment(self):
        # Added for #219
        return ', '.join([c.alias for c in self.allCognateClasses])

    @property
    def loanEventSourceTitle(self):
        ccd = self.getCognateClassData()
        if ccd == None:
            return '';
        parts = []
        if 'root_form' in ccd and 'root_language' in ccd:
            parts.append('(%s) < (%s)' %
                         (ccd['root_form'], ccd['root_language']))
        elif 'root_form' in ccd:
            parts.append('(%s) < (?)' % ccd['root_form'])
        elif 'root_language' in ccd:
            parts.append('(?) < (%s)' % ccd['root_language'])
        return '\n'.join(parts)

    @property
    def lexCitCount(self):
        return self.lexemecitation_set.count()


@reversion.register
class CognateJudgement(AbstractTimestamped):
    lexeme = models.ForeignKey(Lexeme)
    cognate_class = models.ForeignKey(CognateClass)
    source = models.ManyToManyField(Source, through="CognateJudgementCitation")

    def get_absolute_url(self):
        anchor = "cognatejudgement_%s" % self.id
        return self.lexeme.get_absolute_url(anchor)

    @property
    def reliability_ratings(self):
        return set([cj.reliability
                    for cj in self.cognatejudgementcitation_set.all()])

    @property
    def long_reliability_ratings(self):
        """
        An alphabetically sorted list of (rating_code, description) tuples
        """
        descriptions = defaultdict(str, RELIABILITY_CHOICES)
        return [(rating, descriptions[rating]) for rating in
                sorted(self.reliability_ratings)]

    @property
    def is_loanword(self):
        is_loanword = "L" in self.reliability_ratings
        return is_loanword

    @property
    def is_excluded(self):
        return bool(set(["X", "L"]).intersection(self.reliability_ratings))

    def __str__(self):
        return u"%s-%s-%s" % (self.lexeme.meaning.gloss,
                              self.cognate_class.alias, self.id)


@reversion.register
class LanguageList(models.Model):
    """A named, ordered list of languages for use in display and output. A
    default list, named 'all' is (re)created on save/delete of the Language
    table (cf. ielex.models.update_language_list_all)

    To get an order list of language from LanguageList `ll`::

        ll.languages.all().order_by("languagelistorder")
    """
    DEFAULT = "Current"
    ALL = "all"

    name = models.CharField(
        max_length=128, unique=True,
        validators=[suitable_for_url, standard_reserved_names])
    description = models.TextField(blank=True, null=True)
    languages = models.ManyToManyField(Language, through="LanguageListOrder")
    modified = models.DateTimeField(auto_now=True)

    def append(self, language):
        """Add another language to the end of a LanguageList ordering"""
        N = list(self.languagelistorder_set.aggregate(Max("order")).values())[0]
        try:
            N += 1
        except TypeError:
            assert N is None
            N = 0
        LanguageListOrder.objects.create(
            language=language,
            language_list=self,
            order=N)

    def insert(self, N, language):
        """
        Insert another language into a LanguageList
        ordering before the object position N
        """
        llo = LanguageListOrder.objects.get(
            language=language,
            language_list=self)
        target = self.languagelistorder_set.all()[N]
        llo.order = target.order - 0.0001
        llo.save()

    def remove(self, language):
        llo = LanguageListOrder.objects.get(
            language=language,
            language_list=self)
        llo.delete()

    def sequentialize(self):
        """Sequentialize the order fields of a LanguageListOrder set
        with a separation of approximately 1.0.  This is a bit slow, so
        it should only be done from time to time."""
        if self.languagelistorder_set.count():
            llos = self.languagelistorder_set.order_by('order').all()
            for i, llo in enumerate(llos):
                if i < llo.order:
                    llo.order = i
                    llo.save()

    def swap(self, languageA, languageB):
        """Swap the order of two languages"""
        orderA = LanguageListOrder.objects.get(
            language=languageA,
            language_list=self)
        orderB = LanguageListOrder.objects.get(
            language=languageB,
            language_list=self)
        orderB.delete()
        orderA.order, orderB.order = orderB.order, orderA.order
        orderA.save()
        orderB.save()

    def get_absolute_url(self):
        return "/languages/%s/" % self.name

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class LanguageListOrder(models.Model):

    language = models.ForeignKey(Language)
    language_list = models.ForeignKey(LanguageList)
    order = models.FloatField()

    def __str__(self):
        return u"%s:%s(%s)" % (self.language_list.name,
                               self.order,
                               self.language.ascii_name)

    class Meta:
        ordering = ["order"]
        unique_together = (("language_list", "language"),
                           ("language_list", "order"))


@reversion.register
class MeaningList(models.Model):
    """Named lists of meanings, e.g. 'All' and 'Swadesh_100'"""
    DEFAULT = "Jena175"
    ALL = "all"

    name = models.CharField(
        max_length=128, unique=True,
        validators=[suitable_for_url, standard_reserved_names])
    description = models.TextField(blank=True, null=True)
    meanings = models.ManyToManyField(Meaning, through="MeaningListOrder")
    modified = models.DateTimeField(auto_now=True)

    def append(self, meaning):
        """Add another meaning to the end of a MeaningList ordering"""
        N = list(self.meaninglistorder_set.aggregate(Max("order")).values())[0]
        try:
            N += 1
        except TypeError:
            assert N is None
            N = 0
        MeaningListOrder.objects.create(
            meaning=meaning,
            meaning_list=self,
            order=N)

    def insert(self, N, meaning):
        """
        Insert another meaning into a MeaningList
        ordering before the object position N
        """
        llo = MeaningListOrder.objects.get(
            meaning=meaning,
            meaning_list=self)
        target = self.meaninglistorder_set.all()[N]
        llo.order = target.order - 0.0001
        llo.save()

    def remove(self, meaning):
        llo = MeaningListOrder.objects.get(
            meaning=meaning,
            meaning_list=self)
        llo.delete()

    def sequentialize(self):
        """Sequentialize the order fields of a MeaningListOrder set
        with a separation of approximately 1.0.  This is a bit slow, so
        it should only be done from time to time."""
        if self.meaninglistorder_set.count():
            mlos = self.meaninglistorder_set.order_by('order').all()
            for i, mlo in enumerate(mlos):
                if i != mlo.order:
                    mlo.order = i
                    mlo.save()

    def swap(self, meaningA, meaningB):
        """Swap the order of two meanings"""
        orderA = MeaningListOrder.objects.get(
            meaning=meaningA,
            meaning_list=self)
        orderB = MeaningListOrder.objects.get(
            meaning=meaningB,
            meaning_list=self)
        orderB.delete()
        orderA.order, orderB.order = orderB.order, orderA.order
        orderA.save()
        orderB.save()

    def get_absolute_url(self):
        return "/meanings/%s/" % self.name

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class MeaningListOrder(models.Model):

    meaning = models.ForeignKey(Meaning)
    meaning_list = models.ForeignKey(MeaningList)
    order = models.FloatField()

    def __str__(self):
        return u"%s:%s(%s)" % (self.meaning_list.name,
                               self.order,
                               self.meaning.gloss)

    class Meta:
        ordering = ["meaning__gloss"]
        unique_together = (("meaning_list", "meaning"),
                           ("meaning_list", "order"))


class AbstractBaseCitation(models.Model):
    """Abstract base class for citation models
    The source field has to be in the subclasses in order for the
    unique_together constraints to work properly"""
    pages = models.CharField(max_length=128, blank=True)
    reliability = models.CharField(max_length=1, choices=RELIABILITY_CHOICES)
    comment = models.TextField(blank=True)
    modified = models.DateTimeField(auto_now=True)

    def long_reliability(self):
        try:
            description = dict(RELIABILITY_CHOICES)[self.reliability]
        except KeyError:
            description = ""
        return description

    class Meta:
        abstract = True


@reversion.register
class CognateJudgementCitation(AbstractBaseCitation):
    cognate_judgement = models.ForeignKey(CognateJudgement)
    source = models.ForeignKey(Source)

    def get_absolute_url(self):
        anchor = "cognatejudgementcitation_%s" % self.id
        return self.cognate_judgement.lexeme.get_absolute_url(anchor)

    def __str__(self):
        return u"CJC src=%s cit=%s" % (self.source.id, self.id)

    class Meta:
        unique_together = (("cognate_judgement", "source"),)


@reversion.register
class LexemeCitation(AbstractBaseCitation):
    lexeme = models.ForeignKey(Lexeme)
    source = models.ForeignKey(Source)

    # def get_absolute_url(self):
    #     return "/lexeme/citation/%s/" % self.id

    def get_absolute_url(self):
        anchor = "lexemecitation_%s" % self.id
        return self.lexeme.get_absolute_url(anchor)

    def __str__(self):
        return u"%s %s src:%s" % \
            (self.id, self.lexeme.romanised, self.source.id)

    class Meta:
        unique_together = (("lexeme", "source"),)


@reversion.register
class CognateClassCitation(AbstractBaseCitation):
    cognate_class = models.ForeignKey(CognateClass)
    source = models.ForeignKey(Source)
    rfcWeblink = models.URLField(blank=True)

    def __str__(self):
        try:
            cog = self.cognate_class.id
        except CognateClass.DoesNotExist:
            cog = None
        try:
            src = self.source.id
        except Source.DoesNotExist:
            src = None
        return u"%s cog=%s src=%s" % (self.id, cog, src)

    def get_absolute_url(self):
        return reverse("cognate-class-citation-detail",
                       kwargs={"pk": self.id})

    def getCommentExpandedMarkups(self):
        # replace markups for comment field (used in non-edit mode)
        s = Source.objects.all().filter(deprecated=False)
        comment = self.comment
        pattern = re.compile(r'(\{ref +([^\{]+?)(:[^\{]+?)? *\})')
        pattern2 = re.compile(r'(\{ref +[^\{]+?(:[^\{]+?)? *\})')
        for m in re.finditer(pattern, comment):
            foundSet = s.filter(shorthand=m.group(2))
            if foundSet.count() == 1:
                comment = re.sub(pattern2, lambda match: '<a href="/sources/'
                    + str(foundSet.first().id)
                    + '" title="' + foundSet.first().citation_text.replace('"', '\"')
                    + '">' + foundSet.first().shorthand + '</a>', comment, 1)
        return comment

    class Meta:
        unique_together = (("cognate_class", "source"),)


@disable_for_loaddata
def update_language_list_all(sender, instance, **kwargs):
    """Update the LanguageList 'all' whenever Language table is changed"""
    ll, _ = LanguageList.objects.get_or_create(name=LanguageList.ALL)
    ll.sequentialize()

    missing_langs = set(Language.objects.all()) - set(ll.languages.all())
    for language in missing_langs:
        ll.append(language)

    if missing_langs:
        # make a new alphabetized list
        default_alpha = LanguageList.DEFAULT + "-alpha"
        try:  # zap the old one
            ll_alpha = LanguageList.objects.get(name=default_alpha)
            ll_alpha.delete()
        except LanguageList.DoesNotExist:
            pass
        ll_alpha = LanguageList.objects.create(name=default_alpha)
        for language in Language.objects.all().order_by("ascii_name"):
            ll_alpha.append(language)


models.signals.post_save.connect(update_language_list_all, sender=Language)
models.signals.post_delete.connect(update_language_list_all, sender=Language)


@disable_for_loaddata
def update_meaning_list_all(sender, instance, **kwargs):
    ml, _ = MeaningList.objects.get_or_create(name=MeaningList.ALL)
    ml.sequentialize()

    missing_meanings = set(Meaning.objects.all()) - set(ml.meanings.all())
    for meaning in missing_meanings:
        ml.append(meaning)

    if missing_meanings:
        # make a new alphabetized list
        default_alpha = MeaningList.DEFAULT + "-alpha"
        try:
            ml_alpha = MeaningList.objects.get(name=default_alpha)
            ml_alpha.delete()
        except MeaningList.DoesNotExist:
            pass
        ml_alpha = MeaningList.objects.create(name=default_alpha)
        for meaning in Meaning.objects.all().order_by("gloss"):
            ml_alpha.append(meaning)


models.signals.post_save.connect(update_meaning_list_all, sender=Meaning)
models.signals.post_delete.connect(update_meaning_list_all, sender=Meaning)


@disable_for_loaddata
def update_meaning_percent_coded(sender, instance, **kwargs):
    meaning = None
    if isinstance(instance, Lexeme):
        meaning = instance.meaning  # Could be None
    elif isinstance(instance, CognateJudgement):
        meaning = instance.lexeme.meaning  # Could be None
    if meaning is not None:
        meaning.set_percent_coded()


models.signals.post_save.connect(
    update_meaning_percent_coded, sender=Lexeme)
models.signals.post_delete.connect(
    update_meaning_percent_coded, sender=Lexeme)
models.signals.post_save.connect(
    update_meaning_percent_coded, sender=CognateJudgement)
models.signals.post_delete.connect(
    update_meaning_percent_coded, sender=CognateJudgement)


@reversion.register
class Author(AbstractTimestamped):
    surname = models.TextField(blank=True)
    firstNames = models.TextField(blank=True)
    initials = models.TextField(blank=True, unique=True)
    email = models.TextField(blank=True, unique=True)
    website = models.TextField(blank=True)
    # An Author may relate to a database user:
    user = models.ForeignKey(User, null=True)

    def timestampedFields(self):
        return set(['surname', 'firstNames', 'email', 'website', 'initials'])

    def deltaReport(self, **kwargs):
        return 'Could not update author entry: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.surname, kwargs, self.lastEditedBy, self.lastTouched)

    class Meta:
        ordering = ["surname", "firstNames"]

    def __str__(self):
        return '%s, %s' % (self.surname, self.firstNames)

    @property
    def getAvatar(self):
        """
        Tries to infer the avatar of an Author by seaching for pictures that
        are named after the surname of an Author.
        @return path :: str | None
        """
        if self.surname is None or self.surname == '':
            return None
        basePath = 'static/contributors/'
        extensions = ['.jpg', '.jpeg', '.png', '.gif']
        for extension in extensions:
            p = os.path.join(basePath,
                             self.surname + extension)
            if os.path.isfile(p):
                return os.path.join('/ielex', p)

    @property
    def displayEmail(self):
        return " [ AT ] ".join(self.email.split("@"))

    @property
    def fullName(self):
        return ' '.join([self.firstNames, self.surname])


@reversion.register
class NexusExport(AbstractTimestamped):
    # Name of .nex file:
    exportName = models.CharField(max_length=256, blank=True)
    description = models.CharField(max_length=256, blank=True)
    # Settings:
    language_list_name = models.CharField(max_length=128, blank=True)
    meaning_list_name = models.CharField(max_length=128, blank=True)
    dialect = models.CharField(
        max_length=128, choices=NEXUS_DIALECT_CHOICES, default="NN")
    label_cognate_sets = models.BooleanField(default=True)
    ascertainment_marker = models.BooleanField(default=True)
    excludeNotSwadesh = models.BooleanField(default=True)
    excludePllDerivation = models.BooleanField(default=True)
    excludeIdeophonic = models.BooleanField(default=True)
    excludeDubious = models.BooleanField(default=True)
    excludeLoanword = models.BooleanField(default=False)
    excludePllLoan = models.BooleanField(default=True)
    includePllLoan = models.BooleanField(default=False)
    excludeMarkedMeanings = models.BooleanField(default=True)
    excludeMarkedLanguages = models.BooleanField(default=True)
    calculateMatrix = models.BooleanField(default=False)
    # List of setting fields:
    settingFields = ['language_list_name',
                     'meaning_list_name',
                     'dialect',
                     'calculateMatrix',
                     'label_cognate_sets',
                     'ascertainment_marker',
                     'excludeNotSwadesh',
                     'excludePllDerivation',
                     'excludeIdeophonic',
                     'excludeDubious',
                     'excludeLoanword',
                     'excludePllLoan',
                     'includePllLoan',
                     'excludeMarkedMeanings',
                     'excludeMarkedLanguages']
    # Compressed data of nexus file:
    _exportData = models.BinaryField(null=True)
    exportData = property(**compressedField('_exportData'))
    # Compressed data of BEAUti nexus file:
    _exportBEAUti = models.BinaryField(null=True)
    exportBEAUti = property(**compressedField('_exportBEAUti'))
    # Compressed data of constraints file:
    _constraintsData = models.BinaryField(null=True)
    constraintsData = property(**compressedField('_constraintsData'))
    # Compressed data of nexus table data CSV file:
    _exportTableData = models.BinaryField(null=True)
    exportTableData = property(**compressedField('_exportTableData'))
    # Compressed data of matrix data CSV file:
    _exportMatrix = models.BinaryField(null=True)
    exportMatrix = property(**compressedField('_exportMatrix'))

    @property
    def pending(self):
        # True if calculation for export is not finished
        return self._exportData is None

    def generateResponse(self, constraints=False, beauti=False, tabledata=False, matrix=False):
        """
        If constraints == True response shall carry the constraintsData
        rather than the exportData.
        If beauti == True response shall carry exportBEAUti
        rather than exportData.
        """
        assert not self.pending, "NexusExport.generateResponse " \
                                 "impossible for pending exports."

        # name for the export file:
        if constraints:
            name = self.constraintsName
        elif beauti:
            name = self.beautiName
        elif tabledata:
            name = self.tabledataName
        elif matrix:
            name = self.matrixName
        else:
            name = self.exportName

        # The response itself:
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % \
            name.replace(" ", "_")

        # data for the export file:
        if constraints:
            data = self.constraintsData
        elif beauti:
            data = self.exportBEAUti
        elif tabledata:
            # for csv files write the UTF-8 BOM, mainly for Excel
            response.write(codecs.BOM_UTF8)
            data = self.exportTableData
        elif matrix:
            # for csv files write the UTF-8 BOM, mainly for Excel
            response.write(codecs.BOM_UTF8)
            data = self.exportMatrix
        else:
            data = self.exportData

        response.write(data)
        return response

    def setSettings(self, form):
        # form :: ChooseNexusOuputForm
        settings = {
            'language_list_name': form.cleaned_data["language_list"].name,
            'meaning_list_name': form.cleaned_data["meaning_list"].name,
            'label_cognate_sets': True,
        }
        # Copying `simple` fields:
        for f in set(self.settingFields) - set(settings.keys()):
            settings[f] = form.cleaned_data[f]
        for k, v in settings.items():
            setattr(self, k, v)

    def getSettings(self):
        settings = {f: getattr(self, f) for f in self.settingFields}
        settings['language_list_name'] = LanguageList.objects.get(
            name=settings['language_list_name'])
        settings['meaning_list_name'] = MeaningList.objects.get(
            name=settings['meaning_list_name'])
        return settings

    @property
    def constraintsName(self):
        # Replaces the /\.nex$/ in exportName with _Constraints.nex
        return self.exportName[:-4] + "_Constraints.nex"

    @property
    def beautiName(self):
        # Replaces the /\.nex$/ in exportName with _BEAUti.nex
        return self.exportName[:-4] + "_BEAUti.nex"

    @property
    def tabledataName(self):
        # Replaces the /\.nex$/ in exportName _TableData.csv
        return self.exportName[:-4] + "_DataTable.csv"

    @property
    def matrixName(self):
        # Replaces the /\.nex$/ in exportName _TableData.csv
        return self.exportName[:-4] + "_Matrix.csv"


class RomanisedSymbol(AbstractTimestamped):
    # Contains allowed symbols for Lexeme.romanised entries.
    symbol = models.CharField(max_length=8, blank=False)

    @property
    def formattedLastTouchedDate(self):
        return self.lastTouched.strftime("%Y/%m/%d %H:%M:%S")

    @property
    def escapedSymbol(self):
        return self.symbol.encode('unicode_escape')
