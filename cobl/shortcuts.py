import hashlib
import pathlib

from django.shortcuts import render

import cobl
from cobl.lexicon.defaultModels import getDefaultDict
from cobl.settings import DEBUG


def md5(fname):
    hash_md5 = hashlib.md5()
    with fname.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


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
    fname = pathlib.Path(cobl.__file__).parent / 'static' / 'minified.js'
    if not fname.exists():
        raise ValueError('minified.js does not exist')
    return '{0}?hash={1}'.format(fname.name, md5(fname))


minifiedJs = get_minifiedJs()
