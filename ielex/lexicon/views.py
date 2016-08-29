from __future__ import print_function
from textwrap import dedent
import time
import sys
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, UpdateView, TemplateView
from ielex import settings
from ielex.lexicon.models import CognateClass, \
                                 CognateClassCitation, \
                                 CognateJudgement, \
                                 LanguageList, \
                                 Lexeme, \
                                 MeaningList, \
                                 NexusExport, \
                                 Clade, \
                                 Language
from ielex.forms import EditCognateClassCitationForm
from ielex.lexicon.forms import ChooseNexusOutputForm, DumpSnapshotForm
from ielex.lexicon.functions import nexus_comment
from ielex.lexicon.defaultModels import getDefaultWordlistId, \
                                        getDefaultLanguagelistId

try:
    if settings.default_language_list != "all":
        LanguageList.DEFAULT = settings.default_language_list
except AttributeError:
    pass


class CognateClassCitationUpdateView(UpdateView):
    model = CognateClassCitation
    form_class = EditCognateClassCitationForm
    template_name = "generic_update.html"

    def get_context_data(self, **kwargs):
        context = super(
            CognateClassCitationUpdateView, self).get_context_data(**kwargs)
        cc_id = context["object"].cognate_class.id
        context["title"] = "New cognate class citation"
        context["heading"] = "Citation to cognate class %s" % cc_id
        context["cancel_dest"] = reverse(
            "cognate-set", kwargs={"cognate_id": cc_id})
        return context


class CognateClassCitationCreateView(CreateView):
    form_class = EditCognateClassCitationForm
    template_name = "generic_update.html"

    def get_context_data(self, **kwargs):
        cc_id = int(self.kwargs["cognate_id"])
        context = super(
            CognateClassCitationCreateView,
            self).get_context_data(**kwargs)
        context["title"] = "New cognate class citation"
        context["heading"] = "Citation to cognate class %s" % cc_id
        context["cancel_dest"] = reverse(
            "cognate-set", kwargs={"cognate_id": cc_id})
        return context

    def get_form_kwargs(self):
        """Need to instantiate the object and set the cognate_class parameter
        here, since fields in the Meta.exclude attribute of ModelForm classes
        can't otherwise be set by forms.
        """
        cc_id = int(self.kwargs["cognate_id"])
        self.object = CognateClassCitation()
        self.object.cognate_class = CognateClass.objects.get(id=cc_id)
        kwargs = super(
            CognateClassCitationCreateView, self).get_form_kwargs()
        return kwargs

# class CognateClassRedirectView(RedirectView):


@login_required
def cognate_class_citation_delete(request, pk):
    cognate_class_citation = CognateClassCitation.objects.get(id=pk)
    cognate_class_id = cognate_class_citation.cognate_class.id
    cognate_class_citation.delete()
    return HttpResponseRedirect(
        reverse('cognate-set', args=[cognate_class_id]))


class NexusExportView(TemplateView):
    template_name = "nexus_list.html"

    def get(self, request):
        defaults = {
            "unique": 1,
            "language_list": getDefaultLanguagelistId(request),
            "meaning_list": getDefaultWordlistId(request),
            "dialect": "NN",
            "ascertainment_marker": 1,
            "excludeNotSwadesh": 1,
            "excludePllDerivation": 1,
            "excludeIdeophonic": 1,
            "excludeDubious": 1,
            "excludeLoanword": 0,
            "excludePllLoan": 1,
            "includePllLoan": 0}
        form = ChooseNexusOutputForm(defaults)
        return self.render_to_response({"form": form})

    def post(self, request):
        form = ChooseNexusOutputForm(request.POST)
        if form.is_valid():
            export = NexusExport(exportName=self.fileNameForForm(form))
            export.setSettings(form)
            export.bump(request)
            export.save()
            return HttpResponseRedirect(reverse("view_nexus_export",
                                        args=[export.id]))
        return self.render_to_response({"form": form})

    def fileNameForForm(self, form):
        return "%s_CoBL-IE_Lgs%s_Mgs%s_%s_%s.nex" % (
            time.strftime("%Y-%m-%d"),
            # settings.project_short_name,
            form.cleaned_data["language_list"].languages.filter(
                notInExport=False).count(),
            form.cleaned_data["meaning_list"].meanings.filter(
                exclude=False).count(),
            form.cleaned_data["language_list"].name,
            form.cleaned_data["meaning_list"].name)


class DumpRawDataView(TemplateView):
    template_name = "dump_data.html"

    def get(self, request):
        defaults = {
            "language_list": 1, "meaning_list": 1,
            "reliability": ["L", "X"]}
        form = DumpSnapshotForm(defaults)
        return self.render_to_response({"form": form})

    def post(self, request):
        form = DumpSnapshotForm(request.POST)
        if form.is_valid():
            # return HttpResponseRedirect(reverse("nexus-data"))
            return self.dump_cognate_data_view(form)
        return self.render_to_response({"form": form})

    def dump_cognate_data_view(self, form):
        """A wrapper to call the `dump_cognate_data` function from a view"""

        # Create the HttpResponse object with the appropriate header.
        filename = "%s-%s-%s-data.csv" % (
            settings.project_short_name,
            form.cleaned_data["language_list"].name,
            form.cleaned_data["meaning_list"].name)
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % \
            filename.replace(" ", "_")

        dump_cognate_data(
            response,
            form.cleaned_data["language_list"],
            form.cleaned_data["meaning_list"]
            # set(form.cleaned_data["reliability"]),
            )
        return response


def write_nexus(fileobj,                  # file object
                language_list_name,       # str
                meaning_list_name,        # str
                dialect,                  # string
                **kwargs):
    # In kwargs:
    # label_cognate_sets :: bool
    # ascertainment_marker :: bool
    # excludeNotSwadesh :: bool
    # excludePllDerivation :: bool
    # excludeIdeophonic :: bool
    # excludeDubious :: bool
    # excludeLoanword :: bool
    # excludePllLoan :: bool
    # includePllLoan :: bool
    start_time = time.time()
    dialect_full_name = dict(ChooseNexusOutputForm.DIALECT)[dialect]

    # get data together
    language_list = LanguageList.objects.get(name=language_list_name)
    languages = language_list.languages.exclude(
        notInExport=True).all()
    language_names = [language.ascii_name for language in languages]

    meaning_list = MeaningList.objects.get(name=meaning_list_name)
    meanings = meaning_list.meanings.exclude(
        exclude=True).all().order_by("meaninglistorder")
    max_len = max([len(l) for l in language_names])

    matrix, cognate_class_names, assumptions = construct_matrix(
        languages, meanings, **kwargs)

    print("#NEXUS\n\n[ Generated by: %s ]" %
          settings.project_long_name, file=fileobj)
    try:
        if settings.project_citation:
            print(nexus_comment(settings.project_citation), file=fileobj)
    except AttributeError:
        pass

    print("[ Language list: %s ]" % language_list_name, file=fileobj)
    print("[ Meaning list: %s ]" % meaning_list_name, file=fileobj)
    print("[ Nexus dialect: %s ]" % dialect_full_name, file=fileobj)
    print("[ Cognate set labels: %s ]" % kwargs['label_cognate_sets'],
          file=fileobj)
    print("[ Mark meaning sets for ascertainment correction: %s ]" %
          kwargs['ascertainment_marker'], file=fileobj)
    print("[ Exclude lexemes: not Swadesh: %s ]" % kwargs['excludeNotSwadesh'],
          file=fileobj)
    print("[ Exclude cog. sets: Pll. Derivation: %s ]" %
          kwargs['excludePllDerivation'],
          file=fileobj)
    print("[ Exclude cog. sets: Ideophonic: %s ]" %
          kwargs['excludeIdeophonic'],
          file=fileobj)
    print("[ Exclude cog. sets: Dubious: %s ]" %
          kwargs['excludeDubious'], file=fileobj)
    print("[ Exclude cog. sets: Loan event: %s ]" %
          kwargs['excludeLoanword'], file=fileobj)
    print("[ Exclude cog. sets: Pll Loan: %s ]" %
          kwargs['excludePllLoan'], file=fileobj)
    print("[ Include Pll Loan as independent cog. sets: %s ]" %
          kwargs['includePllLoan'], file=fileobj)
    print("[ File generated: %s ]\n" % time.strftime("%Y-%m-%d %H:%M:%S",
          time.localtime()), file=fileobj)

    if dialect == "NN":
        max_len += 2  # taxlabels are quoted
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
            """ % (len(languages),
                   len(cognate_class_names), " ".join(language_names))),
              file=fileobj)

    if kwargs['label_cognate_sets']:
        row = [" "*9] + [
            str(i).ljust(10) for i in
            range(len(cognate_class_names))[10::10]]
        print("   %s[ %s ]" % (" "*max_len, "".join(row)), file=fileobj)
        row = [" "*9] + [
            ".         " for i in range(len(cognate_class_names))[10::10]]
        print("   %s[ %s ]" % (" "*max_len, "".join(row)), file=fileobj)

    # write matrix
    for row in matrix:
        language_name, row = row[0], row[1:]
        if dialect == "NN":
            def quoted(s):
                return "'%s'" % s
        else:
            def quoted(s):
                return s
        print("    %s %s%s" % (quoted(language_name),
              " "*(max_len - len(quoted(language_name))),
              "".join(row)), file=fileobj)
    print("  ;\nend;\n", file=fileobj)

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

    # write assumptions
    if assumptions:
        print("begin assumptions;", file=fileobj)
        for charset in assumptions:
            print("   ", charset, file=fileobj)
        print("end;", file=fileobj)

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
    # print("[ %s ]" % " ".join(sys.argv), file=fileobj)
    print("# Processed %s cognate sets from %s languages" %
          (len(cognate_class_names), len(matrix)), file=sys.stderr)
    # Return combined data:
    return {
        'fileobj': fileobj,
        'cladeMemberships': cladeMembership(language_list),
        'computeCalibrations': computeCalibrations(language_list)
    }


def construct_matrix(languages,                # [Language]
                     meanings,                 # [Meaning]
                     ascertainment_marker,     # bool
                     excludeNotSwadesh,        # bool
                     excludePllDerivation,     # bool
                     excludeIdeophonic,        # bool
                     excludeDubious,           # bool
                     excludeLoanword,          # bool
                     excludePllLoan,           # bool
                     includePllLoan,           # bool
                     **kwargs):                # don't care

        # Specifying cognate classes we're interested in:
        cognateJudgementFilter = {
            'lexeme__language__in': languages,
            'lexeme__meaning__in': meanings
        }
        # If excludeNotSwadesh, only allow cjs
        # with a lexeme that is not_swadesh_term=False
        if excludeNotSwadesh:
            cognateJudgementFilter['lexeme__not_swadesh_term'] = False
        # Filtering interesting cognate judgements:
        wantedCJs = CognateJudgement.objects.filter(**cognateJudgementFilter)
        if excludePllDerivation:
            wantedCJs = wantedCJs.exclude(
                cognate_class__parallelDerivation=True)
        if excludeIdeophonic:
            wantedCJs = wantedCJs.exclude(cognate_class__ideophonic=True)
        if excludeDubious:
            wantedCJs = wantedCJs.exclude(cognate_class__dubiousSet=True)
        if excludeLoanword:
            wantedCJs = wantedCJs.exclude(cognate_class__loanword=True)
        elif excludePllLoan:  # not excludeLoanword and excludePllLoan
            wantedCJs = wantedCJs.exclude(
                cognate_class__parallelLoanEvent=True)
        elif includePllLoan:  # not excludeLoanword and includePllLoan
            raise ValueError('Case not implemented.')  # FIXME IMPLEMENT
        # synonymous cognate classes (i.e. cognate reflexes representing
        # a single Swadesh meaning)
        cognate_classes = defaultdict(list)
        for cc, meaning in wantedCJs.order_by(
                           "lexeme__meaning",
                           "cognate_class").values_list(
                               "cognate_class__id",
                               "lexeme__meaning__gloss").distinct():
            cognate_classes[meaning].append(cc)

        # Lexemes which shall be excluded:
        exclude_lexemes = set()  # :: set(lexeme.id)
        if excludeNotSwadesh:
            exclude_lexemes |= set(Lexeme.objects.filter(
                not_swadesh_term=True).values_list("id", flat=True))

        # languages lacking any lexeme for a meaning
        languages_missing_meaning = dict()
        # languages having a reflex for a cognate set
        '''
        data :: meaning.gloss -> cognate_classes[meaning.gloss] -> [language]
        '''
        data = dict()
        for meaning in meanings:
            languages_missing_meaning[meaning.gloss] = [
                language for language in
                languages if not
                language.lexeme_set.filter(meaning=meaning).exists()]
            for cc in cognate_classes[meaning.gloss]:
                matches = [
                    cj.lexeme.language for cj in
                    CognateJudgement.objects.filter(
                        cognate_class=cc,
                        lexeme__meaning=meaning) if cj.lexeme.language in
                    languages and cj.lexeme.id not in exclude_lexemes]
                if matches:
                    data.setdefault(meaning.gloss, dict())[cc] = matches

        # adds a cc code for all singletons
        # (lexemes which are not registered as
        # belonging to a cognate class), and add to cognate_class_dict
        for lexeme in Lexeme.objects.filter(
                language__in=languages,
                meaning__in=meanings,
                cognate_class__isnull=True):
            if lexeme.id not in exclude_lexemes:
                cc = ("U", lexeme.id)  # use tuple for sorting
                data[lexeme.meaning.gloss].setdefault(
                    cc, list()).append(lexeme.language)

        def cognate_class_name_formatter(cc, gloss):
            # gloss = cognate_class_dict[cc]
            if type(cc) == int:
                return "%s_cognate_%s" % (gloss, cc)
            else:
                assert type(cc) == tuple
                return "%s_lexeme_%s" % (gloss, cc[1])

        # make matrix
        matrix, cognate_class_names, assumptions = list(), list(), list()
        make_header = True
        col_num = 0
        for language in languages:
            row = [language.ascii_name]
            for meaning in meanings:
                if ascertainment_marker:
                    if language in languages_missing_meaning[meaning.gloss]:
                        row.append("?")
                    else:
                        row.append("0")
                    if make_header:
                        col_num += 1
                        start_range = col_num
                        cognate_class_names.append("%s_group" % meaning.gloss)
                for cc in sorted(data[meaning.gloss]):
                    if ascertainment_marker and make_header:
                        col_num += 1
                        cognate_class_names.append(
                            cognate_class_name_formatter(cc, meaning.gloss))
                    if language in data[meaning.gloss][cc]:
                        row.append("1")
                    elif language in languages_missing_meaning[meaning.gloss]:
                        row.append("?")
                    else:
                        row.append("0")
                if ascertainment_marker and make_header:
                    end_range = col_num
                    assumptions.append(
                        "charset %s = %s-%s;" %
                        (meaning.gloss, start_range, end_range))

            matrix.append(row)
            make_header = False

        return matrix, cognate_class_names, assumptions


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
            ).order_by(
                "lexeme__meaning",
                "cognate_class__alias",
                "lexeme__language")

    print("Processed", cognate_judgements.count(),
          "cognate judgements", file=sys.stderr)
    print("cc_alias", "cc_id", "language",
          "lexeme", "lexeme_id", "status",
          sep="\t", file=fileobj)
    for cj in cognate_judgements:
        if ("L" in cj.reliability_ratings) or \
           ("L" in cj.lexeme.reliability_ratings):
            loanword_flag = "LOAN"
        else:
            loanword_flag = ""
        if ("X" in cj.reliability_ratings) or \
           ("X" in cj.lexeme.reliability_ratings):
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
                      lexeme.source_form.strip()),
              lexeme.id, loanword_flag,
              sep="\t", file=fileobj)

    return fileobj


def cladeMembership(language_list):
    '''
    Computes the clade memberships as described in #50:

    begin sets;
    taxset tsAnatolian = Hittite Luvian Lycian Palaic;
    taxset tsTocharian = TocharianA TocharianB;
    taxset tsArmenian = ArmenianClassical ArmenianWestern ArmenianEastern;
    end;
    '''
    taxsets = []
    clades = Clade.objects.filter(export=True).all()
    for clade in clades:
        languages = language_list.languages.exclude(
            notInExport=True).filter(
            languageclade__clade=clade).values_list(
            'ascii_name', flat=True)
        if len(languages) >= 1:
            taxsets.append("taxset ts%s = %s;" %
                           (clade.taxonsetName, " ".join(languages)))
    return "begin sets;\n%s\nend;\n" % "\n".join(taxsets)


def computeCalibrations(language_list):
    '''
    Computes the {clade,language} calibrations as described in #161:

    begin assumptions;
    calibrate tsTocharian = offsetlognormal(1.650,0.200,0.900)
    calibrate Latin = normal(2.050,0.075)
    end;
    '''
    def getDistribution(abstractDistribution):
        if abstractDistribution.distribution == 'U':
            upper = round(abstractDistribution.uniformUpper / 1000, 3)
            lower = round(abstractDistribution.uniformLower / 1000, 3)
            return "uniform(%.3f,%.3f)" % (upper, lower)
        if abstractDistribution.distribution == 'N':
            mean = round(abstractDistribution.normalMean / 1000, 3)
            stDev = round(abstractDistribution.normalStDev / 1000, 3)
            return "normal(%.3f,%.3f)" % (mean, stDev)
        if abstractDistribution.distribution == 'L':
            mean = round(abstractDistribution.logNormalMean / 1000, 3)
            stDev = abstractDistribution.logNormalStDev
            return "lognormal(%.3f,%f)" % (mean, stDev)
        if abstractDistribution.distribution == 'O':
            mean = round(abstractDistribution.logNormalMean / 1000, 3)
            stDev = abstractDistribution.logNormalStDev
            offset = round(abstractDistribution.logNormalOffset / 1000, 3)
            return "offsetlognormal(%.3f,%.3f,%f)" % (offset, mean, stDev)
        return None

    calibrations = []
    for clade in Clade.objects.filter(export=True, exportDate=True).all():
        cal = getDistribution(clade)
        lCount = language_list.languages.exclude(
            notInExport=True).filter(
            languageclade__clade=clade).count()
        if cal is not None and lCount >= 1:
            calibrations.append("calibrate ts%s = %s" %
                                (clade.taxonsetName, cal))
    for language in language_list.languages.filter(
                    historical=True, notInExport=False).all():
        cal = getDistribution(language)
        if cal is not None:
            calibrations.append("calibrate %s = %s" %
                                (language.ascii_name, cal))
    return "begin assumptions;\n%s\nend;\n" % "\n".join(calibrations)
