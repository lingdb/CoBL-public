"""Writing your own context processors

A context processor is a Python function that takes one argument, an
HttpRequest object, and returns a dictionary that gets added to the template
context. Each context processor must return a dictionary.

Custom context processors can live anywhere in the code base. All Django cares
about is that your custom context processors are pointed-to by the
TEMPLATE_CONTEXT_PROCESSORS setting."""

from ielex.settings import VERSION
config = None

def version(request):
    """Provides a {{ version }} tag (referring to the database programme, not
    the particular installation"""
    return {"version":VERSION}

def current_url(request):
    """The {{ current_url }} tag is used as a link target to force reloading of
    a page (e.g. to dismiss a message)"""
    return {"current_url":request.get_full_path()}

def local_settings(request):
    """
    Local customizations: Database name, description, etc.
    """
    
    if not config:
        # if !exists config file, create default
        # read config file
        pass
    return config
