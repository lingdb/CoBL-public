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

    """
    # also used by the clean_value_for_url function in forms.py
    regex = re.compile(r"^[a-zA-Z0-9_.~-]+$")
    match = regex.match(value)
    if not match:
        raise ValidationError("""This field can only include characters
                which are legal in a url: letters, digits and - . _ ~""")
    return

# this cannot be serialized by django 1.8
# https://docs.djangoproject.com/en/1.8/topics/migrations/#serializing-values
# def reserved_names(*names):
#     # reserved_names =["all", "all-alpha"]
#     def test_reserved_names(value):
#         if value in names:
#             raise ValidationError(
#             "The name `%s' is reserved for system-internal use. Please choose another."
#             % value)
#         return
#     return test_reserved_names

def standard_reserved_names(value):
    reserved_names =["all", "all-alpha"]
    if value in names:
        raise ValidationError(
        "The name `%s' is reserved for system-internal use. Please choose another."
        % value)
    return


