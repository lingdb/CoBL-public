from textwrap import dedent
import time
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
# from django.shortcuts import render_to_response
from ielex import settings
from ielex.lexicon.models import *
from ielex.shortcuts import render_template
#from ielex.views import get_sort_order
from ielex.views import ChooseNexusOutputForm

def list_nexus(request):
    if request.method == "POST":
        form =  ChooseNexusOutputForm(request.POST)
        return HttpResponseRedirect("/nexus-data/")
    else:
        defaults = {"unique":1, "reliability":["L","X"], "language_list":1,
                "meaning_list":1, "dialect":"NN"}
        form =  ChooseNexusOutputForm(defaults)
    return render_template(request, "nexus_list.html", {"form":form})

@login_required
def write_nexus(request):
    # TODO 
    #   - contributor and sources list
    LABEL_COGNATE_SETS = True
    INCLUDE_UNIQUE_STATES = bool(request.POST.get("unique", 0))
    language_list_id = request.POST["language_list"]
    meaning_list_id = request.POST["meaning_list"]
    exclude = set(request.POST.getlist("reliability"))
    dialect = request.POST.get("dialect", "NN")
    # 0:19 included
    # 0.17 excluded

    start_time = time.time()
    assert request.method == 'POST'

    # get data together
    language_list = LanguageList.objects.get(id=language_list_id)
    languages = get_ordered_languages(language_list)
    # languages = Language.objects.filter(
    #         id__in=language_list.language_id_list).order_by("sort_key")
    language_names = ["'"+name+"'" for name in
            languages.values_list("ascii_name", flat=True)]

    meaning_list = MeaningList.objects.get(id=meaning_list_id)
    meanings = Meaning.objects.filter(id__in=meaning_list.meaning_id_list)
    max_len = max([len(l) for l in language_names])


    cognate_class_ids = CognateSet.objects.all().values_list("id", flat=True)

    data = {}
    for cc in cognate_class_ids:
        # language_ids = CognateSet.objects.get(id=cc).lexeme_set.filter(
        #         meaning__in=meanings).values_list('language', flat=True)
        ## this is much slower than the values_list version (probably from
        ## calculating the reliability ratings property
        # TODO look at LexemeCitation reliablity ratings here too
        language_ids = [cj.lexeme.language.id for cj in
                CognateJudgement.objects.filter(cognate_class=cc,
                        lexeme__meaning__in=meanings)
                        if not (cj.reliability_ratings & exclude)]
        if language_ids:
            data[cc] = language_ids

    if INCLUDE_UNIQUE_STATES:
        # adds a cc code for all the lexemes which are not registered as
        # belonging to a cognate class
        # TODO look at LexemeCitation reliablity ratings here too
        # note that registered cognate classes with one member will NOT be
        # ignored when INCLUDE_UNIQUE_STATES = False
        uniques = Lexeme.objects.filter(
                cognate_class__isnull=True,
                meaning__in=meanings).values_list("language", "id")
        for language_id, lexeme_id in uniques:
            cc = ("U", lexeme_id)
            data[cc] = [language_id]

    # Create the HttpResponse object with the appropriate header.
    filename = "%s-%s-%s.nex" % (settings.project_short_name, 
            language_list.name, meaning_list.name)
    response = HttpResponse(mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % \
            filename.replace(" ", "_")

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
    print>>response, "[ Exclude rating/s: %s ]" % ", ".join(sorted(exclude))
    print>>response, "[ Include unique states: %s ]" % INCLUDE_UNIQUE_STATES
    print>>response, "[ File generated: %s ]\n" % \
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    if dialect in ("NN", "MB"):
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
    else:
        assert dialect == "BP"
        print>>response, dedent("""\
            begin data;
              dimensions ntax=%s nchar=%s;
              taxlabels %s;
              format symbols="01";
              matrix
            """ % (len(languages), len(data), " ".join(language_names)))

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
    print>>response, "  ;\nend;\n"

    if dialect == "BP":
        print>>response, dedent("""\
            begin BayesPhylogenies;
                Chains 1;
                it 12000000;
                Model m1p;
                bf emp;
                cv 2;
                pf 10000;
                autorun;
            end;
            """)

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
