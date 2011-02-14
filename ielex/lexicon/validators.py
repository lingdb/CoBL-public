# http://docs.djangoproject.com/en/dev/ref/validators/
# http://docs.djangoproject.com/en/dev/ref/models/instances/#id1

# These are currently used as model validators (`validator=[]` arguments of
# model definitions, but should also be used as form validators

import re
from django.core.validators import ValidationError

def suitable_for_url(value):
    # cf also clean_ascii_name function in forms.py
    regex = re.compile(r"[a-zA-Z0-9_-.]+")
    match = regex.match(value)
    if match.start() > 0 or match.end() < len(value):
        raise ValidationError("Meaning.gloss does not match regex pattern")
    return
