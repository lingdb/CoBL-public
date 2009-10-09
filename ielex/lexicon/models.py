from django.db import models

class Language(models.Model):
    iso_code = models.CharField(max_length=3)
    ascii_name = models.CharField(max_length=999)
    utf8_name = models.CharField(max_length=999)

class DyenName(models.Model):
    language = models.ForeignKey(Language)
    name = models.CharField(max_length=999)

class Meaning(models.Model):
    gloss = models.CharField(max_length=64) # one word name
    description = models.CharField(max_length=64) # show name
    notes = models.TextField()

class CognateSet(models.Model):
    reconstruction = models.CharField(max_length=999)
    notes = models.TextField()
    modified = models.DateTimeField(auto_now=True)

class Lexeme(models.Model):
    language = models.ForeignKey(Language)
    meaning = models.ForeignKey(Meaning)
    cognate_set = models.ManyToManyField(CognateSet,
            through="CognateJudgement")
    source_form = models.CharField(max_length=999)
    phon_form = models.CharField(max_length=999)
    gloss = models.CharField(max_length=999)
    notes = models.TextField()
    modified = models.DateTimeField(auto_now=True)

class CognateJudgement(models.Model):
    lexeme = models.ForeignKey(Lexeme)
    cognate_set = models.ForeignKey(CognateSet)
    modified = models.DateTimeField(auto_now=True)
