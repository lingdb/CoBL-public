import glob
import os.path as path

from django.shortcuts import render

from cobl.lexicon.defaultModels import getDefaultDict
from cobl.settings import DEBUG


def render_template(request, template_path, extra_context={}):
    """Wrapper around render_to_response that fills in context_instance"""
    c = {}
    c.update(getDefaultDict(request))
    c.update(extra_context)
    if minifiedJs is not None and 'minifiedJs' not in c:
        c['minifiedJs'] = minifiedJs
    return render(request, template_path, c)


# When we're not in DEBUG mode, we search for the minified.js file:
def minifiedJs():
    if DEBUG:
        return None
    files = glob.glob('./static/minified.*.js')
    for file in files:
        return path.basename(file)


minifiedJs = minifiedJs()
