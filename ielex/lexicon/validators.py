# http://docs.djangoproject.com/en/dev/ref/validators/
# http://docs.djangoproject.com/en/dev/ref/models/instances/#id1

# These are currently used as model validators (`validator=[]` arguments of
# model definitions, but should also be used as form validators

import re
from django.core.validators import ValidationError

def suitable_for_url(value):
    """Test that value contains onlys unreserved characters
    according to RFC3986/2.3:

    unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"

    TODO: reserved names 'all', 'none' # put this list somewhere
    """
    reserved_names =["all", "all-alpha"]
    # cf also clean_ascii_name function in forms.py
    regex = re.compile(r"^[a-zA-Z0-9_.~-]+$")
    match = regex.match(value)
    if not match:
        raise ValidationError("Meaning.gloss does not match %s" %
                repr(regex.pattern))
    if value in reserved_names:
        raise ValidationError("Meaning.gloss is a reserved name")
    return
