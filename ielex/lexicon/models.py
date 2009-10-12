from django.db import models, connection

class Language(models.Model):
    iso_code = models.CharField(max_length=3)
    ascii_name = models.CharField(max_length=999)
    utf8_name = models.CharField(max_length=999)

    def __unicode__(self):
        return self.ascii_name

    class Meta:
        ordering = ["utf8_name"]

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
    # objects = MeaningCount()

    def __unicode__(self):
        return self.gloss.upper()

    class Meta:
        ordering = ["gloss"]

class CognateSet(models.Model):
    alias = models.CharField(max_length=3)
    reconstruction = models.CharField(max_length=999)
    notes = models.TextField()
    modified = models.DateTimeField(auto_now=True)
    objects = models.Manager() # all rows

    def _get_meaning_set(self):
        return set([cj.lexeme.meaning for cj in self.cognatejudgement_set.all()])
    meaning_set = property(_get_meaning_set)

    def _get_meaning(self):
        """This will cause problems when/if the database has cognate sets
        providing reflexes for more than one meaning"""
        return self._get_meaning_set().pop()
    meaning = property(_get_meaning) # treat as an attribute

    def __unicode__(self):
        return unicode(self.id)

    class Meta:
        ordering = ["alias"]

class Lexeme(models.Model):
    language = models.ForeignKey(Language)
    meaning = models.ForeignKey(Meaning)
    cognate_class = models.ManyToManyField(CognateSet,
            through="CognateJudgement")
    source_form = models.CharField(max_length=999)
    phon_form = models.CharField(max_length=999)
    gloss = models.CharField(max_length=999)
    notes = models.TextField()
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.phon_form or self.source_form or "Lexeme"

    class Meta:
        order_with_respect_to = "language"

class CognateJudgement(models.Model):
    lexeme = models.ForeignKey(Lexeme)
    cognate_class = models.ForeignKey(CognateSet)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return unicode(self.id)

class LanguageList(models.Model):
    name = models.CharField(max_length=999)
    language_ids = models.CommaSeparatedIntegerField(max_length=999)
    # modified = models.DateTimeField(auto_now=True) # ADD LATER

    def _get_language_id_list(self):
        return [int(i) for i in self.language_ids.split(",")]
    language_id_list = property(_get_language_id_list)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

