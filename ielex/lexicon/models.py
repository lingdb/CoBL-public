# -*- coding: utf-8 -*-
from __future__ import division
from itertools import izip
from string import uppercase, lowercase
from django.db import models, connection
from django.db.models import Max, F
from django.core.urlresolvers import reverse
# from django.core.cache import cache
# from django.db import connection ### testing
from django.db import IntegrityError
from django.dispatch import receiver
from django.db.models.signals import pre_delete, post_delete, post_save
from django.db.backends.signals import connection_created
from django.utils.safestring import SafeString
from django.utils.encoding import python_2_unicode_compatible
# from django.contrib import admin
import jsonfield
import reversion
# from reversion.admin import VersionAdmin
from ielex.utilities import two_by_two
from ielex.lexicon.validators import *
from itertools import izip

# from https://code.djangoproject.com/ticket/8399
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps
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


@reversion.register
class Source(models.Model):

    citation_text = models.TextField(unique=True)
    type_code = models.CharField(
        max_length=1, choices=TYPE_CHOICES, default="P")
    description = models.TextField(blank=True)
    data = jsonfield.JSONField(blank=True)
    modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "/source/%s/" % self.id

    def __unicode__(self):
        return self.citation_text[:64]

    class Meta:
        ordering = ["type_code", "citation_text"]


@reversion.register
class SndComp(models.Model):
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

    def is_unchanged(self, **vdict):

        def isInt(x):
            entry = vdict[x]
            if entry is not None:
                entry = int(entry)
            return getattr(self, x) == entry

        def isString(x):
            return getattr(self, x) == vdict[x]

        fields = {
            'lgSetName': isString,
            'lv0': isInt,
            'lv1': isInt,
            'lv2': isInt,
            'lv3': isInt,
            'cladeLevel0': isInt,
            'cladeLevel1': isInt,
            'cladeLevel2': isInt,
            'cladeLevel3': isInt}

        for k, _ in vdict.iteritems():
            if k in fields:
                if not fields[k](k):
                    return False
        return True

    def setDelta(self, **vdict):

        def setInt(x):
            entry = vdict[x]
            if entry is not None:
                entry = int(entry)
            setattr(self, x, entry)

        def setString(x):
            setattr(self, x, vdict[x])

        fields = {
            'lgSetName': setString,
            'lv0': setInt,
            'lv1': setInt,
            'lv2': setInt,
            'lv3': setInt,
            'cladeLevel0': setInt,
            'cladeLevel1': setInt,
            'cladeLevel2': setInt,
            'cladeLevel3': setInt}

        # Setting fields:
        for k, _ in vdict.iteritems():
            if k in fields:
                fields[k](k)

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
            except Exception, e:
                pass

        return None

    class Meta:
        ordering = ["lv0", "lv1", "lv2", "lv3"]


@reversion.register
class Clade(models.Model):
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

    def is_unchanged(self, **vdict):

        def isInt(x):
            entry = vdict[x]
            if entry is not None:
                entry = int(entry)
            return getattr(self, x) == entry

        def isString(x):
            return getattr(self, x) == vdict[x]

        fields = {
            'cladeName': isString,
            'shortName': isString,
            'hexColor': isString,
            'export': isString,
            'exportDate': isString,
            'taxonsetName': isString,
            'atMost': isInt,
            'atLeast': isInt,
            'distribution': isString,
            'logNormalOffset': isInt,
            'logNormalMean': isInt,
            'logNormalStDev': isInt,
            'normalMean': isInt,
            'normalStDev': isInt,
            'uniformUpper': isInt,
            'uniformLower': isInt,
            'cladeLevel0': isInt,
            'cladeLevel1': isInt,
            'cladeLevel2': isInt,
            'cladeLevel3': isInt,
            'level0Name': isString,
            'level1Name': isString,
            'level2Name': isString,
            'level3Name': isString}

        for k, _ in vdict.iteritems():
            if k in fields:
                if not fields[k](k):
                    return False
        return True

    def setDelta(self, **vdict):

        def setInt(x):
            entry = vdict[x]
            if entry is not None:
                entry = int(entry)
            setattr(self, x, entry)

        def setString(x):
            setattr(self, x, vdict[x])

        fields = {
            'cladeName': setString,
            'shortName': setString,
            'hexColor': setString,
            'export': setString,
            'exportDate': setString,
            'taxonsetName': setString,
            'atMost': setInt,
            'atLeast': setInt,
            'distribution': setString,
            'logNormalOffset': setInt,
            'logNormalMean': setInt,
            'logNormalStDev': setInt,
            'normalMean': setInt,
            'normalStDev': setInt,
            'uniformUpper': setInt,
            'uniformLower': setInt,
            'cladeLevel0': setInt,
            'cladeLevel1': setInt,
            'cladeLevel2': setInt,
            'cladeLevel3': setInt,
            'level0Name': setString,
            'level1Name': setString,
            'level2Name': setString,
            'level3Name': setString}

        # Setting fields:
        for k, _ in vdict.iteritems():
            if k in fields:
                fields[k](k)

    class Meta:
        ordering = ['cladeLevel0',
                    'cladeLevel1',
                    'cladeLevel2',
                    'cladeLevel3']

    @property
    def languageIds(self):
        return [cl.language_id for cl in self.languageclade_set]


@reversion.register
class Language(models.Model):
    iso_code = models.CharField(max_length=3, blank=True)
    ascii_name = models.CharField(
        max_length=128, unique=True, validators=[suitable_for_url])
    utf8_name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True, null=True)
    clades = models.ManyToManyField(Clade, through="LanguageClade", blank=True)
    beastName = models.CharField(max_length=128, blank=True)  # #130
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

    def isChanged(self, **vdict):

        fields = [
            'iso_code',
            'ascii_name',
            'glottocode',
            'variety',
            'foss_stat',
            'low_stat',
            'soundcompcode',
            'level0',
            'level1',
            'level2',
            'level3',
            'representative',
            'mean_timedepth_BP_years',
            'std_deviation_timedepth_BP_years',
            'rfcWebPath1',
            'rfcWebPath2',
            'author',
            'reviewer',
            'beastName',
            'earliestTimeDepthBound',
            'latestTimeDepthBound',
            'progress',
            'sortRankInClade']

        for f in fields:
            if f in vdict:
                if getattr(self, f) != vdict[f]:
                    return True
        return False

    def setDelta(self, **vdict):
        """
            Alter a models attributes by giving a vdict
            similar to the one used for is_unchanged.
        """

        fields = [
            'iso_code',
            'ascii_name',
            'utf8_name',  # Not checked in isChanged
            'glottocode',
            'variety',
            'foss_stat',
            'low_stat',
            'soundcompcode',
            'level0',
            'level1',
            'level2',
            'level3',
            'representative',
            'mean_timedepth_BP_years',
            'std_deviation_timedepth_BP_years',
            'rfcWebPath1',
            'rfcWebPath2',
            'author',
            'reviewer',
            'beastName',
            'earliestTimeDepthBound',
            'latestTimeDepthBound',
            'progress',
            'sortRankInClade']

        # Escaping special fields:
        if 'ascii_name' in vdict:
            vdict['utf8_name'] = vdict['ascii_name'].encode('utf8', 'ignore')

        # Setting fields:
        for f in fields:
            if f in vdict:
                setattr(self, f, vdict[f])

    def getCsvRow(self, *fields):
        '''
        @return row :: [str]
        '''
        fieldSet = set(['iso_code',
                        'ascii_name',
                        'utf8_name',
                        'description',
                        'clades',
                        'beastName',
                        'earliestTimeDepthBound',
                        'latestTimeDepthBound',
                        'progress',
                        'glottocode',
                        'variety',
                        'soundcompcode',
                        'level0',
                        'level1',
                        'level2',
                        'level3',
                        'mean_timedepth_BP_years',
                        'std_deviation_timedepth_BP_years',
                        'foss_stat',
                        'low_stat',
                        'representative',
                        'rfcWebPath1',
                        'rfcWebPath2',
                        'author',
                        'reviewer',
                        'sortRankInClade',
                        'sndCompLevel0',
                        'sndCompLevel1',
                        'sndCompLevel2',
                        'sndCompLevel3'])

        row = []
        for f in fields:
            if f in fieldSet:
                row.append(str(getattr(self, f)))
        return row

    def getClades(self):
        '''
        This method tries to find the clades closest to a Language.
        @return clades :: [Clade]
        '''
        clades = []
        wanted = [('cladeLevel0', self.level0),
                  ('cladeLevel1', self.level1),
                  ('cladeLevel2', self.level2),
                  ('cladeLevel3', self.level3)]

        for i in xrange(len(wanted), 0, -1):
            try:
                d = dict(wanted[:i])
                no = [c.id for c in clades]
                cs = Clade.objects.filter(**d).exclude(id__in=no).all()
                clades.extend(cs)
            except Exception, e:
                pass

        return clades

    def updateClades(self):
        '''
        This method updates the related LanguageClade models.
        To do so it uses self.getClades to obtain a list of current clades.
        It compares if the clades changed by checking
        if the sets of clade ids are different.
        If so it replaces the old clades by deleting them
        and creating instances for the current clades.
        '''
        currentClades = self.getClades()
        currentIds = set([c.id for c in currentClades])
        oldIds = set([c.id for c in self.clades.all()])
        if currentIds != oldIds:
            # Removing old models:
            self.clades.clear()
            # Adding new models:
            toCreate = [
                LanguageClade(language=self, clade=c, cladesOrder=o)
                for c, o in izip(currentClades, xrange(len(currentClades)))]
            LanguageClade.objects.bulk_create(toCreate)

    @property
    def meaningCount(self):
        return len(set(
            lex.meaning.id for lex in self.lexeme_set.all()))

    @property
    def entryCount(self):
        return len(self.lexeme_set.all())

    @property
    def nonLexCount(self):
        return len([l for l in self.lexeme_set.all()
                    if l.data.get('not_swadesh_term', False)])

    @property
    def lexCount(self):
        return self.entryCount - self.nonLexCount

    @property
    def excessCount(self):
        return self.lexCount - self.meaningCount

    @property
    def firstClade(self):
        try:
            for lc in self.languageclade_set.all():
                if lc.cladesOrder == 0:
                    # Iterating clades is faster than querying db.
                    for c in self.clades.all():
                        if c.id == lc.clade_id:
                            return c
        except:
            return None

    @property
    def level0Tooltip(self):
        try:
            if self.firstClade is not None:
                return self.firstClade.level0Name
        except:
            return ''

    @property
    def level1Tooltip(self):
        try:
            if self.firstClade is not None:
                return self.firstClade.level1Name
        except:
            return ''

    @property
    def level2Tooltip(self):
        try:
            if self.firstClade is not None:
                return self.firstClade.level2Name
        except:
            return ''

    @property
    def level3Tooltip(self):
        try:
            if self.firstClade is not None:
                return self.firstClade.level3Name
        except:
            return ''

    @property
    def hexColor(self):
        try:
            if self.firstClade is not None:
                if self.firstClade.hexColor != '':
                    return self.firstClade.hexColor
        except:
            return None


@receiver(post_save, sender=Language)
def update_language_clades(sender, instance, **kwargs):
    '''
    Making sure clades are updated whenever a language changes:
    '''
    instance.updateClades()


@reversion.register
class LanguageClade(models.Model):
    language = models.ForeignKey(Language)
    clade = models.ForeignKey(Clade)
    # Order in which Language.getClades found these entries:
    cladesOrder = models.IntegerField(default=0, null=False)

    class Meta:
        ordering = ['cladesOrder']


@reversion.register
class Meaning(models.Model):
    gloss = models.CharField(
        max_length=64, unique=True, validators=[suitable_for_url])
    description = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    data = jsonfield.JSONField(blank=True)
    percent_coded = models.FloatField(editable=False, default=0)

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

    def is_unchanged(self, **vdict):

        if 'desc' in vdict:
            vdict['description'] = vdict['desc']

        fields = ['gloss', 'description', 'notes']

        for f in fields:
            if f in vdict:
                if getattr(self, f) != vdict[f]:
                    return False
        return True

    def setDelta(self, **vdict):
        """
            Alter a models attributes by giving a vdict
            similar to the one used for is_unchanged.
        """

        def setField(x):
            setattr(self, x, vdict[x])

        fields = ['gloss', 'description', 'notes']

        if 'desc' in vdict:
            vdict['description'] = vdict['desc']

        # Setting fields:
        for f in fields:
            if f in vdict:
                setattr(self, f, vdict[f])


@reversion.register
@python_2_unicode_compatible
class CognateClass(models.Model):
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
    modified = models.DateTimeField(auto_now=True)
    name = CharNullField(
        max_length=128, blank=True, null=True,
        unique=True, validators=[suitable_for_url])
    root_form = models.TextField(blank=True)
    root_language = models.TextField(blank=True)
    data = jsonfield.JSONField(blank=True)

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

    def is_unchanged(self, **vdict):

        def isField(x):
            return getattr(self, x) == vdict[x]

        def isData(x):
            return self.data.get(x, '') == vdict[x]

        def isY(x):
            return self.data.get(x, False) == vdict.get(x, False)

        fields = {
            'alias': isField,
            'root_form': isField,
            'root_language': isField,
            'notes': isField,
            'gloss_in_root_lang': isData,
            'loan_source': isData,
            'loan_notes': isData,
            'loanword': isY
            }

        for k, _ in vdict.iteritems():
            if k in fields:
                if not fields[k](k):
                    return False
        return True

    def setDelta(self, **vdict):
        """
            Alter a models attributes by giving a vdict
            similar to the one used for is_unchanged.
        """

        def setField(x):
            setattr(self, x, vdict[x])

        def setData(x):
            self.data[x] = vdict[x]

        def setY(x):
            self.data[x] = vdict.get(x, False)

        fields = {
            'alias': setField,
            'notes': setField,
            'root_form': setField,
            'root_language': setField,
            'gloss_in_root_lang': setData,
            'loanword': setY,
            'loan_source': setData,
            'loan_notes': setData}

        # Setting fields:
        for k, _ in vdict.iteritems():
            if k in fields:
                fields[k](k)


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
class Lexeme(models.Model):
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
    data = jsonfield.JSONField(blank=True)
    modified = models.DateTimeField(auto_now=True)
    number_cognate_coded = models.IntegerField(editable=False, default=0)
    denormalized_cognate_classes = models.TextField(editable=False, blank=True)

    def set_denormalized_cognate_classes(self):
        """Create a sequence of 'cc1.id, cc1.alias, cc2.id, cc2.alias'
        as a string and store"""
        old_value = self.denormalized_cognate_classes
        data = []
        for cc in self.cognate_class.all():
            data.append(cc.id)
            judgement = CognateJudgement.objects.get(
                lexeme=self, cognate_class=cc)
            if judgement.is_excluded:
                data.append("(%s)" % cc.alias)
            else:
                data.append(cc.alias)
        self.denormalized_cognate_classes = ",".join(str(e) for e in data)
        if self.denormalized_cognate_classes != old_value:
            self.save()

    def set_number_cognate_coded(self):
        old_number = self.number_cognate_coded
        self.number_cognate_coded = self.cognate_class.count()
        if self.number_cognate_coded != old_number:
            self.save()

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
    # get_cognate_class_links.allow_tags = True # this is only for admin

    def is_excluded_lexeme(self):
        # Tests is_exc for #88
        return ('X' in self.reliability_ratings)

    def is_loan_lexeme(self):
        # Tests is_loan for #88
        return ('L' in self.reliability_ratings)

    def is_excluded_cognate(self):
        # Tests is_exc for #29
        for j in self.cognatejudgement_set.all():
            if j.is_excluded:
                if not j.is_loanword:
                    return True
        return False

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

    def is_unchanged(self, **vdict):

        def isField(x):
            return getattr(self, x) == vdict[x]

        def isData(x):
            return self.data.get(x, '') == vdict[x]

        def isY(x):
            return self.data.get(x, False) == vdict.get(x, False)

        fields = {
            'source_form': isField,
            'phon_form': isField,
            'gloss': isField,
            'notes': isField,
            'phoneMic': isData,
            'transliteration': isData,
            'not_swadesh_term': isY,
            'rfcWebLookup1': isData,
            'rfcWebLookup2': isData,
            'dubious': isY
            }

        try:
            for k, f in fields.iteritems():
                # Fixing boolean fields:
                if f == isY:
                    if k not in vdict:
                        vdict[k] = False
                # Testing for changes:
                if k in vdict:
                    if not f(k):
                        return False
        except Exception, e:
            print('Problem in Lexeme.is_unchanged():', e)
        return True

    def setDelta(self, **vdict):
        """
            Alter a models attributes by giving a vdict
            similar to the one used for is_unchanged.
        """

        def setField(x):
            setattr(self, x, vdict[x])

        def setData(x):
            self.data[x] = vdict[x]

        def setY(x):
            self.data[x] = vdict.get(x, False)

        fields = {
            'source_form': setField,
            'phon_form': setField,
            'gloss': setField,
            'notes': setField,
            'phoneMic': setData,
            'transliteration': setData,
            'not_swadesh_term': setY,
            'rfcWebLookup1': setData,
            'rfcWebLookup2': setData,
            'dubious': setY}

        # Setting fields:
        for k, _ in vdict.iteritems():
            if k in fields:
                fields[k](k)

    def checkLoanEvent(self):
        """
        This method was added for #29 and shall return one of three values:
        * In case that there is exactly one CognateClass linked to this lexeme:
          * Return .data.get('loanword', False)
        * Otherwise return None.
        """
        if self.cognate_class.count() == 1:
            for c in self.cognate_class.all():
                return c.data.get('loanword', False)
        return None

    def getCognateClassData(self):
        """
        This method was added for #90 and shall returns
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

    def setCognateClassData(self, **ccData):
        """
        This method was added for #90 and shall save
        potentially changed cc data for a lexeme.
        @param ccData :: {id: …, root_form: …, root_language: …}
        """
        tuples = izip(
            ccData['cog_class_ids'].split(','),
            ccData['root_form'].split(','),
            ccData['root_language'].split(','))
        for (id, root_form, root_language) in tuples:
            if id == '':
                continue
            cc = CognateClass.objects.get(id=int(id))
            if cc.root_form != root_form or cc.root_language != root_language:
                try:
                    cc.root_form = root_form
                    cc.root_language = root_language
                    cc.save()
                except Exception, e:
                    print('Exception while saving CognateClass: ', e)


@reversion.register
class CognateJudgement(models.Model):
    lexeme = models.ForeignKey(Lexeme)
    cognate_class = models.ForeignKey(CognateClass)
    source = models.ManyToManyField(Source, through="CognateJudgementCitation")
    data = jsonfield.JSONField(blank=True)
    modified = models.DateTimeField(auto_now=True)

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
        descriptions = dict(RELIABILITY_CHOICES)
        return [(rating, descriptions[rating]) for rating in
                sorted(self.reliability_ratings)]

    @property
    def is_loanword(self):
        is_loanword = "L" in self.reliability_ratings
        return is_loanword

    @property
    def is_excluded(self):
        inRel = bool(set(["X", "L"]).intersection(self.reliability_ratings))
        inLex = bool(set(["X", "L"]).intersection(
            self.lexeme.reliability_ratings))
        return inRel or inLex

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

    # TODO how can I make this the default ordering?
    """
    DEFAULT = "2016-04-18_129"
    ALL = "all"

    name = models.CharField(
        max_length=128, unique=True,
        validators=[suitable_for_url, standard_reserved_names])
    description = models.TextField(blank=True, null=True)
    languages = models.ManyToManyField(Language, through="LanguageListOrder")
    data = jsonfield.JSONField(blank=True)
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
        count = self.languagelistorder_set.count()

        def jitter(N, N_list):
            """Return a number close to N such that N is not in N_list"""
            while True:
                try:
                    assert N not in N_list
                    return N
                except AssertionError:
                    N += 0.0001

        if count:
            order_floats = self.languagelistorder_set.values_list(
                "order", flat=True)
            for i, llo in enumerate(self.languagelistorder_set.all()):
                if i != llo.order:
                    llo.order = jitter(i, order_floats)
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
    data = jsonfield.JSONField(blank=True)
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
        count = self.meaninglistorder_set.count()

        def jitter(N, N_list):
            """Return a number close to N such that N is not in N_list"""
            while True:
                try:
                    assert N not in N_list
                    return N
                except AssertionError:
                    N += 0.0001

        if count:
            order_floats = self.meaninglistorder_set.values_list(
                "order", flat=True)
            for i, llo in enumerate(self.meaninglistorder_set.all()):
                if i != llo.order:
                    llo.order = jitter(i, order_floats)
                    llo.save()

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
        ordering = ["order"]
        unique_together = (("meaning_list", "meaning"),
                           ("meaning_list", "order"))


class CognateClassList(models.Model):
    """A named, ordered list of cognate classes for use in display and output. A
    default list, named 'all' is (re)created on save/delete of the CognateClass
    table (cf. ielex.models.update_cognateclass_list_all)

    To get an order list of language from cognateclasslist `ccl`::

        ccl.cognateclasses.all().order_by("cognateclasslistorder")
    """

    DEFAULT = "all"

    name = models.CharField(
        max_length=128,
        validators=[suitable_for_url, standard_reserved_names])
    description = models.TextField(blank=True, null=True)
    cognateclasses = models.ManyToManyField(
        CognateClass, through="CognateClassListOrder")
    modified = models.DateTimeField(auto_now=True)

    def append(self, cognateclass):
        """
        Add another cognateclass to the end of a CognateClassList ordering
        """
        N = self.cognateclasslistorder_set.aggregate(Max("order")).values()[0]
        try:
            N += 1
        except TypeError:
            assert N is None
            N = 0
        CognateClassListOrder.objects.create(
                cognateclass=cognateclass,
                cognateclass_list=self,
                order=N)

    def insert(self, N, cognateclass):
        """
        Insert another cognateclass into a CognateClassList
        ordering before the object position N
        """
        llo = CognateClassListOrder.objects.get(
                cognateclass=cognateclass,
                cognateclass_list=self)
        target = self.cognateclassorder_set.all()[N]
        llo.order = target.order - 0.0001
        llo.save()

    def remove(self, cognateclass):
        llo = CognateClassListOrder.objects.get(
                cognateclass=cognateclass,
                cognateclass_list=self)
        llo.delete()

    def sequentialize(self):
        """Sequentialize the order fields of a CognateClassListOrder set
        with a separation of approximately 1.0.  This is a bit slow, so
        it should only be done from time to time."""
        count = self.cognateclasslistorder_set.count()

        def jitter(N, N_list):
            """Return a number close to N such that N is not in N_list"""
            while True:
                try:
                    assert N not in N_list
                    return N
                except AssertionError:
                    N += 0.0001

        if count:
            order_floats = self.cognateclasslistorder_set.values_list(
                "order", flat=True)
            for i, llo in enumerate(self.cognateclasslistorder_set.all()):
                if i != llo.order:
                    llo.order = jitter(i, order_floats)
                    llo.save()

    def swap(self, cognateclassA, cognateclassB):
        """Swap the order of two meanings"""
        orderA = CognateClassListOrder.objects.get(
                cognateclass=cognateclassA,
                cognateclass_list=self)
        orderB = CognateClassListOrder.objects.get(
                cognateclass=cognateclassB,
                cognateclass_list=self)
        orderB.delete()
        orderA.order, orderB.order = orderB.order, orderA.order
        orderA.save()
        orderB.save()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class CognateClassListOrder(models.Model):

    cognateclass = models.ForeignKey(CognateClass)
    cognateclass_list = models.ForeignKey(CognateClassList)
    order = models.FloatField()

    def __unicode__(self):
        return u"%s:%s(%s)" % (self.cognateclass_list.name,
                               self.order,
                               self.cognateclass.alias)

    class Meta:
        ordering = ["order"]
        unique_together = (("cognateclass_list", "cognateclass"),
                           ("cognateclass_list", "order"))


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
def update_cognateclass_list_all(sender, instance, **kwargs):
    """
    Update the CognateClassList 'all' whenever CognateClass table is changed
    """
    ccl, _ = CognateClassList.objects.get_or_create(
        name=CognateClassList.DEFAULT)
    ccl.sequentialize()

    missing_cognateclasses = \
        set(CognateClass.objects.all()) - set(ccl.cognateclasses.all())
    for cogclass in missing_cognateclasses:
        ccl.append(cogclass)

    if missing_cognateclasses:
        # make a new alphabetized list
        default_alpha = CognateClassList.DEFAULT+"-alpha"
        try:
            ml_alpha = CognateClassList.objects.get(name=default_alpha)
            ml_alpha.delete()
        except CognateClassList.DoesNotExist:
            pass
        ccl_alpha = CognateClassList.objects.create(name=default_alpha)
        for cgclss in CognateClass.objects.all().order_by("alias"):
            ccl_alpha.append(cgclss)

models.signals.post_save.connect(
    update_cognateclass_list_all, sender=CognateClass)
models.signals.post_delete.connect(
    update_cognateclass_list_all, sender=CognateClass)


@disable_for_loaddata
def update_denormalized_data(sender, instance, **kwargs):
    try:
        if sender in [CognateJudgement, LexemeCitation]:
            lexeme = instance.lexeme
        elif sender == CognateJudgementCitation:
            try:
                lexeme = instance.cognate_judgement.lexeme
            except CognateJudgement.DoesNotExist:
                # e.g. if the cognate judgement
                # citation is deleted automatically because the cognate
                # judgement has been deleted
                return
        if sender in [CognateJudgement, CognateJudgementCitation]:
            lexeme.set_number_cognate_coded()
        lexeme.set_denormalized_cognate_classes()
    except Lexeme.DoesNotExist:
        pass  # must have been deleted

models.signals.post_save.connect(
    update_denormalized_data, sender=CognateJudgement)
models.signals.post_delete.connect(
    update_denormalized_data, sender=CognateJudgement)

models.signals.post_save.connect(
    update_denormalized_data, sender=CognateJudgementCitation)
models.signals.post_delete.connect(
    update_denormalized_data, sender=CognateJudgementCitation)

models.signals.post_save.connect(
    update_denormalized_data, sender=LexemeCitation)
models.signals.post_delete.connect(
    update_denormalized_data, sender=LexemeCitation)


@disable_for_loaddata
def update_denormalized_from_lexeme(sender, instance, **kwargs):
    instance.meaning.set_percent_coded()

models.signals.post_save.connect(
    update_denormalized_from_lexeme, sender=Lexeme)
models.signals.post_delete.connect(
    update_denormalized_from_lexeme, sender=Lexeme)


@reversion.register
class Author(models.Model):
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

    def is_unchanged(self, **vdict):
        fields = ['surname', 'firstNames', 'email', 'website', 'initials']

        for f in fields:
            if f in vdict:
                if vdict[f] != getattr(self, f):
                    return False

        return True

    def setDelta(self, **vdict):
        """
            Alter a models attributes by giving a vdict
            similar to the one used for is_unchanged.
        """
        fields = ['surname', 'firstNames', 'email', 'website', 'initials']

        for f in fields:
            if f in vdict:
                setattr(self, f, vdict[f])

    class Meta:
        ordering = ["surname", "firstNames"]
