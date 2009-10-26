from textwrap import dedent
import time
from django.http import HttpResponse
from ielex.lexicon.models import *

def write_nexus(response):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/plain')
    # response['Content-Disposition'] = 'attachment; filename=ielex.nex'
    print>>response, "#NEXUS"
    print>>reponse, "[ File generated: %s ]" % time.strftime("%Y-%m-%d %H:%M:%S",
            time.localtime()) 
    languages = Language.objects.filter(id__in=[1,2,3])
    cognate_classes = CognateSet.objects.filter(id__in=range(1,21))
    for language in languages:
        row = []
        row.append(language.ascii_name)
        data = []
        # cj = CognateJudgement.objects.filter(language=language
        # CognateSet.objects.filter(lexeme__language=language, id__in=range(1,21))
        # for cognate_class in cognate_classes.filter(language=language):
        print>>response, "".join(row)

    return response
