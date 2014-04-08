from __future__ import division
from string import uppercase, lowercase
from django.db import models
from django.db.models import Max, F
from django.core.urlresolvers import reverse
## from django.core.cache import cache
from django.db import connection, transaction ### testing
from django.db import IntegrityError
from django.dispatch import receiver
from django.db.models.signals import pre_delete, post_delete
from django.db.backends.signals import connection_created
from django.utils.safestring import SafeString
# from django.contrib import admin
import reversion
from reversion.revisions import RegistrationError
# from reversion.admin import VersionAdmin # reinstate?
from south.modelsinspector import add_introspection_rules
from ielex.utilities import two_by_two
from ielex.lexicon.validators import *

### from https://code.djangoproject.com/ticket/8399
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
### end

## TODO: reinstate the cache stuff, but using a site specific key prefix (maybe
## the short name of the database

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

# http://south.aeracode.org/docs/customfields.html#extending-introspection
add_introspection_rules([], ["^ielex\.lexicon\.models\.CharNullField"])

class CharNullField(models.CharField):
	"""CharField that stores NULL but returns ''
    This is important for uniqueness checks where multiple null values
    are allowed (following ANSI SQL standard). For example, if
    CognateClass objects have an explicit name, it must be unique, but
    having a name is optional."""
	def to_python(self, value):
		if isinstance(value, models.CharField):
			return value 
		if value==None:
			return ""
		else:
			return value
	def get_prep_value(self, value):
        # this was get_db_prep_value, but that is for database specific things
		if value=="":
			return None
		else:
			return value

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

class Language(models.Model):
    iso_code = models.CharField(max_length=3, blank=True)
    ascii_name = models.CharField(max_length=128, unique=True,
            validators=[suitable_for_url])
    utf8_name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True, null=True)

    def get_absolute_url(self):
        return "/language/%s/" % self.ascii_name

    def __unicode__(self):
        return self.utf8_name

    class Meta:
        ordering = ["ascii_name"]

class DyenName(models.Model):
    language = models.ForeignKey(Language)
    name = models.CharField(max_length=128)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

class Meaning(models.Model):
    gloss = models.CharField(max_length=64, validators=[suitable_for_url])
    description = models.CharField(max_length=64, blank=True) # show name
    notes = models.TextField(blank=True)
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
        return

    def __unicode__(self):
        return self.gloss.upper()

    class Meta:
        ordering = ["gloss"]

class CognateClass(models.Model):
    """`name` field is optional, for manually given names"""
    alias = models.CharField(max_length=3)
    notes = models.TextField(blank=True)
    modified = models.DateTimeField(auto_now=True)
    name = CharNullField(max_length=128, blank=True, null=True, unique=True,
            validators=[suitable_for_url])

    def update_alias(self, save=True):
        """Reset alias to the first unused letter"""
        codes = set(uppercase) | set([i+j for i in uppercase for j in
            lowercase])
        meanings = Meaning.objects.filter(lexeme__cognate_class=self).distinct()
        current_aliases = CognateClass.objects.filter(
                lexeme__meaning__in=meanings).distinct().exclude(
                id=self.id).values_list("alias", flat=True)
        codes -= set(current_aliases)
        self.alias = sorted(codes, key=lambda i:(len(i), i))[0]
        if save:
            self.save()
        return

    def get_meanings(self):
        # some cognate classes have more than one meaning, e.g. "right" ~
        # "rightside", "in" ~ "at"
        meanings = Meaning.objects.filter(lexeme__cognate_class=self).distinct()
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

class DyenCognateSet(models.Model):
    cognate_class = models.ForeignKey(CognateClass)
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
    cognate_class = models.ManyToManyField(CognateClass,
            through="CognateJudgement", blank=True)
    source_form = models.CharField(max_length=128)
    phon_form = models.CharField(max_length=128, blank=True)
    gloss = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    source = models.ManyToManyField(Source, through="LexemeCitation",
            blank=True)
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
            if CognateJudgement.objects.get(lexeme=self,
                    cognate_class=cc).is_excluded:
                data.append("(%s)" % cc.alias)
            else:
                data.append(cc.alias)
        self.denormalized_cognate_classes = ",".join(str(e) for e in data)
        if self.denormalized_cognate_classes != old_value:
            self.save()
        return

    def set_number_cognate_coded(self):
        old_number = self.number_cognate_coded 
        self.number_cognate_coded = self.cognate_class.count()
        if self.number_cognate_coded != old_number:
            self.save()
        return

    def get_cognate_class_links(self):
        def format_link(cc_id, alias):
            if alias.startswith("(") and alias.endswith(")"):
                template = '(<a href="/cognate/%s/">%s</a>)'
                alias = alias[1:-1]
            else:
                template = '<a href="/cognate/%s/">%s</a>'
            return template % (cc_id, alias)
        return  SafeString(", ".join(format_link(cc_id, alias) for cc_id, alias in
                        two_by_two(self.denormalized_cognate_classes.split(","))))
    # get_cognate_class_links.allow_tags = True # this is only for admin

    @property
    def reliability_ratings(self):
        return set(self.lexemecitation_set.values_list("reliability", flat=True))

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


class CognateJudgement(models.Model):
    lexeme = models.ForeignKey(Lexeme)
    cognate_class = models.ForeignKey(CognateClass)
    source = models.ManyToManyField(Source, through="CognateJudgementCitation")
    modified = models.DateTimeField(auto_now=True)

    # def get_absolute_url(self):
    #     return "/meaning/%s/%s/%s/" % (self.lexeme.meaning.gloss,
    #             self.lexeme.id, self.id)

    def get_absolute_url(self):
        anchor = "cognatejudgement_%s" % self.id
        return self.lexeme.get_absolute_url(anchor)

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
        is_loanword = "L" in self.reliability_ratings
        return is_loanword

    @property
    def is_excluded(self):
        return bool(set(["X","L"]).intersection(self.reliability_ratings)) or \
                bool(set(["X","L"]).intersection(self.lexeme.reliability_ratings))

    def __unicode__(self):
        return u"%s-%s-%s" % (self.lexeme.meaning.gloss,
                self.cognate_class.alias, self.id)

class LanguageList(models.Model):
    """A named, ordered list of languages for use in display and output. A
    default list, named 'all' is (re)created on save/delete of the Language
    table (cf. ielex.models.update_language_list_all)

    To get an order list of language from LanguageList `ll`::

        ll.languages.all().order_by("languagelistorder")

    # TODO how can I make this the default ordering?
    """
    DEFAULT = "all" # all languages

    name = models.CharField(max_length=128, unique=True, 
            validators=[suitable_for_url, reserved_names("all", "all-alpha")])
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
        return

    def insert(self, N, language):
        """Insert another language into a LanguageList ordering before the object position N"""
        llo = LanguageListOrder.objects.get(
                language=language,
                language_list=self)
        target = self.languagelistorder_set.all()[N]
        llo.order = target.order - 0.0001
        llo.save()
        return

    def remove(self, language):
        llo = LanguageListOrder.objects.get(
                language=language,
                language_list=self)
        llo.delete()
        return

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
            return
        if count:
            order_floats = self.languagelistorder_set.values_list("order", flat=True)
            for i, llo in enumerate(self.languagelistorder_set.all()):
                if i != llo.order:
                    llo.order = jitter(i, order_floats)
                    llo.save()
        return

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
        return

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

class MeaningList(models.Model):
    """Named lists of meanings, e.g. 'All' and 'Swadesh_100'"""
    DEFAULT = "all"

    name = models.CharField(max_length=128,
            validators=[suitable_for_url, reserved_names("all", "all-alpha")])
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
        return

    def insert(self, N, meaning):
        """Insert another meaning into a MeaningList ordering before the object position N"""
        llo = MeaningListOrder.objects.get(
                meaning=meaning,
                meaning_list=self)
        target = self.meaninglistorder_set.all()[N]
        llo.order = target.order - 0.0001
        llo.save()
        return

    def remove(self, meaning):
        llo = MeaningListOrder.objects.get(
                meaning=meaning,
                meaning_list=self)
        llo.delete()
        return

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
            return
        if count:
            order_floats = self.meaninglistorder_set.values_list("order", flat=True)
            for i, llo in enumerate(self.meaninglistorder_set.all()):
                if i != llo.order:
                    llo.order = jitter(i, order_floats)
                    llo.save()
        return

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
        return

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

# class GenericCitation(models.Model):
#     # This would have been a good way to do it, but it's going to be too
#     # difficult to convert the ManyToMany fields in the current models to use
#     # this instead of the old classes.
#     source = models.ForeignKey(Source)
#     content_type = models.ForeignKey(ContentType)
#     object_id = models.PositiveIntegerField()
#     content_object = generic.GenericForeignKey('content_type',
#                     'object_id')
#     pages = models.CharField(max_length=128, blank=True)
#     reliability = models.CharField(max_length=1, choices=RELIABILITY_CHOICES)
#     comment = models.TextField(blank=True)
#     modified = models.DateTimeField(auto_now=True)
# 
#     def long_reliability(self):
#         try:
#             description = dict(RELIABILITY_CHOICES)[self.reliability]
#         except KeyError:
#             description = ""
#         return description
# 
#     class Meta:
#         unique_together = (("content_type", "object_id", "source"),)
#         ## Can't use a "content_object" in a unique_together constraint
# 
# # reversion.register(GenericCitation)

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


class CognateJudgementCitation(AbstractBaseCitation):
    cognate_judgement = models.ForeignKey(CognateJudgement)
    source = models.ForeignKey(Source)

    # def get_absolute_url(self):
    #     return reverse("cognate-judgement-citation-detail",
    #             kwargs={"pk":self.id})

    def get_absolute_url(self):
        anchor = "cognatejudgementcitation_%s" % self.id
        return self.cognate_judgement.lexeme.get_absolute_url(anchor)

    def __unicode__(self):
        return u"CJC src=%s cit=%s" % (self.source.id, self.id)

    class Meta:

        unique_together = (("cognate_judgement", "source"),)


class LexemeCitation(AbstractBaseCitation):
    lexeme = models.ForeignKey(Lexeme)
    source = models.ForeignKey(Source)

    # def get_absolute_url(self):
    #     return "/lexeme/citation/%s/" % self.id

    def get_absolute_url(self):
        anchor = "lexemecitation_%s" % self.id
        return self.lexeme.get_absolute_url(anchor)

    def __unicode__(self):
        return u"%s %s src:%s" % (self.id, self.lexeme.source_form, self.source.id)

    class Meta:
        unique_together = (("lexeme", "source"),)

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
                # self.cognate_class.id, self.source.id)

    def get_absolute_url(self):
        return reverse("cognate-class-citation-detail",
                kwargs={"pk":self.id})

    class Meta:
        unique_together = (("cognate_class", "source"),)

# @receiver(post_delete, sender=CognateJudgementCitation)
# def check_cognate_judgement_has_citation(sender, instance, **kwargs):
#     try:
#         if instance.cognate_judgement.source.count() == 0:
#             instance.save() # reinstate object
#             raise IntegrityError(
#                     "This deletion would leave parent without citations")
#     except CognateJudgement.DoesNotExist:
#         pass # parent has been deleted
# 
# @receiver(post_delete, sender=LexemeCitation)
# def check_lexeme_has_citation(sender, instance, **kwargs):
#     #_delete = getattr(instance.lexeme, "_delete", False)
#     try:
#         if instance.lexeme.source.count() == 0:
#             instance.save() # reinstate object
#             raise IntegrityError(
#                     "This deletion would leave parent without citations")
#     except Lexeme.DoesNotExist:
#         pass # parent has been deleted

@disable_for_loaddata
def update_language_list_all(sender, instance, **kwargs):
    """Update the LanguageList 'all' whenever Language table is changed"""
    ll, _ = LanguageList.objects.get_or_create(name=LanguageList.DEFAULT)
    ll.sequentialize()

    missing_langs = set(Language.objects.all()) - set(ll.languages.all())
    for language in missing_langs:
        ll.append(language)

    if missing_langs:
        # make a new alphabetized list
        default_alpha = LanguageList.DEFAULT+"-alpha"
        try: # zap the old one
            ll_alpha = LanguageList.objects.get(name=default_alpha)
            ll_alpha.delete()
        except LanguageList.DoesNotExist:
            pass
        ll_alpha = LanguageList.objects.create(name=default_alpha)
        for language in Language.objects.all().order_by("ascii_name"):
            ll_alpha.append(language)
    return

models.signals.post_save.connect(update_language_list_all, sender=Language)
models.signals.post_delete.connect(update_language_list_all, sender=Language)

@disable_for_loaddata
def update_meaning_list_all(sender, instance, **kwargs):
    ml, _ = MeaningList.objects.get_or_create(name=MeaningList.DEFAULT)
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
    return

models.signals.post_save.connect(update_meaning_list_all, sender=Meaning)
models.signals.post_delete.connect(update_meaning_list_all, sender=Meaning)

@disable_for_loaddata
def update_denormalized_data(sender, instance, **kwargs):
    try:
        if sender in [CognateJudgement, LexemeCitation]:
            lexeme = instance.lexeme
        elif sender == CognateJudgementCitation:
            try:
                lexeme = instance.cognate_judgement.lexeme
            except CognateJudgement.DoesNotExist: # e.g. if the cognate judgement
                return      # citation is deleted automatically because the cognate
                            # judgement has been deleted
        if sender in [CognateJudgement, CognateJudgementCitation]:
            lexeme.set_number_cognate_coded()
        lexeme.set_denormalized_cognate_classes()
    except Lexeme.DoesNotExist:
        pass # must have been deleted
    return

models.signals.post_save.connect(update_denormalized_data,
        sender=CognateJudgement)
models.signals.post_delete.connect(update_denormalized_data,
        sender=CognateJudgement)

models.signals.post_save.connect(update_denormalized_data,
        sender=CognateJudgementCitation)
models.signals.post_delete.connect(update_denormalized_data,
        sender=CognateJudgementCitation)

models.signals.post_save.connect(update_denormalized_data,
        sender=LexemeCitation)
models.signals.post_delete.connect(update_denormalized_data,
        sender=LexemeCitation)

@disable_for_loaddata
def update_denormalized_from_lexeme(sender, instance, **kwargs):
    instance.meaning.set_percent_coded()
    return

models.signals.post_save.connect(update_denormalized_from_lexeme,
        sender=Lexeme)
models.signals.post_delete.connect(update_denormalized_from_lexeme,
        sender=Lexeme)

# -- Reversion registration ----------------------------------------

# once we're upgraded to 1.5.1 this might not be necessary anymore
for modelclass in [Source, Language, Meaning, CognateClass, Lexeme,
        CognateJudgement, LanguageList, LanguageListOrder,
        CognateJudgementCitation, CognateClassCitation, LexemeCitation,
        MeaningList]:
    if not reversion.is_registered(modelclass):
        reversion.register(modelclass)

