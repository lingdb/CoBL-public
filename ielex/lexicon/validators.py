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
        raise ValidationError("""This field can only include characters
                which are legal in a url: letters, digits and - . _ ~""")
    if value in reserved_names:
        raise ValidationError("""This name is reserved for
                system-internal use. Please choose another.""")
    return
