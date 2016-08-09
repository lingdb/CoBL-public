# -*- coding: utf-8 -*-
from __future__ import division
import json
import reversion
import math
import os.path
from collections import defaultdict
from string import uppercase, lowercase
from django.db import models
from django.db.models import Max
from django.core.urlresolvers import reverse
from django.utils.safestring import SafeString
from django.utils.encoding import python_2_unicode_compatible
# ielex specific imports:
from ielex.utilities import two_by_two
from ielex.lexicon.validators import suitable_for_url, standard_reserved_names

import inspect


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

# TODO: reinstate the cache stuff, but using a site specific key prefix (maybe
# the short name of the database

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
        else:
            return value

    def get_prep_value(self, value):
        # this was get_db_prep_value, but that is for database specific things
        if value == "":
            return None
        else:
            return value


class AbstractTimestamped(models.Model):
    '''
    This model is created as a mixin that adds
    fields and functionality to other models.
    It aims to solve the problems observed in #111.
    '''
    lastTouched = models.DateTimeField(auto_now=True, blank=True)
    lastEditedBy = models.CharField(max_length=32, default="unknown")

    class Meta:
        abstract = True

    def timestampedFields(self):
        '''
        timestampedFields shall be overwritten by children
        and return a set of field names that are
        allowed to be considered by the AbstractTimestamped
        {isChanged,setDelta} methods.
        '''
        return set()

    def isChanged(self, **vdict):
        '''
        Returns True iff any of the fields in vdict
        that are also specified in timestampedFields
        and are one of the models fields stored in the db
        has changed. Returns False otherwise.
        '''
        tFields = self.timestampedFields()

        for f in self._meta.fields:
            if f.name in tFields and f.name in vdict:
                if getattr(self, f.name) != vdict[f.name]:
                    return True
        return False

    def setDelta(self, request=None, **vdict):
        '''
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
        '''
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
        '''
        Produces a dict that lists all the fields of vdict
        that are valid fields for self in the sense that
        they are mentioned in timestampedFields and
        that are different than the current entries.
        '''
        tFields = self.timestampedFields()
        return {k: vdict[k] for k in vdict
                if k in tFields and
                vdict[k] != getattr(self, k)}

    def checkTime(self, t):
        '''
        Returns true if the given datetime t is
        less then a second different from the current
        lastTouched value.
        '''
        return abs(t - self.lastTouched).seconds == 0

    def bump(self, request, t=None):
        '''
        Updates the lastEditedBy field of an AbstractTimestamped.
        If a t :: datetime is given, bump uses checkTime on that.
        '''
        if t is not None and not self.checkTime(t):
            raise Exception('Refusing bump because of failed checkTime.')
        if request is not None:
            if not request.user.is_authenticated:
                raise Exception('Refusing bump with unauthenticated user.')
            self.lastEditedBy = ' '.join([request.user.first_name,
                                          request.user.last_name])

    def toDict(self):
        '''
        Returns a dict carrying the timestampedFields.
        '''
        return {k: getattr(self, k) for k in self.timestampedFields()}


@reversion.register
class Source(models.Model):

    citation_text = models.TextField(unique=True)
    type_code = models.CharField(
        max_length=1, choices=TYPE_CHOICES, default="P")
    description = models.TextField(blank=True)
    modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "/source/%s/" % self.id

    def __unicode__(self):
        return self.citation_text[:64]

    class Meta:
        ordering = ["type_code", "citation_text"]


@reversion.register
class SndComp(AbstractTimestamped):
    '''
    Introduced for #153.
    This model tracks the correspondence of clades to sndComp sets.
    '''
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
        '''
        This method tries to find the clade closest to a SndComp.
        @return clade :: Clade | None
        '''

        wanted = [('cladeLevel0', self.cladeLevel0),
                  ('cladeLevel1', self.cladeLevel1),
                  ('cladeLevel2', self.cladeLevel2),
                  ('cladeLevel3', self.cladeLevel3)]

        for i in xrange(len(wanted), 0, -1):
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
class Clade(AbstractTimestamped):
    '''
    This model was added for #153
    and shall be used to track clade constraints.
    '''
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
    # Distribution type used:
    distribution = models.CharField(
        max_length=1, choices=DISTRIBUTION_CHOICES, default="_")
    # For [offset] log normal distribution:
    logNormalOffset = models.IntegerField(null=True)
    logNormalMean = models.IntegerField(null=True)
    logNormalStDev = models.IntegerField(null=True)
    # For normal distribution:
    normalMean = models.IntegerField(null=True)
    normalStDev = models.IntegerField(null=True)
    # For uniform distribution:
    uniformUpper = models.IntegerField(null=True)
    uniformLower = models.IntegerField(null=True)

    def __unicode__(self):
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
        return set(['cladeName', 'shortName', 'hexColor', 'export',
                    'exportDate', 'taxonsetName', 'atMost', 'atLeast',
                    'distribution', 'logNormalOffset', 'logNormalMean',
                    'logNormalStDev', 'normalMean', 'normalStDev',
                    'uniformUpper', 'uniformLower', 'cladeLevel0',
                    'cladeLevel1', 'cladeLevel2', 'cladeLevel3',
                    'level0Name', 'level1Name', 'level2Name', 'level3Name'])

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
        if len(self._cognateClassConnections):
            return self._cognateClassConnections.pop(0)
        return False

    @property
    def cladePath(self):
        return ','.join([str(l) for l in [self.cladeLevel0,
                                          self.cladeLevel1,
                                          self.cladeLevel2,
                                          self.cladeLevel3] if l != 0])


@reversion.register
class Language(AbstractTimestamped):
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
    mean_timedepth_BP_years = models.IntegerField(null=True)
    std_deviation_timedepth_BP_years = models.IntegerField(null=True)
    foss_stat = models.BooleanField(default=0)
    low_stat = models.BooleanField(default=0)
    representative = models.BooleanField(default=0)
    rfcWebPath1 = models.TextField(blank=True, null=True)
    rfcWebPath2 = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=256, null=True)
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

    def get_absolute_url(self):
        return "/language/%s/" % self.ascii_name

    def __unicode__(self):
        return self.utf8_name

    class Meta:
        ordering = ['level0',
                    'level1',
                    'level2',
                    'level3',
                    'sortRankInClade']

    def getCsvRow(self, *fields):
        '''
        @return row :: [str]
        '''
        fieldSet = self.timestampedFields()

        row = []
        for f in fields:
            if f in fieldSet:
                row.append(str(getattr(self, f)))
        return row

    _computeCounts = {}  # Memo for computeCounts

    def computeCounts(self, meaningList=None):
        '''
        computeCounts calculates some of the properties of this model.
        It uses self._computeCounts for memoization.
        '''
        if len(self._computeCounts) == 0:
            # Making sure we've got a meaningList:
            if meaningList is None:
                meaningList = MeaningList.objects.get(name=MeaningList.ALL)
            # Setting up sets to aid computations:
            meaningIdSet = getattr(meaningList,
                                   '_language__computeCounts',
                                   None)
            if meaningIdSet is None:
                meaningIdSet = set([m.id for m in meaningList.meanings.all()])
                setattr(meaningList, '_language__computeCounts', meaningIdSet)
            lexemeMeaningIdSet = set([l.meaning_id for l
                                      in self.lexeme_set.all()])
            # Computing base counts:
            meaningCount = len(meaningIdSet & lexemeMeaningIdSet)
            entryCount = len([l for l in self.lexeme_set.all()
                              if l.meaning_id in meaningIdSet])
            nonLexCount = len([l for l in self.lexeme_set.all()
                              if l.meaning_id in meaningIdSet and
                              l.not_swadesh_term])
            # Computing dependant counts:
            lexCount = entryCount - nonLexCount
            excessCount = lexCount - meaningCount
            # Computing unassigned count (#255):
            unassignedCount = self.lexeme_set.filter(
                not_swadesh_term=False,
                meaning__in=meaningIdSet,
                cognate_class=None).count()
            # Setting counts:
            self._computeCounts = {
                'meaningCount': meaningCount,
                'entryCount': entryCount,
                'nonLexCount': nonLexCount,
                'lexCount': lexCount,
                'excessCount': excessCount,
                'unassignedCount': unassignedCount}
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
        return set(['iso_code', 'ascii_name', 'utf8_name', 'glottocode',
                    'variety', 'foss_stat', 'low_stat', 'soundcompcode',
                    'level0', 'level1', 'level2', 'level3', 'representative',
                    'mean_timedepth_BP_years',
                    'std_deviation_timedepth_BP_years',
                    'rfcWebPath1', 'rfcWebPath2', 'author', 'reviewer',
                    'earliestTimeDepthBound', 'latestTimeDepthBound',
                    'progress', 'sortRankInClade', 'entryTimeframe',
                    'historical'])

    def deltaReport(self, **kwargs):
        return 'Could not update language: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.ascii_name, kwargs, self.lastEditedBy, self.lastTouched)


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
    gloss = models.CharField(
        max_length=64, unique=True, validators=[suitable_for_url])
    description = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    percent_coded = models.FloatField(editable=False, default=0)
    # Added when mobbing 2016-08-04:
    doubleCheck = models.BooleanField(default=0)
    exclude = models.BooleanField(default=0)

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

    def __unicode__(self):
        return self.gloss.upper()

    class Meta:
        ordering = ["gloss"]

    def timestampedFields(self):
        return set(['gloss', 'description', 'notes', 'doubleCheck', 'exclude'])

    def deltaReport(self, **kwargs):
        return 'Could not update meaning: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.gloss, kwargs, self.lastEditedBy, self.lastTouched)

    _computeCounts = {}  # Memo for computeCounts

    def computeCounts(self, languageList=None):
        '''
        computeCounts calculates some of the properties of this model.
        It uses self._computeCounts for memoization.
        '''
        if len(self._computeCounts) == 0:
            # Making sure we have a languageList:
            if languageList is None:
                languageList = LanguageList.objects.get(name='all')
            # Cognate classes to iterate:
            lIds = languageList.languagelistorder_set.values_list(
                "language_id", flat=True)
            ccs = CognateClass.objects.filter(
                lexeme__meaning_id=self.id,
                lexeme__language_id__in=lIds).order_by(
                'id').distinct('id').all()
            # Setup to count stuff:
            cog_count = len(ccs)
            cogRootFormCount = 0
            cogRootLanguageCount = 0
            # Iterating ccs to calculate counts:
            for cc in ccs:
                if cc.root_form != '':
                    cogRootFormCount += 1
                if cc.root_language != '':
                    cogRootLanguageCount += 1
            # Computing percentages:
            cogRootFormPercentage = cogRootFormCount / cog_count \
                if cog_count > 0 else float('nan')
            cogRootLanguagePercentage = cogRootLanguageCount / cog_count \
                if cog_count > 0 else float('nan')
            # Filling memo with data:
            self._computeCounts = {
                'cog_count': cog_count,
                'cogRootFormCount': cogRootFormCount,
                'cogRootFormPercentage': cogRootFormPercentage,
                'cogRootLanguageCount': cogRootLanguageCount,
                'cogRootLanguagePercentage': cogRootLanguagePercentage}
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
    def cogRootFormCount(self):
        return self.computeCounts()['cogRootFormCount']

    @property
    def cogRootFormPercentage(self):
        return '%.2f' % self.computeCounts()['cogRootFormPercentage']

    @property
    def cogRootLanguageCount(self):
        return self.computeCounts()['cogRootLanguageCount']

    @property
    def cogRootLanguagePercentage(self):
        return '%.2f' % self.computeCounts()['cogRootLanguagePercentage']


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
    name = CharNullField(
        max_length=128, blank=True, null=True,
        unique=True, validators=[suitable_for_url])
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
    loanSourceId = models.IntegerField(null=True)
    # Not given via timestampedFields;
    # self.save takes care of it automagically:
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

    def __str__(self):
        return self.root_form

    def update_alias(self, save=True):
        """Reset alias to the first unused letter"""
        codes = set(uppercase) | \
            set([i+j for i in uppercase for j in lowercase])
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

    def __unicode__(self):
        if self.alias:
            return "%s (%s)" % (self.id, self.alias)
        else:
            return "%s" % self.id

    class Meta:
        ordering = ["alias"]

    def timestampedFields(self):
        return set(['alias', 'notes', 'name', 'root_form', 'root_language',
                    'gloss_in_root_lang', 'loanword', 'loan_source',
                    'loan_notes', 'loanSourceId', 'loanEventTimeDepthBP',
                    'sourceFormInLoanLanguage', 'parallelLoanEvent',
                    'notProtoIndoEuropean', 'ideophonic',
                    'parallelDerivation', 'dubiousSet',
                    'revisedYet', 'revisedBy'])

    def deltaReport(self, **kwargs):
        return 'Could not update cognate class: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.id, kwargs, self.lastEditedBy, self.lastTouched)

    def save(self, *args, **kwargs):
        '''
        Overwriting save method to make sure loanSourceId
        and loanSourceCognateClass are handled correctly.
        '''
        if self.loanSourceId != self.loanSourceCognateClass_id:
            if self.loanSourceId is None:
                self.loanSourceCognateClass = None
            else:
                self.loanSourceCognateClass = CognateClass.objects.get(
                    id=self.loanSourceId)
        # Relaying to parent:
        return super(CognateClass, self).save(*args, **kwargs)

    _computeCounts = {}  # Memo for computeCounts

    def computeCounts(self, languageList=None):
        '''
        computeCounts calculates the lexeme* properties.
        It uses self._computeCounts for memoization.
        '''
        if len(self._computeCounts) == 0:
            # Use languageList to build lSet to filter lexemes:
            lSet = None
            if languageList is not None:
                lSet = set(llo.language_id for llo in
                           languageList.languagelistorder_set.all())
            # Gather counts:
            lexemeCount = 0
            onlyNotSwh = True  # True iff all lexemes are not_swadesh_term.
            for l in self.lexeme_set.filter(language__in=lSet).all():
                # Update onlyNotSwh iff necessary:
                if not l.not_swadesh_term:
                    onlyNotSwh = False
                # If we have lSet we use it to skip unwanted:
                if lSet is not None:
                    if l.language_id not in lSet:
                        continue
                # Major beef:
                lexemeCount += 1
            # Computing cladeCount:
            languageIds = self.lexeme_set.filter(
                language_id__in=lSet,
                not_swadesh_term=False).exclude(
                language__level0=0).values_list(
                'language_id', flat=True)
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
        return 'root_form'+str(self.id)

    @property
    def root_language_compare(self):
        return 'root_language'+str(self.id)

    @property
    def idField(self):
        return self.id

    @property
    def lexemeCount(self):
        return self.computeCounts()['lexemeCount']

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


class DyenCognateSet(models.Model):
    cognate_class = models.ForeignKey(CognateClass)
    name = models.CharField(max_length=8)
    doubtful = models.BooleanField(default=0)

    def __unicode__(self):
        if self.doubtful:
            qmark = " ?"
        else:
            qmark = ""
        return "%s%s" % (self.name, qmark)


@reversion.register
class Lexeme(AbstractTimestamped):
    language = models.ForeignKey(Language)
    meaning = models.ForeignKey(Meaning, blank=True, null=True)
    cognate_class = models.ManyToManyField(
        CognateClass, through="CognateJudgement", blank=True)
    source_form = models.CharField(max_length=128)
    phon_form = models.CharField(max_length=128, blank=True)
    gloss = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    source = models.ManyToManyField(
        Source, through="LexemeCitation", blank=True)
    # Former JSON fields:
    phoneMic = models.TextField(blank=True)
    transliteration = models.TextField(blank=True)
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
        else:
            return "/lexeme/%s/" % self.id

    def __unicode__(self):
        return self.phon_form or self.source_form or ("Lexeme %s" % self.id)

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

    def getCognateClassData(self):
        """
        This method was added for #90 and shall return
        gathered cc data for a lexeme.
        @return {id: …, root_form: …, root_language: …}
        """
        ccs = self.cognate_class.all()
        ids = [str(cc.id) for cc in ccs]
        rfs = [cc.root_form for cc in ccs]
        rls = [cc.root_language for cc in ccs]
        if len(ids) == 0:
            return None
        return {
            'id':            ','.join(ids),
            'root_form':     ','.join(rfs),
            'root_language': ','.join(rls)}

    def timestampedFields(self):
        return set(['source_form', 'phon_form', 'gloss', 'notes', 'phoneMic',
                    'transliteration', 'not_swadesh_term',
                    'rfcWebLookup1', 'rfcWebLookup2', 'dubious'])

    def deltaReport(self, **kwargs):
        return 'Could not update Lexeme entry: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.source_form, kwargs, self.lastEditedBy, self.lastTouched)

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
        return ('X' in self.reliability_ratings)

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
    def loan_event(self):
        return self.checkLoanEvent()

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

    def __unicode__(self):
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
        N = self.languagelistorder_set.aggregate(Max("order")).values()[0]
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
                if i != llo.order:
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

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class LanguageListOrder(models.Model):

    language = models.ForeignKey(Language)
    language_list = models.ForeignKey(LanguageList)
    order = models.FloatField()

    def __unicode__(self):
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
    DEFAULT = "Jena200"
    ALL = "all"

    name = models.CharField(
        max_length=128, unique=True,
        validators=[suitable_for_url, standard_reserved_names])
    description = models.TextField(blank=True, null=True)
    meanings = models.ManyToManyField(Meaning, through="MeaningListOrder")
    modified = models.DateTimeField(auto_now=True)

    def append(self, meaning):
        """Add another meaning to the end of a MeaningList ordering"""
        N = self.meaninglistorder_set.aggregate(Max("order")).values()[0]
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

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class MeaningListOrder(models.Model):

    meaning = models.ForeignKey(Meaning)
    meaning_list = models.ForeignKey(MeaningList)
    order = models.FloatField()

    def __unicode__(self):
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

    def __unicode__(self):
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

    def __unicode__(self):
        return u"%s %s src:%s" % \
            (self.id, self.lexeme.source_form, self.source.id)

    class Meta:
        unique_together = (("lexeme", "source"),)


@reversion.register
class CognateClassCitation(AbstractBaseCitation):
    cognate_class = models.ForeignKey(CognateClass)
    source = models.ForeignKey(Source)

    def __unicode__(self):
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
        default_alpha = LanguageList.DEFAULT+"-alpha"
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
        default_alpha = MeaningList.DEFAULT+"-alpha"
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
    if type(instance) == Lexeme:
        meaning = instance.meaning  # Could be None
    elif type(instance) == CognateJudgement:
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
    # See https://github.com/lingdb/CoBL/issues/106
    # We leave out the ix field in favour
    # of the id field provided by reversion.
    # Author Surname
    surname = models.TextField(blank=True)
    # Author First names
    firstNames = models.TextField(blank=True)
    # Email address
    email = models.TextField(blank=True, unique=True)
    # Personal website URL
    website = models.TextField(blank=True)
    # Initials
    initials = models.TextField(blank=True, unique=True)

    def timestampedFields(self):
        return set(['surname', 'firstNames', 'email', 'website', 'initials'])

    def deltaReport(self, **kwargs):
        return 'Could not update author entry: ' \
            '"%s" with values %s. ' \
            'It was last touched by "%s" %s.' % \
            (self.surname, kwargs, self.lastEditedBy, self.lastTouched)

    class Meta:
        ordering = ["surname", "firstNames"]

    @property
    def getAvatar(self):
        '''
        Tries to infer the avatar of an Author by seaching for pictures that
        are named after the surname of an Author.
        @return path :: str | None
        '''
        # Guard to make sure we've got a surname:
        if self.surname is None or self.surname == '':
            return None
        basePath = 'static/contributors/'
        extensions = ['.jpg', '.jpeg', '.png', '.gif']
        for extension in extensions:
            p = os.path.join(basePath,
                             self.surname.encode('utf-8') + extension)
            if os.path.isfile(p):
                return p
