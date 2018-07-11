import pathlib
import json

from django.shortcuts import render

import cobl
from cobl.lexicon.defaultModels import getDefaultDict
from cobl.settings import DEBUG


def render_template(request, template_path, extra_context={}):
    """Wrapper around render_to_response that fills in context_instance"""
    c = {}
    c.update(getDefaultDict(request))
    c.update(extra_context)
    c['minifiedJs'] = minifiedJs
    return render(request, template_path, c)


# When we're not in DEBUG mode, we search for the minified.js file:
def get_minifiedJs():
    if DEBUG:
        return None
    sdir = pathlib.Path(cobl.__file__).parent / 'static'
    with sdir.joinpath('assets.json') as fp:
        assets = json.load(fp)
    minjs = sdir / 'minified.{0}.js'.format(assets['./minified.js'])
    if minjs.exists():
        return minjs.name
    raise ValueError('{0} not found'.format(minjs))


minifiedJs = get_minifiedJs()
