from django.db import models
import reversion
from ielex.lexicon.models import Lexeme, Source

class SemanticRelation(models.Model):
    relation_code = models.CharField(max_length=64)
    long_name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "/relation/%s/" % self.id

    def __unicode__(self):
        return unicode(self.id)

reversion.register(SemanticRelation)


class SemanticExtension(models.Model):
    lexeme = models.ForeignKey(Lexeme)
    cognate_class = models.ForeignKey(SemanticRelation)
    source = models.ManyToManyField(Source, through="SemanticExtensionCitation")
    modified = models.DateTimeField(auto_now=True)

    # def get_absolute_url(self):
    #     return "/meaning/%s/%s/%s/" % (self.lexeme.meaning.gloss,
    #             self.lexeme.id, self.id)

    @property
    def reliability_ratings(self):
        return set(self.kinmappingcitation_set.values_list("reliability", flat=True))

    def __unicode__(self):
        return u"" % (self.id)

reversion.register(SemanticExtension)


class SemanticExtensionCitation(models.Model):
    semantic_extension = models.ForeignKey(SemanticExtension)
    source = models.ForeignKey(Source)
    pages = models.CharField(max_length=999)
    reliability = models.CharField(max_length=1,
            choices=Source.RELIABILITY_CHOICES)
    comment = models.CharField(max_length=999)
    modified = models.DateTimeField(auto_now=True)

    # def get_absolute_url(self):
    #     return "/lexeme/%s/edit-cognate-citation/%s/" % \
    #             (self.cognate_judgement.lexeme.id, self.id)

    def __unicode__(self):
        return u"%s" % (self.id)

reversion.register(SemanticExtensionCitation)

class RelationList(models.Model):
    """A named, ordered list of semantic relations for use in display and output. A
    default list, named 'all' is (re)created on save/delete of the Language
    table (cf. ielex.models.update_relation_list_all)"""
    name = models.CharField(max_length=999)
    description = models.TextField(blank=True, null=True)
    language_ids = models.CommaSeparatedIntegerField(max_length=999)
    modified = models.DateTimeField(auto_now=True)

    def _get_list(self):
        if not self.relation_ids: # i.e. fresh install
            self.relation_ids = ",".join([str(i) for i in
                SemanticRelation.objects.values_list("id", flat=True)])
        return [int(i) for i in self.relation_ids.split(",")]
    def _set_list(self, listobj):
        self.relation_ids = ",".join([str(i) for i in listobj])
        return
    relation_id_list = property(_get_list, _set_list)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

reversion.register(RelationList)
