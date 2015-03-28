from __future__ import print_function
from textwrap import dedent
import time
import sys
from django.contrib.auth.decorators import login_required
# from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
# from django.core.urlresolvers import reverse_lazy # avail Django 1.4
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.generic import CreateView, UpdateView, TemplateView
#from django.views.generic import RedirectView
from django.contrib import messages
from ielex import settings
from ielex.lexicon.models import *
from ielex.lexicon.functions import local_iso_code_generator
from ielex.shortcuts import render_template
from ielex.forms import EditCognateClassCitationForm
from ielex.lexicon.forms import ChooseNexusOutputForm, DumpSnapshotForm
from ielex.lexicon.functions import nexus_comment

class FrontpageView(TemplateView):
    template_name = "frontpage.html"

    def get_context_data(self, **kwargs):
        context = super(FrontpageView,
                self).get_context_data(**kwargs)
        context["lexemes"] = Lexeme.objects.count()
        context["cognate_classes"] = CognateClass.objects.count()
        context["languages"] = Language.objects.count()
        context["meanings"] = Meaning.objects.count()
        context["coded_characters"] = CognateJudgement.objects.count()
        try:
            context["google_site_verification"] = settings.META_TAGS
        except AttributeError:
            pass
        return context

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

#class CognateClassRedirectView(RedirectView):

@login_required
def cognate_class_citation_delete(request, pk):
    cognate_class_citation = CognateClassCitation.objects.get(id=pk)
    cognate_class_id = cognate_class_citation.cognate_class.id
    cognate_class_citation.delete()
    return HttpResponseRedirect(reverse('cognate-set',
        args=[cognate_class_id]))

class NexusExportView(TemplateView):
    template_name = "nexus_list.html"

    def get(self, request):
        defaults = {"unique":1, "reliability":["L","X"], "language_list":1,
                "meaning_list":1, "dialect":"NN", "ascertainment_marker":0}
        form =  ChooseNexusOutputForm(defaults)
        return self.render_to_response({"form":form})

    def post(self, request):
        form =  ChooseNexusOutputForm(request.POST)
        if form.is_valid():
            #return HttpResponseRedirect(reverse("nexus-data"))
            return self.write_nexus_view(form)
        return self.render_to_response({"form":form})

    def write_nexus_view(self, form):
        """A wrapper to call the `write_nexus` function from a view"""
        # TODO: contributor and sources list

        # Create the HttpResponse object with the appropriate header.
        filename = "%s-%s-%s.nex" % (settings.project_short_name,
                form.cleaned_data["language_list"].name,
                form.cleaned_data["meaning_list"].name)
        response = HttpResponse(mimetype='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % \
                filename.replace(" ", "_")

        write_nexus(response,
                form.cleaned_data["language_list"],
                form.cleaned_data["meaning_list"],
                set(form.cleaned_data["reliability"]),
                form.cleaned_data["dialect"],
                True,
                form.cleaned_data["ascertainment_marker"],
                form.cleaned_data["use_iso_codes"]
                )
        return response

class DumpRawDataView(TemplateView):
    template_name = "dump_data.html"

    def get(self, request):
        defaults = {"language_list":1, "meaning_list":1,
                "reliability":["L","X"]}
        form =  DumpSnapshotForm(defaults)
        return self.render_to_response({"form":form})

    def post(self, request):
        form =  DumpSnapshotForm(request.POST)
        if form.is_valid():
            #return HttpResponseRedirect(reverse("nexus-data"))
            return self.dump_cognate_data_view(form)
        return self.render_to_response({"form":form})

    def dump_cognate_data_view(self, form):
        """A wrapper to call the `dump_cognate_data` function from a view"""

        # Create the HttpResponse object with the appropriate header.
        filename = "%s-%s-%s-data.csv" % (settings.project_short_name,
                form.cleaned_data["language_list"].name,
                form.cleaned_data["meaning_list"].name)
        response = HttpResponse(mimetype='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % \
                filename.replace(" ", "_")

        dump_cognate_data(response,
                form.cleaned_data["language_list"],
                form.cleaned_data["meaning_list"]
                # set(form.cleaned_data["reliability"]),
                )
        return response

def write_nexus(fileobj,
            language_list_name,   # string
            meaning_list_name,    # string
            exclude_ratings,      # set
            dialect,              # string
            LABEL_COGNATE_SETS,   # bool
            ascertainment_marker, # bool
            use_iso_codes):       # bool
    start_time = time.time()

    # get data together
    language_list = LanguageList.objects.get(name=language_list_name)
    languages = language_list.languages.all().order_by("languagelistorder")
    if use_iso_codes:
        names_and_iso_codes = []
        code_generator = local_iso_code_generator()
        language_names = []
        for language in languages:
            if language.iso_code and language.iso_code not in language_names:
                language_names.append(language.iso_code)
                names_and_iso_codes.append((language.ascii_name,
                    language.iso_code))
            else:
                iso_code = code_generator.next()
                language_names.append(iso_code)
                names_and_iso_codes.append((language.ascii_name, iso_code))
    else:
        language_names = [language.ascii_name for language in languages]

    meaning_list = MeaningList.objects.get(name=meaning_list_name)
    meanings = meaning_list.meanings.all().order_by("meaninglistorder")
    max_len = max([len(l) for l in language_names])

    matrix, cognate_class_names = construct_matrix(languages,
            meanings, exclude_ratings, ascertainment_marker)

    print("#NEXUS\n\n[ Generated by: %s ]" % settings.project_long_name, file=fileobj)
    try:
        if settings.project_citation:
            print(nexus_comment(settings.project_citation), file=fileobj)
    except AttributeError:
        pass

    print("[ Language list: %s ]" % language_list_name, file=fileobj)
    print("[ Meaning list: %s ]" % meaning_list_name, file=fileobj)
    print("[ Exclude rating/s: %s ]" % ", ".join(sorted(exclude_ratings)), file=fileobj)
    print("[ File generated: %s ]\n" % time.strftime("%Y-%m-%d %H:%M:%S",
            time.localtime()), file=fileobj)

    if dialect == "NN":
        max_len += 2 # taxlabels are quoted
        print(dedent("""\
            begin taxa;
              dimensions ntax=%s;
              taxlabels %s;
            end;
            """ % (len(languages), " ".join(language_names))), file=fileobj)
        print(dedent("""\
            begin characters;
              dimensions nchar=%s;
              format symbols="01" missing=?;
              charstatelabels""" % len(cognate_class_names)), file=fileobj)
        labels = []
        
        for i, cc in enumerate(cognate_class_names):
            labels.append("    %d %s" % (i+1, cc))
        print(*labels, sep=",\n", file=fileobj)
        print("  ;\n  matrix", file=fileobj)

    elif dialect == "MB":
        print(dedent("""\
            begin taxa;
              dimensions ntax=%s;
              taxlabels %s;
            end;

            begin characters;
              dimensions nchar=%s;
              format missing=? datatype=restriction;
              matrix
            """ % (len(languages), " ".join(language_names),
                len(cognate_class_names))), file=fileobj)

    else:
        assert dialect == "BP"
        print(dedent("""\
            begin data;
              dimensions ntax=%s nchar=%s;
              taxlabels %s;
              format symbols="01";
              matrix
            """ % (len(languages), len(cognate_class_names), " ".join(language_names))),
                    file=fileobj)

    if LABEL_COGNATE_SETS:
        row = [" "*9] + [str(i).ljust(10) for i in
                range(len(cognate_class_names))[10::10]]
        print("    %s[ %s ]" % (" "*max_len, "".join(row)), file=fileobj)
        row = [" "*9] + [".         " for i in range(len(cognate_class_names))[10::10]]
        print("    %s[ %s ]" % (" "*max_len, "".join(row)), file=fileobj)

    # write matrix
    if use_iso_codes:
        name2iso_code = dict(names_and_iso_codes)
    for row in matrix:
        language_name, row = row[0], row[1:]
        if dialect == "NN":
            quoted = lambda s: "'%s'" % s
        else:
            quoted = lambda s: s
        if use_iso_codes:
            language_name = name2iso_code[language_name]
        print("    %s %s%s" % (quoted(language_name),
                " "*(max_len - len(quoted(language_name))), "".join(row)), file=fileobj)
    print("  ;\nend;\n", file=fileobj)

    if use_iso_codes:
        print("[ ISO code: name (may include local codes) ]", file=fileobj)
        for name, iso_code in sorted(names_and_iso_codes, key=lambda e:e[1]):
            print("[ %s: %s ]" % (iso_code, name.ljust(35)), file=fileobj)

    if dialect == "BP":
        print(dedent("""\
            begin BayesPhylogenies;
                Chains 1;
                it 12000000;
                Model m1p;
                bf emp;
                cv 2;
                pf 10000;
                autorun;
            end;
            """), file=fileobj)

    # get contributor list:
    # lexical sources
    # lexemes coded by
    # cognate sources
    # cognates coded by

    # timing
    seconds = int(time.time() - start_time)
    minutes = seconds // 60
    seconds %= 60
    print("[ Processing time: %02d:%02d ]" % (minutes, seconds), file=fileobj)
    print("[ %s ]" % " ".join(sys.argv), file=fileobj)
    print("# Processed %s cognate sets from %s languages" %
            (len(cognate_class_names), len(matrix)), file=sys.stderr)
    return fileobj

def write_delimited(fileobj,
            language_list_name,
            meaning_list_name,
            exclude_ratings,
            LABEL_COGNATE_SETS):
    start_time = time.time()

    language_list = LanguageList.objects.get(name=language_list_name)
    languages = language_list.languages.all().order_by("languagelistorder")
    meaning_list = MeaningList.objects.get(name=meaning_list_name)
    meanings = meaning_list.meanings.all().order_by("meaninglistorder")
    matrix, cognate_class_names = construct_matrix(languages,
            meanings, exclude_ratings, False) # no ascertainment marker
    print("\t" + "\t".join(cognate_class_names), file=fileobj)
    for row in matrix:
        print(*row, sep="\t", file=fileobj)

    seconds = int(time.time() - start_time)
    minutes = seconds // 60
    seconds %= 60
    print("# Processing time: %02d:%02d" % (minutes, seconds), file=sys.stderr)
    print("# %s" % " ".join(sys.argv), file=sys.stderr)
    print("# Processed %s cognate sets from %s languages" %
            (len(cognate_class_names), len(matrix)), file=sys.stderr)
    return fileobj

def construct_matrix(
    languages,
    meanings,
    exclude_ratings,
    ascertainment_marker):

        matrix = []
        # all cognate classes
        cognate_class_ids = CognateClass.objects.all().values_list("id", flat=True)
        cognate_class_dict = dict(CognateJudgement.objects.all().values_list(
                "cognate_class__id", "lexeme__meaning__gloss").distinct())
        #logging.info("len cognate_class_ids = %s" % len(cognate_class_ids))

        # make a list for each meaning of the languages lacking any lexeme
        # with that meaning
        missing = {}
        for meaning in meanings:
            missing[meaning] = [language.id for language in languages if not
                    language.lexeme_set.filter(meaning=meaning).exists()]

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
                    if cj.lexeme.language in languages
                    and not (cj.reliability_ratings & exclude_ratings)]
            if language_ids:
                try:
                    meaning = CognateClass.objects.get(id=cc).get_meaning()
                    data[cc] = language_ids
                    try:
                        data_missing[cc] = missing[meaning]
                    except KeyError:
                        data_missing[cc] = []
                except AssertionError:
                    pass

        # adds a cc code for all the lexemes which are not registered as
        # belonging to a cognate class
        # TODO look at LexemeCitation reliablity ratings here too
        uniques = Lexeme.objects.filter(
                language__in=languages,
                meaning__in=meanings,
                cognate_class__isnull=True).values_list(
                        "language__id",
                        "meaning__id",
                        "id")

        for language_id, meaning_id, lexeme_id in uniques:
            # add singleton ids to cognate_class_dict
            meaning = Meaning.objects.get(id=meaning_id)
            cc = ("U", lexeme_id)
            data[cc] = [language_id]
            cognate_class_dict[cc] = meaning.gloss
            try:
                data_missing[cc] = missing[meaning]
            except KeyError:
                data_missing[cc] = []

        # make matrix
        def cognate_class_name_formatter(cc):
            gloss = cognate_class_dict[cc]
            if type(cc) == int:
                return "%s_cogset_%s" % (gloss, cc)
            else:
                assert type(cc) == tuple
                return "%s_lexeme_%s" % (gloss, cc[1])

        # sort cognate class ids by meaning
        data_keys = sorted(data, key=lambda cc: (cognate_class_dict[cc], cc))
        if ascertainment_marker: # store indexes where meaning blocks change
            ascertainment_marker_idx = [i for i, cc in enumerate(data_keys) if
                    cognate_class_dict[cc] if 
                    cognate_class_dict[cc] != cognate_class_dict[data_keys[i-1]]]

        cognate_class_names = []
        make_header = True
        for language in languages:
            row = [language.ascii_name]
            for i, cc in enumerate(data_keys):
                if ascertainment_marker and i in ascertainment_marker_idx:
                    # start of a new group
                    # if language.id in data_missing[cc]:
                    #     row.append("?")
                    # else:
                    row.append("0")
                    if make_header:
                        cognate_class_names.append("%s_group" %
                                cognate_class_dict[cc])
                if make_header:
                    cognate_class_names.append(cognate_class_name_formatter(cc))
                if language.id in data[cc]:
                    row.append("1")
                elif language.id in data_missing[cc]:
                    row.append("?")
                else:
                    row.append("0")
            matrix.append(row)
            make_header = False

        return matrix, cognate_class_names

def dump_cognate_data(
            fileobj,
            language_list_name,
            meaning_list_name):
    language_list = LanguageList.objects.get(name=language_list_name)
    languages = language_list.languages.all().order_by("languagelistorder")
    meaning_list = MeaningList.objects.get(name=meaning_list_name)
    meanings = meaning_list.meanings.all().order_by("meaninglistorder")

    cognate_judgements = CognateJudgement.objects.filter(
            lexeme__language__in=languages,
            lexeme__meaning__in=meanings
            ).order_by("lexeme__meaning", "cognate_class__alias", "lexeme__language")

    print("Processed", cognate_judgements.count(), "cognate judgements",
            file=sys.stderr)
    print("cc_alias", "cc_id", "language", "lexeme", "lexeme_id", "status",
            sep="\t", file=fileobj)
    for cj in cognate_judgements:
        if ("L" in cj.reliability_ratings) or ("L" in cj.lexeme.reliability_ratings):
            loanword_flag = "LOAN"
        else:
            loanword_flag = ""
        if ("X" in cj.reliability_ratings) or ("X" in cj.lexeme.reliability_ratings):
            if loanword_flag:
                loanword_flag += ",EXCLUDE"
            else:
                loanword_flag += "EXCLUDE"

        print(cj.lexeme.meaning.gloss+"-"+cj.cognate_class.alias,
                cj.cognate_class.id, cj.lexeme.language.ascii_name,
                unicode(cj.lexeme.phon_form.strip() or
                cj.lexeme.source_form.strip()), cj.lexeme.id,
                loanword_flag, sep="\t", file=fileobj)
    lexemes = Lexeme.objects.filter(
            language__in=languages,
            meaning__in=meanings,
            cognate_class=None
            ).order_by("meaning", "language")
    for lexeme in lexemes:
        if ("L" in lexeme.reliability_ratings):
            loanword_flag = "LOAN"
        else:
            loanword_flag = ""
        if ("X" in lexeme.reliability_ratings):
            if loanword_flag:
                loanword_flag += ",EXCLUDE"
            else:
                loanword_flag += "EXCLUDE"
        print(lexeme.meaning.gloss,
                "", lexeme.language.ascii_name,
                unicode(lexeme.phon_form.strip() or
                lexeme.source_form.strip()), lexeme.id, loanword_flag,
                sep="\t", file=fileobj)

    return fileobj
