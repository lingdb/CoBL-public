"""Writing your own context processors

A context processor is a Python function that takes one argument, an
HttpRequest object, and returns a dictionary that gets added to the template
context. Each context processor must return a dictionary.

Custom context processors can live anywhere in the code base. All Django cares
about is that your custom context processors are pointed-to by the
TEMPLATE_CONTEXT_PROCESSORS setting."""

from cobl.settings import VERSION
from cobl import settings
from cobl.lexicon.defaultModels import (
    getDefaultWordlist, getDefaultLanguagelist
)


def configuration(request):
    """Various things stored in settings.py"""
    return {"version": VERSION,
            "current_url": request.get_full_path(),
            "project_long_name": settings.project_long_name,
            "project_short_name": settings.project_short_name,
            "project_description": settings.project_description,
            "acknowledgements": settings.acknowledgements,
            "semantic_domains": settings.semantic_domains,
            "structural_features": settings.structural_features}


def navigation(request):
    return {"current_wordlist_name":
            request.session.get(
                "current_wordlist_name", getDefaultWordlist(request)),
            "current_language_list_name":
            request.session.get(
                "current_language_list_name", getDefaultLanguagelist(request))}
