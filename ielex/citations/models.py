from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
# import reversion ### TODO: add this once testing is complete

RELIABILITY_CHOICES = ( # used by Citation classes
        ("A", "High"),
        ("B", "Good (e.g. but needs further checking)"),
        ("C", "Doubtful"),
        ("L", "Loanword"),
        ("X", "Exclude (e.g. not the Swadesh term)"),
        )

# TODO: move Source class here too

class GenericCitation(models.Model):
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
        unique_together = (("content_object", "source"),)
        # maybe need this instead:
        #unique_together = (("content_type", "object_id", "source"),)

# reversion.register(GenericCitation)
