from textwrap import dedent
import time
from django.http import HttpResponse
from django.shortcuts import render_to_response
from ielex.lexicon.models import *
from ielex.views import get_sort_order

def list_nexus(request):
    return render_to_response("nexus_list.html", 
            {"language_lists":LanguageList.objects.all().extra(
                select={"lower_name":"lower(name)"}).order_by("lower_name")})

def write_nexus(request, language_list=None):
    start_time = time.time()

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/plain')
    # response['Content-Disposition'] = 'attachment; filename=ielex.nex'

    # get data together
    if language_list:
        languages = Language.objects.filter(
                id__in=LanguageList.objects.get(
                name=language_list).language_id_list).order_by(get_sort_order(request))
    else:
        languages = Language.objects.all()
    language_names = languages.values_list("ascii_name", flat=True)
    max_len = max([len(l) for l in language_names])
    cognate_class_ids = CognateSet.objects.all().values_list("id", flat=True)
    data = {}
    for cc in cognate_class_ids:
        data[cc] = CognateSet.objects.get(id=cc).lexeme_set.values_list('language', flat=True)

    # print out response
    print>>response, dedent("""\
        #NEXUS

        [ Citation:                                                        ]
        [   Dunn, Michael; Ludewig, Julia. 2009. IELex (Indo-European      ]
        [   Lexicon) Database. Max Planck Institute for Psycholinguistics, ]
        [   Nijmegen.                                                      ]
        """)
    if language_list:
        print>>response, "[ Taxon list: %s ]" % language_list
    print>>response, "[ File generated: %s ]\n" % time.strftime("%Y-%m-%d %H:%M:%S",
            time.localtime())

    print>>response, dedent("""\
        begin taxa;
          dimensions ntax=%s;
          taxlabels %s;
        end;
        """ % (len(languages), " ".join(language_names)))
    print>>response, dedent("""\
        begin characters;
          dimensions nchar=%s;
          format symbols="01";
          matrix""" % len(data))

    for language in languages:
        row = []
        for cc in cognate_class_ids:
            if language.id in data[cc]:
                row.append("1")
            else:
                row.append("0")
        print>>response, "    %s %s" % (language.ascii_name.ljust(max_len), "".join(row))
    print>>response, "  ;\nend;"

    # timing
    seconds = int(time.time() - start_time)
    minutes = seconds // 60
    seconds %= 60
    print>>response, "[ Processing time: %02d:%02d ]" % (minutes, seconds)
    return response
