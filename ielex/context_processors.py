"""Writing your own context processors

A context processor is a Python function that takes one argument, an
HttpRequest object, and returns a dictionary that gets added to the template
context. Each context processor must return a dictionary.

Custom context processors can live anywhere in the code base. All Django cares
about is that your custom context processors are pointed-to by the
TEMPLATE_CONTEXT_PROCESSORS setting."""

from ielex.settings import VERSION
from ielex import local_settings
from ielex.lexicon.models import *
from ielex.extensional_semantics.models import *

# config = None # XXX what's this for?

def configuration(request):
    """Various things stored in local_settings.py"""
    return {"version":VERSION,
            "current_url":request.get_full_path(),
            "project_long_name":local_settings.project_long_name,
            "project_short_name":local_settings.project_short_name,
            "project_description":local_settings.project_description,
            "acknowledgements":local_settings.acknowledgements,
            "semantic_domains":local_settings.semantic_domains,
            "structural_features":local_settings.structural_features
            }

def navigation(request):
    return {"current_wordlist_name":
                    request.session.get("current_wordlist_name", "CWN"),
            "current_language_list_name":
                    request.session.get("current_language_list_name", "CLLN"),
            }
