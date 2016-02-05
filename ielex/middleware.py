from os import linesep
from django.utils.encoding import force_unicode


def strip_blank_lines(value):
    return linesep.join(
        [s for s in force_unicode(value).splitlines() if s.strip()])


class NoBlankLinesMiddleware(object):
    def process_response(self, request, response):
        if 'text/html' in response['Content-Type']:
            response.content = strip_blank_lines(response.content)
        return response
