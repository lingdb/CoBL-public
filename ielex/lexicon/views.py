from textwrap import dedent
import time
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
# from django.shortcuts import render_to_response
from ielex.lexicon.models import *
from ielex.shortcuts import render_template
from ielex.views import get_sort_order
from ielex.views import ChooseNexusOutputForm

def list_nexus(request):
    defaults = {"unique":True, "reliability":["L"], "language_list":1,
            "meaning_list":1}
    form =  ChooseNexusOutputForm(defaults)
    return render_template(request, "nexus_list.html", {"form":form})

@login_required
def write_nexus(request):
    # TODO 
    #   - take into account the requested reliability ratings
    #   - include unique states
    #   - contributor and sources list
    LABEL_COGNATE_SETS = True
    INCLUDE_UNIQUE_STATES = True
    # 0:19 included
    # 0.17 excluded

    start_time = time.time()
    assert request.method == 'POST'

    # Create the HttpResponse object with the appropriate header.
    response = HttpResponse(mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=ielex.nex'

    # get data together
    #form =  ChooseNexusOutputForm(request.POST)
    language_list_id = request.POST["language_list"]
    languages = Language.objects.filter(
            id__in=LanguageList.objects.get(
            id=language_list_id).language_id_list).order_by(get_sort_order(request))
    language_names = ["'"+name+"'" for name in
            languages.values_list("ascii_name", flat=True)]

    meaning_list_id = request.POST["meaning_list"]
    meanings = Meaning.objects.filter(id__in=MeaningList.objects.get(
            id=meaning_list_id).meaning_id_list)
    max_len = max([len(l) for l in language_names])

    exclude = set(request.POST.getlist("reliability"))

    cognate_class_ids = CognateSet.objects.all().values_list("id", flat=True)

    data = {}
    for cc in cognate_class_ids:
        # language_ids = CognateSet.objects.get(id=cc).lexeme_set.filter(
        #         meaning__in=meanings).values_list('language', flat=True)
        ## this is much slower than the values_list version (probably from
        ## calculating the reliability ratings property
        language_ids = [cj.lexeme.language.id for cj in
                CognateJudgement.objects.filter(cognate_class=cc,
                    lexeme__meaning__in=meanings)
                if not (cj.reliability_ratings & exclude)]
        if language_ids:
            data[cc] = language_ids

    if INCLUDE_UNIQUE_STATES:
        # add a cc for all the lexemes which are not in a cognate class
        # TODO look at lexeme reliablity ratings here too
        uniques = Lexeme.objects.filter(
                cognate_class__isnull=True,
                meaning__in=meanings).values_list("language", "id")
        for language_id, lexeme_id in uniques:
            cc = ("U", lexeme_id)
            data[cc] = [language_id]

    # print out response
    print>>response, dedent("""\
        #NEXUS

        [ Citation:                                                        ]
        [   Dunn, Michael; Ludewig, Julia. 2009. IELex (Indo-European      ]
        [   Lexicon) Database. Max Planck Institute for Psycholinguistics, ]
        [   Nijmegen.                                                      ]
        """)
    print>>response, "[ Language list: %s ]" % LanguageList.objects.get(
            id=language_list_id).name
    print>>response, "[ Meaning list: %s ]" % MeaningList.objects.get(
            id=meaning_list_id).name
    print>>response, "[ Exclude rating: %s ]" % ", ".join(sorted(exclude))
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

    if LABEL_COGNATE_SETS:
        def get_code(cc):
            """Take a integer or tuple index and return a concatenated string"""
            try:
                code = "".join(str(e) for e in cc)
            except TypeError:
                code = str(cc)
            return code
        msg = "   %s [ Cognate class codes ]"  % (" "*max_len)
        if INCLUDE_UNIQUE_STATES:
            msg += " ['U' codes are lexeme ids representing unique states ]"
        print>>response, msg
        for i in range(max([len(get_code(i)) for i in data.keys()])):
            row = []
            for cc in sorted(data):
                try:
                    row.append(get_code(cc)[i])
                except IndexError:
                    row.append(".")
            print>>response, "    %s[ %s ]" % (" "*max_len, "".join(row))
        print>>response

    for language in languages:
        row = []
        for cc in sorted(data):
            if language.id in data[cc]:
                row.append("1")
            else:
                row.append("0")
        print>>response, "    '%s'%s%s" % (language.ascii_name,
                " "*(max_len - len(language.ascii_name)), "".join(row))
    print>>response, "  ;\nend;"

    # get contributor list:
    # lexical sources
    # lexemes coded by
    # cognate sources
    # cognates coded by

    # timing
    seconds = int(time.time() - start_time)
    minutes = seconds // 60
    seconds %= 60
    print>>response, "[ Processing time: %02d:%02d ]" % (minutes, seconds)
    return response
