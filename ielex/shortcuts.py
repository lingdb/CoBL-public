import glob
import os.path as path

from django.shortcuts import render_to_response
from django.template import RequestContext

from ielex.lexicon.defaultModels import getDefaultDict

from ielex.settings import DEBUG


def render_template(request, template_path, extra_context={}):
    """Wrapper around render_to_response that fills in context_instance"""
    c = RequestContext(request)
    c.update(getDefaultDict(request))
    c.update(extra_context)
    if minifiedJs is not None and 'minifiedJs' not in c:
        c['minifiedJs'] = minifiedJs
    return render_to_response(template_path, context_instance=c)


# When we're not in DEBUG mode, we search for the minified.js file:
def minifiedJs():
    files = glob.glob('./static/minified.*.js')
    for file in files:
        return path.basename(file)


minifiedJs = minifiedJs()
