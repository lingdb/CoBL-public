# -*- coding: utf-8 -*-
from string import uppercase, lowercase
from itertools import izip
#from ielex.lexicon.models import Language
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.management.base import NoArgsCommand

codes = list(uppercase) + [i+j for i in uppercase for j in lowercase]

def int2alpha(n):
    """Indexes start at 1!"""
    assert n == int(n)
    return codes[n-1]

def alpha2int(a):
    """Indexes start at 1!"""
    return codes.index(a)+1

def next_alias(l, ignore=[]):
    """Find the next unused alias from a list of aliases"""
    for alias in l:
        assert alias in codes+ignore
    for alias in codes:
        if alias not in l+ignore:
            return alias
    return

def two_by_two(I):
    """Return an iterable two-by-two, e.g.:
        [1,2,3,4,5,6] -> (1,2), (3,4), (5,6)
    This is used in formatting the denormalized [id, alias] field of
    the Lexeme model"""
    args = [iter(I)] * 2
    return izip(*args)

def confirm_required(template_name, context_creator, key='__confirm__'):
    """
    Decorator for views that need confirmation page. For example, delete
    object view. Decorated view renders confirmation page defined by template
    'template_name'. If request.POST contains confirmation key, defined
    by 'key' parameter, then original view is executed.

    Context for confirmation page is created by function 'context_creator',
    which accepts same arguments as decorated view.

    Example
    -------

        def remove_file_context(request, id):
            file = get_object_or_404(Attachment, id=id)
            return RequestContext(request, {'file': file})

        @confirm_required('remove_file_confirm.html', remove_file_context)
        def remove_file_view(request, id):
            file = get_object_or_404(Attachment, id=id)
            file.delete()
            next_url = request.GET.get('next', '/')
            return HttpResponseRedirect(next_url)

    Example of HTML template
    ------------------------

        <h1>Remove file {{ file }}?</h1>

        <form method="POST" action="">
            <input type="hidden" name="__confirm__" value="1" />
            <input type="submit" value="delete"/> <a href="{{ file.get_absolute_url }}">cancel</a>
        </form>

    Source: http://djangosnippets.org/snippets/1922/
    """
    def decorator(func):
        def inner(request, *args, **kwargs):
            if request.POST.has_key(key):
                return func(request, *args, **kwargs)
            else:
                context = context_creator and context_creator(request, *args, **kwargs) \
                    or RequestContext(request)
                return render_to_response(template_name, context)
        return wraps(func)(inner)
    return decorator

def anchored(url):
    return "%s#active" % url

class LexDBManagementCommand(NoArgsCommand):
    """Suppress Django default options from Management commands"""

    def run_from_argv(self, argv):
        """
        A version of the method from
        Django-1.3-py2.7.egg/django/core/management/base.py
        with call to `handle_default_options` disabled in order to
        suppress unwanted default options.
        """
        parser = self.create_parser(argv[0], argv[1])
        options, args = parser.parse_args(argv[2:])
        # handle_default_options(options)
        assert not hasattr(options, "settings")
        assert not hasattr(options, "pythonpath")
        self.execute(*args, **options.__dict__)
        return

if __name__ == "__main__":
    snip_flag = True
    for i in range(1,703):
        s = int2alpha(i)
        if i < 11 or i > 692:
            print i, s
        elif snip_flag:
            print "[...]"
            snip_flag = False
        else:
            pass
        assert alpha2int(s) == i

    l = ["A","B","C"]
    print l
    print "next_alias(l) -->", next_alias(l)
    l = ["none","A","B","C"]
    print l
    print 'next_alias(l, ignore=["none","new"]) -->', next_alias(l,
            ignore=["none","new"])
