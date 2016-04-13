from django.shortcuts import render_to_response
from django.template import RequestContext

from ielex.lexicon.defaultModels import getDefaultDict


def render_template(request, template_path, extra_context={}):
    """Wrapper around render_to_response that fills in context_instance"""
    c = RequestContext(request)
    c.update(getDefaultDict(request))
    c.update(extra_context)
    return render_to_response(template_path, context_instance=c)
