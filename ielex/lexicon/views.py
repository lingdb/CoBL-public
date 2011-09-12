from textwrap import dedent
import time
import sys
# import logging
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.generic import CreateView, UpdateView
from ielex import settings
from ielex.lexicon.models import *
from ielex.shortcuts import render_template
from ielex.forms import ChooseNexusOutputForm, EditCognateClassCitationForm

class CognateClassCitationUpdateView(UpdateView):
    model=CognateClassCitation
    form_class=EditCognateClassCitationForm
    template_name="generic_update.html"

    def get_context_data(self, **kwargs):
        context = super(CognateClassCitationUpdateView,
                self).get_context_data(**kwargs)
        cc_id = context["object"].cognate_class.id
        context["title"] = "New cognate class citation"
        context["heading"] = "Citation to cognate class %s" % cc_id
        context["cancel_dest"] = reverse("cognate-set",
                kwargs={"cognate_id":cc_id})
        return context

class CognateClassCitationCreateView(CreateView):
    form_class=EditCognateClassCitationForm
    template_name="generic_update.html"

    def get_context_data(self, **kwargs):
        cc_id = int(self.kwargs["cognate_id"])
        context = super(CognateClassCitationCreateView,
                self).get_context_data(**kwargs)
        context["title"] = "New cognate class citation"
        context["heading"] = "Citation to cognate class %s" % cc_id
        context["cancel_dest"] = reverse("cognate-set",
                kwargs={"cognate_id":cc_id})
        return context

    def get_form_kwargs(self):
        """Need to instantiate the object and set the cognate_class parameter
        here, since fields in the Meta.exclude attribute of ModelForm classes
        can't otherwise be set by forms.
        """
        cc_id = int(self.kwargs["cognate_id"])
        self.object = CognateClassCitation()
        self.object.cognate_class = CognateClass.objects.get(id=cc_id)
        kwargs = super(CognateClassCitationCreateView,
                self).get_form_kwargs()
        return kwargs

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
def write_nexus_view(request):
    """A wrapper to call the `write_nexus` function from a view"""
    # TODO 
    #   - contributor and sources list
    LABEL_COGNATE_SETS = True
    INCLUDE_UNIQUE_STATES = bool(request.POST.get("unique", 0))
    language_list = LanguageList.objects.get(id=request.POST["language_list"])
    meaning_list = MeaningList.objects.get(id=request.POST["meaning_list"])
    exclude = set(request.POST.getlist("reliability"))
    dialect = request.POST.get("dialect", "NN")
    msg = "Warning: nexus export can be very slow"
    messages.add_message(request, messages.INFO, msg)
    assert request.method == 'POST'

    # Create the HttpResponse object with the appropriate header.
    filename = "%s-%s-%s.nex" % (settings.project_short_name,
            language_list.name, meaning_list.name)
    response = HttpResponse(mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % \
            filename.replace(" ", "_")

    response = write_nexus(response,
            language_list.name,
            meaning_list.name,
            exclude,
            dialect,
            LABEL_COGNATE_SETS,
            INCLUDE_UNIQUE_STATES)
    return response

def write_nexus(fileobj,
            language_list_name,
            meaning_list_name,
            exclude,
            dialect,
            LABEL_COGNATE_SETS,
            singletons):
    start_time = time.time()

    # MAX_1_SINGLETON: True|False
    # only allow zero or one singletons per language per meaning (zero
    # if there is another lexeme coded for that meaning, one if not).
    if singletons:
        INCLUDE_UNIQUE_STATES = True
        if singletons == "all":
            MAX_1_SINGLETON = False
        else:
            assert singletons == "limited"
            MAX_1_SINGLETON = True
    else:
        INCLUDE_UNIQUE_STATES = False

    # get data together
    language_list = LanguageList.objects.get(name=language_list_name)
    languages = language_list.languages.all().order_by("languagelistorder")
    language_names = [language.ascii_name for language in languages]

    meaning_list = MeaningList.objects.get(name=meaning_list_name)
    meanings = Meaning.objects.filter(id__in=meaning_list.meaning_id_list)
    max_len = max([len(l) for l in language_names])

    # all cognate classes
    cognate_class_ids = CognateClass.objects.all().values_list("id", flat=True)
    cognate_class_names = dict(CognateJudgement.objects.all().values_list(
            "cognate_class__id", "lexeme__meaning__gloss").distinct())
    #logging.info("len cognate_class_ids = %s" % len(cognate_class_ids))

    # make a list for each meaning of the languages lacking any lexeme with that meaning
    missing = {}
    #logging.info("=== missing data MEANING: [LANGUAGE_IDS] ===")
    for meaning in meanings:
        missing[meaning] = [language.id for language in languages if not
                language.lexeme_set.filter(meaning=meaning).exists()]
        #logging.info("%s: %s" % (meaning, missing[meaning]))

    data, data_missing = {}, {}
    for cc in cognate_class_ids:
        ## Faster way: (doesn't do reliability ratings properly)
        # language_ids = CognateClass.objects.get(id=cc).lexeme_set.filter(
        #         meaning__in=meanings).values_list('language', flat=True)
        ## Slower way:
        # TODO look at LexemeCitation reliablity ratings here too
        language_ids = [cj.lexeme.language.id for cj in
                CognateJudgement.objects.filter(cognate_class=cc,
                        lexeme__meaning__in=meanings)
                        if not (cj.reliability_ratings & exclude)]
        if language_ids:
            data[cc] = language_ids
            #meaning = set(CognateClass.objects.get(id=cc).lexeme_set.values_list(
            #        "meaning", flat=True)).pop()
            try:
                data_missing[cc] = missing[CognateClass.objects.get(id=cc).get_meaning()]
                # if data_missing[cc]:
                #     logging.info("missing data '%s': %s %s" % (meaning, cc, data_missing[cc]))
            except KeyError:
                data_missing[cc] = []

    if INCLUDE_UNIQUE_STATES:
        # adds a cc code for all the lexemes which are not registered as
        # belonging to a cognate class
        # TODO look at LexemeCitation reliablity ratings here too
        # note that registered cognate classes with one member will NOT be
        # ignored when INCLUDE_UNIQUE_STATES = False
        uniques = Lexeme.objects.filter(
                language__in=languages,
                meaning__in=meanings,
                cognate_class__isnull=True).values_list(
                        "language__id",
                        "meaning__id",
                        "id")

        if MAX_1_SINGLETON:
            # only allow one singleton per language-meaning, and only if there
            # are not already any lexemes in that language-meaning cell
            # coded as part of a cognate set
            suppress_singleton = set()
            for language in languages:
                for meaning in meanings:
                    if Lexeme.objects.filter(language=language,
                            meaning=meaning, cognate_class__isnull=False):
                        suppress_singleton.add((language.id, meaning.id))
                        #logging.info("Suppress singleton %s %s" % (language,
                        #    meaning))

        for language_id, meaning_id, lexeme_id in uniques:
            if not MAX_1_SINGLETON or (language_id, meaning_id) not in \
                    suppress_singleton:
                meaning = Meaning.objects.get(id=meaning_id)
                cc = ("U", lexeme_id)
                data[cc] = [language_id]
                cognate_class_names[cc] = meaning.gloss
                try:
                    data_missing[cc] = missing[meaning]
                    # if data_missing[cc]:
                    #     logging.info("missing data '%s': %s %s" % (meaning, cc, data_missing[cc]))
                except KeyError:
                    data_missing[cc] = []
            # else:
            #     if MAX_1_SINGLETON:
            #         logging.info("Suppressed %s %s" % (language_id, meaning_id))

    def cognate_class_name_formatter(cc):
        gloss = cognate_class_names[cc]
        if type(cc) == int:
            return "%s_cogset_%s" % (gloss, cc)
        else:
            assert type(cc) == tuple
            return "%s_lexeme_%s" % (gloss, cc[1])

    print>>fileobj, dedent("""\
        #NEXUS

        [ Citation:                                                          ]
        [   Dunn, Michael; Ludewig, Julia; et al. 2011. IELex (Indo-European ]
        [   Lexicon) Database. Max Planck Institute for Psycholinguistics,   ]
        [   Nijmegen.                                                        ]
        """)
    print>>fileobj, "[ Language list: %s ]" % language_list_name
    print>>fileobj, "[ Meaning list: %s ]" % meaning_list_name
    print>>fileobj, "[ Exclude rating/s: %s ]" % ", ".join(sorted(exclude))
    print>>fileobj, "[ Include unique states: %s ]" % INCLUDE_UNIQUE_STATES
    if INCLUDE_UNIQUE_STATES:
        print>>fileobj, "[ Limit of one singleton per language/meaning: %s ]" % MAX_1_SINGLETON
    print>>fileobj, "[ File generated: %s ]\n" % \
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    if dialect in ("NN", "MB"):
        print>>fileobj, dedent("""\
            begin taxa;
              dimensions ntax=%s;
              taxlabels %s;
            end;
            """ % (len(languages), " ".join(language_names)))
        print>>fileobj, dedent("""\
            begin characters;
              dimensions nchar=%s;
              format symbols="01" missing=?;
              charstatelabels""" % len(data))
        labels = []

        for i, cc in enumerate(sorted(data, key=lambda cc:
                (cognate_class_names[cc], cc))):
            labels.append("    %d %s" % (i+1, cognate_class_name_formatter(cc)))
            # try:
            #     labels.append("    %d %s_%d" % (i+1, cognate_class_names[cc],
            #         cc))
            # except KeyError:
            #     labels.append("    %d Lexeme_%d" % (i+1, cc[1]))
        print>>fileobj, ",\n".join(labels)
        print>>fileobj, "  ;\n  matrix"
    else:
        assert dialect == "BP"
        print>>fileobj, dedent("""\
            begin data;
              dimensions ntax=%s nchar=%s;
              taxlabels %s;
              format symbols="01";
              matrix
            """ % (len(languages), len(data), " ".join(language_names)))

    if LABEL_COGNATE_SETS:
        row = [" "*9] + [str(i).ljust(10) for i in range(len(data))[10::10]]
        print>>fileobj, "    %s[ %s ]" % (" "*max_len, "".join(row))
        row = [" "*9] + [".         " for i in range(len(data))[10::10]]
        print>>fileobj, "    %s[ %s ]" % (" "*max_len, "".join(row))

    for language in languages:
        row = []
        for cc in sorted(data, key=lambda cc: (cognate_class_names[cc], cc)):
            if language.id in data[cc]:
                row.append("1")
            elif language.id in data_missing[cc]:
                row.append("?")
            else:
                row.append("0")
        print>>fileobj, "    '%s'%s%s" % (language.ascii_name,
                " "*(max_len - len(language.ascii_name)), "".join(row))
    print>>fileobj, "  ;\nend;\n"

    if dialect == "BP":
        print>>fileobj, dedent("""\
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
    print>>fileobj, "[ Processing time: %02d:%02d ]" % (minutes, seconds)
    print>>fileobj, "[ %s ]" % " ".join(sys.argv)
    return fileobj
