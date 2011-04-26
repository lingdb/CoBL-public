from __future__ import division
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
# from django.contrib import admin
import reversion
# from reversion.admin import VersionAdmin
from ielex.lexicon.validators import *

TYPE_CHOICES = (
        ("P", "Publication"),
        ("U", "URL"),
        ("E", "Expert"),
        )

RELIABILITY_CHOICES = ( # used by Citation classes
        #("X", "Unclassified"), # change "X" to "" will force users to make
        ("A", "High"),         # a selection upon seeing this form
        ("B", "Good (e.g. should be double checked)"),
        ("C", "Doubtful"),
        ("L", "Loanword"),
        ("X", "Exclude (e.g. not the Swadesh term)"),
        )

class Source(models.Model):

    citation_text = models.TextField(unique=True)
    type_code = models.CharField(max_length=1, choices=TYPE_CHOICES,
            default="P")
    description = models.TextField(blank=True)
    modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "/source/%s/" % self.id

    def __unicode__(self):
        return self.citation_text[:64]

    class Meta:
        ordering = ["type_code", "citation_text"]

reversion.register(Source)

class Language(models.Model):
    iso_code = models.CharField(max_length=3, blank=True)
    ascii_name = models.CharField(max_length=999, unique=True,
            validators=[suitable_for_url])
    utf8_name = models.CharField(max_length=999, unique=True)
    # sort key is deprecated: use ordered_manager instead
    sort_key = models.FloatField(null=True, blank=True, editable=False)
    description = models.TextField(blank=True, null=True)

    def get_absolute_url(self):
        return "/language/%s/" % self.ascii_name

    # @property
    def percent_coded(self):
        uncoded = self.lexeme_set.filter(cognate_class=None).count()
        total = self.lexeme_set.all().count()
        try:
            return int(100.0 * (total - uncoded) / total)
        except ZeroDivisionError:
            return ""

    def __unicode__(self):
        return self.utf8_name

    class Meta:
        ordering = ["ascii_name"]

reversion.register(Language)

def make_ordered_language_manager(language_list):
    """Selects a set of languages according to a LanguageList object
    (and annotates them with an order attribute).
    Usage:
        LanguageListManager = make_ordered_language_manager(language_list)
        Language.language_list = LanguageListManager()
        languages = Language.language_list.with_order()
        languages.sort(key=lambda m: m.order)
    """
    class OrderedLanguageManager(models.Manager):
        def get_query_set(self):
            return Language.objects.filter(id__in=language_list.language_id_list)
        def with_order(self):
            languages = []
            for language in self.get_query_set():
                language.order = language_list.language_id_list.index(language.id)
                languages.append(language)
            return languages
    return OrderedLanguageManager

class DyenName(models.Model):
    language = models.ForeignKey(Language)
    name = models.CharField(max_length=999)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

class Meaning(models.Model):
    gloss = models.CharField(max_length=64, validators=[suitable_for_url])
    description = models.CharField(max_length=64, blank=True) # show name
    notes = models.TextField(blank=True)

    def get_absolute_url(self):
        return "/meaning/%s/" % self.gloss

    @property
    def percent_coded(self):
        uncoded = self.lexeme_set.filter(meaning=self, cognate_class=None).count()
        total = self.lexeme_set.filter(meaning=self).count()
        try:
            return int(100.0 * (total - uncoded) / total)
        except ZeroDivisionError:
            return ""

    def __unicode__(self):
        return self.gloss.upper()

    class Meta:
        ordering = ["gloss"]

reversion.register(Meaning)

def make_ordered_meaning_manager(wordlist):
    """Usage:
        WordlistManager = make_ordered_meaning_manager(wordlist)
        Meaning.wordlist = WordlistManager()
        meanings = Meaning.wordlist.with_order()
        meanings.sort(key=lambda m: m.order)
    """
    class OrderedMeaningManager(models.Manager):
        def get_query_set(self):
            return Meaning.objects.filter(id__in=wordlist.meaning_id_list)
        def with_order(self):
            meanings = []
            for meaning in self.get_query_set():
                meaning.order = wordlist.meaning_id_list.index(meaning.id)
                meanings.append(meaning)
            return meanings
    return OrderedMeaningManager

class CognateSet(models.Model):
    alias = models.CharField(max_length=3)
    notes = models.TextField()
    modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "/cognate/%s/" % self.id

    def __unicode__(self):
        return unicode(self.id)

    class Meta:
        ordering = ["alias"]

reversion.register(CognateSet)

class DyenCognateSet(models.Model):
    cognate_class = models.ForeignKey(CognateSet)
    name = models.CharField(max_length=8)
    doubtful = models.BooleanField(default=0)

    def __unicode__(self):
        if self.doubtful:
            qmark = " ?"
        else:
            qmark =""
        return "%s%s" % (self.name, qmark)

class Lexeme(models.Model):
    language = models.ForeignKey(Language)
    meaning = models.ForeignKey(Meaning, blank=True, null=True)
    cognate_class = models.ManyToManyField(CognateSet,
            through="CognateJudgement", blank=True)
    source_form = models.CharField(max_length=999)
    phon_form = models.CharField(max_length=999, blank=True)
    gloss = models.CharField(max_length=999, blank=True)
    notes = models.TextField(blank=True)
    source = models.ManyToManyField(Source, through="LexemeCitation",
            blank=True)
    modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "/lexeme/%s/" % self.id

    def get_absolute_url(self):
        return "/lexeme/%s/" % self.id

    def __unicode__(self):
        return self.phon_form or self.source_form or ("Lexeme %s" % self.id)

    class Meta:
        order_with_respect_to = "language"

reversion.register(Lexeme)

def make_ordered_lexeme_manager(meaning, language_list):
    """Selects a set of lexemes according to a LanguageList object sorted by
    Language (and annotates them with an order attribute).
    Usage:
        LexemeListManager = make_ordered_lexeme_manager(meaning, language_list)
        Lexeme.language_list = LexemeListManager()
        lexemes = Lexeme.language_list.with_order()
        lexemes.sort(key=lambda m: m.order)
    """
    class OrderedLexemeManager(models.Manager):
        def get_query_set(self):
            return Lexeme.objects.filter(meaning=meaning,
                    language__id__in=language_list.language_id_list)
        def with_order(self):
            lexemes = []
            for lexeme in self.get_query_set():
                lexeme.order = language_list.language_id_list.index(lexeme.language.id)
                lexemes.append(lexeme)
            return lexemes
    return OrderedLexemeManager

class CognateJudgement(models.Model):
    lexeme = models.ForeignKey(Lexeme)
    cognate_class = models.ForeignKey(CognateSet)
    source = models.ManyToManyField(Source, through="CognateJudgementCitation")
    modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "/meaning/%s/%s/%s/" % (self.lexeme.meaning.gloss,
                self.lexeme.id, self.id)

    @property
    def reliability_ratings(self):
        return set(self.cognatejudgementcitation_set.values_list("reliability", flat=True))

    @property
    def long_reliability_ratings(self):
        """An alphabetically sorted list of (rating_code, description) tuples"""
        descriptions = dict(RELIABILITY_CHOICES)
        return [(rating, descriptions[rating]) for rating in sorted(self.reliability_ratings)]

    @property
    def is_loanword(self):
        return "L" in self.reliability_ratings

    def __unicode__(self):
        return u"%s-%s-%s" % (self.lexeme.meaning.gloss,
                self.cognate_class.alias, self.id)

reversion.register(CognateJudgement)

class LanguageList(models.Model):
    """A named, ordered list of languages for use in display and output. A
    default list, named 'all' is (re)created on save/delete of the Language
    table (cf. ielex.models.update_language_list_all)"""
    DEFAULT = "all"

    name = models.CharField(max_length=999, validators=[suitable_for_url])
    description = models.TextField(blank=True, null=True)
    language_ids = models.CommaSeparatedIntegerField(max_length=999)
    modified = models.DateTimeField(auto_now=True)

    def _get_list(self):
        try:
            return [int(i) for i in self.language_ids.split(",")]
        except ValueError:
            return []
    def _set_list(self, listobj):
        self.language_ids = ",".join([str(i) for i in listobj])
        return
    language_id_list = property(_get_list, _set_list)

    def get_absolute_url(self):
        return "/languages/"

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

reversion.register(LanguageList)

class MeaningList(models.Model):
    """Named lists of meanings, e.g. 'All' and 'Swadesh_100'"""
    DEFAULT = "all"

    name = models.CharField(max_length=999, validators=[suitable_for_url])
    description = models.TextField(blank=True, null=True)
    meaning_ids = models.CommaSeparatedIntegerField(max_length=999)
    modified = models.DateTimeField(auto_now=True)

    def _get_list(self):
        try:
            return [int(i) for i in self.meaning_ids.split(",")]
        except ValueError:
            return []
    def _set_list(self, listobj):
        self.meaning_ids = ",".join([str(i) for i in listobj])
        return
    meaning_id_list = property(_get_list, _set_list)

    def get_absolute_url(self):
        return "/meanings/"

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class GenericCitation(models.Model):
    # This would have been a good way to do it, but it's going to be too
    # difficult to convert the ManyToMany fields in the current models to use
    # this instead of the old classes.
    source = models.ForeignKey(Source)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type',
                    'object_id')
    pages = models.CharField(max_length=999)
    reliability = models.CharField(max_length=1, choices=RELIABILITY_CHOICES)
    comment = models.CharField(max_length=999)
    modified = models.DateTimeField(auto_now=True)

    def long_reliability(self):
        try:
            description = dict(RELIABILITY_CHOICES)[self.reliability]
        except KeyError:
            description = ""
        return description

    class Meta:
        unique_together = (("content_type", "object_id", "source"),)
        ## Can't use a "content_object" in a unique_together constraint

# reversion.register(GenericCitation)

class AbstractBaseCitation(models.Model):
    # TODO remove
    """Abstract base class for citation models
    The source field has to be in the subclasses in order for the
    unique_together constraints to work properly"""
    pages = models.CharField(max_length=999)
    reliability = models.CharField(max_length=1, choices=RELIABILITY_CHOICES)
    comment = models.CharField(max_length=999)
    modified = models.DateTimeField(auto_now=True)

    def long_reliability(self):
        try:
            description = dict(RELIABILITY_CHOICES)[self.reliability]
        except KeyError:
            description = ""
        return description

    class Meta:
        abstract = True


class CognateJudgementCitation(AbstractBaseCitation):
    # TODO remove
    cognate_judgement = models.ForeignKey(CognateJudgement)
    source = models.ForeignKey(Source)

    def get_absolute_url(self):
        return "/lexeme/%s/edit-cognate-citation/%s/" % \
                (self.cognate_judgement.lexeme.id, self.id)
        # TODO "/citation/cognate/%s/"

    def __unicode__(self):
        return u"CJC src=%s cit=%s" % (self.source.id, self.id)

    class Meta:

        unique_together = (("cognate_judgement", "source"),)

reversion.register(CognateJudgementCitation)

class LexemeCitation(AbstractBaseCitation):
    # TODO remove
    lexeme = models.ForeignKey(Lexeme)
    source = models.ForeignKey(Source)

    def get_absolute_url(self):
        return "/lexeme/%s/edit-citation/%s/" % (self.lexeme.id, self.id)
        # TODO "/citation/lexeme/%s/"

    def __unicode__(self):
        return u"%s src=%s cit=%s" % (self.lexeme.source_form, self.source.id,
                self.id)

    class Meta:
        unique_together = (("lexeme", "source"),)

reversion.register(LexemeCitation)

def update_language_list_all(sender, instance, **kwargs):
    """Update the LanguageList 'all' whenever Language table is changed"""
    ll, _ = LanguageList.objects.get_or_create(name=LanguageList.DEFAULT)
    missing_ids = set(Language.objects.values_list("id", flat=True)) - set(ll.language_id_list)
    if missing_ids:
        ll.language_id_list = sorted(missing_ids) + ll.language_id_list
        ll.save(force_update=True)

    # make alphabetized list
    default_alpha = LanguageList.DEFAULT+"-alpha"
    ids = [i for n, i in sorted([(n.lower(), i) for n, i
        in Language.objects.values_list("ascii_name", "id")])]
    ll_alpha, _ = LanguageList.objects.get_or_create(name=default_alpha)
    ll_alpha.language_id_list = ids
    ll_alpha.save(force_update=True)
    return

models.signals.post_save.connect(update_language_list_all, sender=Language)
models.signals.post_delete.connect(update_language_list_all, sender=Language)

def update_meaning_list_all(sender, instance, **kwargs):
    try:
        ml = MeaningList.objects.get(name=MeaningList.DEFAULT)
    except:
        ml = MeaningList.objects.create(name=MeaningList.DEFAULT)
    # recreate this if the membership has changed but not if just the
    # order has changed
    missing_ids = set(Meaning.objects.values_list("id", flat=True)) - set(ml.meaning_id_list)
    if missing_ids:
        ml.meaning_id_list = sorted(missing_ids) + ml.meaning_id_list
        ml.save(force_update=True)
    return

models.signals.post_save.connect(update_meaning_list_all, sender=Meaning)
models.signals.post_delete.connect(update_meaning_list_all, sender=Meaning)

# def update_aliases(sender, instance, **kwargs):
#     """In case a cognate set has cognate judgements relating to two or more
#     meanings, make sure that the cognate set alias doesn't collide with any
#     other the others"""
#     meanings = cs.cognatejudgement_set.values_list("lexeme__meaning",
#             flat=True).distinct()
#     if meanings.count() > 1:
#         for meaning in meanings:
#             # do something
# 

