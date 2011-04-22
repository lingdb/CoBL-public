from django.db import models
import reversion
from ielex.lexicon.models import AbstractBaseCitation

class SemanticRelation(models.Model):
    relation_code = models.CharField(max_length=64)
    long_name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "/relation/%s/" % self.relation_code

    def __unicode__(self):
        return unicode("%s (%s)" % (self.relation_code, self.long_name))

reversion.register(SemanticRelation)

class SemanticExtension(models.Model):
    lexeme = models.ForeignKey('lexicon.Lexeme')
    relation = models.ForeignKey(SemanticRelation)
    source = models.ManyToManyField('lexicon.Source', through="SemanticExtensionCitation")
    modified = models.DateTimeField(auto_now=True)

    def reliability_ratings(self):
        return set(self.kinmappingcitation_set.values_list("reliability", flat=True))

    def get_absolute_url(self):
        return "/extension/%s/" % self.id

    def __unicode__(self):
        return u"%s" % (self.id)

reversion.register(SemanticExtension)

class SemanticExtensionCitation(AbstractBaseCitation):
    # TODO remove
    extension = models.ForeignKey(SemanticExtension)
    source = models.ForeignKey('lexicon.Source')

    def get_absolute_url(self):
        return "/citation/extension/%s/" % self.id

    def __unicode__(self):
        return u"<SEC %s src=%s sec=%s>" % (self.id, self.extension.id, self.source.id)

    class Meta:
        unique_together = (("extension", "source"),)

reversion.register(SemanticExtensionCitation)

class SemanticDomain(models.Model):
    """A named, ordered list of semantic relations (referred to as a 'domain'
    in the user interface) for use in display and output. A default list, named
    'all' is (re)created on save/delete of the Language table (cf.
    ielex.models.update_semantic_domain_all)"""
    DEFAULT = "all"

    name = models.CharField(max_length=999, unique=True)
    description = models.TextField(blank=True, null=True)
    relation_ids = models.CommaSeparatedIntegerField(blank=True,
            max_length=999)
    modified = models.DateTimeField(auto_now=True)

    def _get_list(self):
        try:
            return [int(i) for i in self.relation_ids.split(",")]
        except ValueError:
            return []
    def _set_list(self, listobj):
        self.relation_ids = ",".join([str(i) for i in listobj])
        return
    relation_id_list = property(_get_list, _set_list)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

reversion.register(SemanticDomain)

def update_semantic_domain_all(sender, instance, **kwargs):
    try:
        sd = SemanticDomain.objects.get(name=SemanticDomain.DEFAULT)
    except:
        sd = SemanticDomain.objects.create(name=SemanticDomain.DEFAULT,
                description="Default semantic domain containing a list of all semantic relations")
    if sd.relation_id_list != list(SemanticRelation.objects.values_list("id", flat=True)):
        sd.relation_id_list = [l.id for l in SemanticRelation.objects.all()]
        sd.save(force_update=True)
    return

models.signals.post_save.connect(update_semantic_domain_all, sender=SemanticRelation)
models.signals.post_delete.connect(update_semantic_domain_all, sender=SemanticRelation)

