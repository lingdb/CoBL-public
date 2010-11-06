from ielex.settings import VERSION
"""Writing your own context processors

A context processor has a very simple interface: It's just a Python function
that takes one argument, an HttpRequest object, and returns a dictionary that
gets added to the template context. Each context processor must return a
dictionary.

Custom context processors can live anywhere in your code base. All Django cares
about is that your custom context processors are pointed-to by your
TEMPLATE_CONTEXT_PROCESSORS setting."""

def version(request):
    return {"version":VERSION}

def current_url(request):
    return {"current_url":request.get_full_path()}
