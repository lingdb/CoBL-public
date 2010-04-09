from __future__ import division
from django.db import models
import reversion
from django.contrib import admin
from reversion.admin import VersionAdmin

class Source(models.Model):

    TYPE_CHOICES = (
            ("P", "Publication"),
            ("U", "URL"),
            ("E", "Expert"),
            )
    RELIABILITY_CHOICES = ( # used by Citation classes
            #("X", "Unclassified"), # change "X" to "" will force users to make
            ("A", "High"),         # a selection upon seeing this form
            ("B", "Good, but needs checking by an expert"),
            ("C", "Doubtful"),
            )
    citation_text = models.TextField()
    type_code = models.CharField(max_length=1, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    modified = models.DateTimeField(auto_now=True)

    @property
    def canonical_url(self):
        return "/source/%s/" % self.id

    def __unicode__(self):
        return self.citation_text[:64]

    class Meta:
        ordering = ["type_code", "citation_text"]

#reversion.register(Source)
class SourceAdmin(VersionAdmin):
    pass

admin.site.register(Source, SourceAdmin)

class Language(models.Model):
    iso_code = models.CharField(max_length=3, blank=True)
    ascii_name = models.CharField(max_length=999)
    utf8_name = models.CharField(max_length=999)
    sort_key = models.FloatField(null=True, blank=True, editable=False)

    @property
    def canonical_url(self):
        return "/language/%s/" % self.ascii_name

    @property
    def percent_coded(self):
        uncoded = self.lexeme_set.filter(cognate_class=None).count()
        total = self.lexeme_set.all().count()
        try:
            return int(100 * (total - uncoded) / total)
        except ZeroDivisionError:
            return ""

    def __unicode__(self):
        return self.ascii_name

    class Meta:
        ordering = ["sort_key", "utf8_name"]

reversion.register(Language)

class DyenName(models.Model):
    language = models.ForeignKey(Language)
    name = models.CharField(max_length=999)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

class Meaning(models.Model):
    gloss = models.CharField(max_length=64) # one word name
    description = models.CharField(max_length=64) # show name
    notes = models.TextField()

    @property
    def canonical_url(self):
        return "/meaning/%s/" % self.gloss

    def __unicode__(self):
        return self.gloss.upper()

    class Meta:
        ordering = ["gloss"]

reversion.register(Meaning)

class CognateSet(models.Model):
    alias = models.CharField(max_length=3)
    notes = models.TextField()
    modified = models.DateTimeField(auto_now=True)

    @property
    def canonical_url(self):
        return "/cognate/%s/" % self.id

    def __unicode__(self):
        return unicode(self.id)

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
    meaning = models.ForeignKey(Meaning)
    cognate_class = models.ManyToManyField(CognateSet,
            through="CognateJudgement")
    source_form = models.CharField(max_length=999)
    phon_form = models.CharField(max_length=999)
    gloss = models.CharField(max_length=999)
    notes = models.TextField()
    source = models.ManyToManyField(Source, through="LexemeCitation")
    modified = models.DateTimeField(auto_now=True)

    @property
    def canonical_url(self):
        return "/lexeme/%s/" % self.id

    def __unicode__(self):
        return self.phon_form or self.source_form or "Lexeme"

    class Meta:
        order_with_respect_to = "language"

reversion.register(Lexeme)

class CognateJudgement(models.Model):
    lexeme = models.ForeignKey(Lexeme)
    cognate_class = models.ForeignKey(CognateSet)
    source = models.ManyToManyField(Source, through="CognateJudgementCitation")
    modified = models.DateTimeField(auto_now=True)

    @property
    def canonical_url(self):
        return "/meaning/%s/%s/%s/" % (self.lexeme.meaning.gloss,
                self.lexeme.id, self.id)

    @property
    def reliability_ratings(self):
        return set(self.cognatejudgementcitation_set.values_list("reliability", flat=True))

    def __unicode__(self):
        return u"%s-%s-%s" % (self.lexeme.meaning.gloss,
                self.cognate_class.alias, self.id)

reversion.register(CognateJudgement)

class LanguageList(models.Model):
    """A named, ordered list of languages for use in display and output. A
    default list, named 'all' is (re)created on save/delete of the Language
    table (cf. ielex.models.update_language_list_all)"""
    name = models.CharField(max_length=999)
    language_ids = models.CommaSeparatedIntegerField(max_length=999)
    modified = models.DateTimeField(auto_now=True)

    def _get_list(self):
        return [int(i) for i in self.language_ids.split(",")]
    def _set_list(self, listobj):
        self.language_ids = ",".join([str(i) for i in listobj])
        return
    language_id_list = property(_get_list, _set_list)
    canonical_url = "/languages/"

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

reversion.register(LanguageList)

class MeaningList(models.Model):
    """Named lists of meanings, e.g. 'All' and 'Swadesh 100'"""
    name = models.CharField(max_length=999)
    meaning_ids = models.CommaSeparatedIntegerField(max_length=999)
    modified = models.DateTimeField(auto_now=True)

    def _get_list(self):
        return [int(i) for i in self.meaning_ids.split(",")]
    def _set_list(self, listobj):
        self.meaning_ids = ",".join([str(i) for i in listobj])
        return
    meaning_id_list = property(_get_list, _set_list)
    canonical_url = "/meanings/"

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

class CognateJudgementCitation(models.Model):
    cognate_judgement = models.ForeignKey(CognateJudgement)
    source = models.ForeignKey(Source)
    pages = models.CharField(max_length=999)
    reliability = models.CharField(max_length=1, choices=Source.RELIABILITY_CHOICES)
    comment = models.CharField(max_length=999)
    modified = models.DateTimeField(auto_now=True)

    @property
    def canonical_url(self):
        return "/lexeme/%s/edit-cognate-citation/%s/" % \
                (self.cognate_judgement.lexeme.id, self.id)

    def __unicode__(self):
        return u"CJC src=%s cit=%s" % (self.source.id, self.id)


reversion.register(CognateJudgementCitation)

class LexemeCitation(models.Model):
    lexeme = models.ForeignKey(Lexeme)
    source = models.ForeignKey(Source)
    pages = models.CharField(max_length=999)
    reliability = models.CharField(max_length=1, choices=Source.RELIABILITY_CHOICES)
    comment = models.CharField(max_length=999)
    modified = models.DateTimeField(auto_now=True)

    @property
    def canonical_url(self):
        return "/lexeme/%s/edit-citation/%s/" % (self.lexeme.id, self.id)

    def __unicode__(self):
        return u"%s src=%s cit=%s" % (self.lexeme.source_form, self.source.id, self.id)

reversion.register(LexemeCitation)

def update_language_list_all(sender, instance, **kwargs):
    """Update the LanguageList 'all' whenever Language objects are saved or
    deleted"""
    # it should just be when created or deleted, but the extra overhead is
    # tiny, since changes in the Language table are rare
    try:
        ll = LanguageList.objects.get(name="all")
    except:
        ll = LanguageList.objects.create(name="all")
    if ll.language_id_list != list(Language.objects.values_list("id", flat=True)):
        ll.language_id_list = [l.id for l in Language.objects.all()]
        ll.save(force_update=True)
    return

models.signals.post_save.connect(update_language_list_all, sender=Language)
models.signals.post_delete.connect(update_language_list_all, sender=Language)

def update_meaning_list_all(sender, instance, **kwargs):
    try:
        ml = MeaningList.objects.get(name="all")
    except:
        ml = MeaningList.objects.create(name="all")
    if ml.meaning_id_list != list(Meaning.objects.values_list("id", flat=True)):
        ml.meaning_id_list = [l.id for l in Meaning.objects.all()]
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

