from __future__ import print_function
from textwrap import dedent
import re
import sys
import time
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
    Clade
from ielex.forms import EditCognateClassCitationForm
from ielex.shortcuts import minifiedJs
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
        context["minifiedJs"] = minifiedJs
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
            "includePllLoan": 0,
            "excludeMarkedMeanings": 1,
            "excludeMarkedLanguages": 1}
        form = ChooseNexusOutputForm(defaults)
        return self.render_to_response({"form": form})

    def post(self, request):
        form = ChooseNexusOutputForm(request.POST)
        if form.is_valid():
            export = NexusExport(exportName=self.fileNameForForm(form))
            export.setSettings(form)
            export.bump(request)
            export.save()
            return HttpResponseRedirect('/nexus/export/')
        return self.render_to_response({"form": form})

    def fileNameForForm(self, form):
        return "%s_CoBL-IE_Lgs%03d_Mgs%03d_%s_%s.nex" % (
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

        print(dump_cognate_data(
            form.cleaned_data["language_list"],
            form.cleaned_data["meaning_list"]
            # set(form.cleaned_data["reliability"]),
        ), file=response)
        return response


def write_nexus(language_list_name,       # str
                meaning_list_name,        # str
                dialect,                  # string
                **kwargs):
    '''
    In kwargs:
    label_cognate_sets :: bool
    ascertainment_marker :: bool
    excludeNotSwadesh :: bool
    excludePllDerivation :: bool
    excludeIdeophonic :: bool
    excludeDubious :: bool
    excludeLoanword :: bool
    excludePllLoan :: bool
    includePllLoan :: bool
    excludeMarkedLanguages :: bool | missing in older settings
    excludeMarkedMeanings :: bool | missing in older settings
    Returns:
    {exportData :: str,
     exportBEAUti :: str,
     cladeMemberships :: str,
     computeCalibrations :: str}
    '''
    start_time = time.time()
    dialect_full_name = dict(ChooseNexusOutputForm.DIALECT)[dialect]

    # get data together
    language_list = LanguageList.objects.get(name=language_list_name)
    if kwargs.get('excludeMarkedLanguages', True):
        languages = language_list.languages.exclude(notInExport=True).all()
    else:
        languages = language_list.languages.all()
    language_names = [language.ascii_name for language in languages]

    meaning_list = MeaningList.objects.get(name=meaning_list_name)
    if kwargs.get('excludeMarkedMeanings', True):
        meanings = meaning_list.meanings.exclude(
            exclude=True).all().order_by("meaninglistorder")
    else:
        meanings = meaning_list.meanings.all().order_by("meaninglistorder")
    max_len = max([len(l) for l in language_names])

    matrix, cognate_class_names, assumptions = construct_matrix(
        languages, meanings, **kwargs)

    # Export data to compose:
    exportData = []
    exportBEAUti = []

    def appendExports(s):
        exportData.append(s)
        exportBEAUti.append(s)

    appendExports("#NEXUS\n\n[ Generated by: %s ]\n" %
                  settings.project_long_name)
    try:
        if settings.project_citation:
            appendExports(nexus_comment(settings.project_citation))
    except AttributeError:
        pass

    appendExports(getNexusComments(language_list_name,
                                   meaning_list_name,
                                   dialect_full_name,
                                   **kwargs))

    if dialect == "NN":
        max_len += 2  # taxlabels are quoted
        exportData.append(dedent("""\
            begin taxa;
              dimensions ntax=%s;
              taxlabels %s;
            end;
            """ % (len(languages), " ".join(language_names))))
        exportData.append(dedent("""\
            begin characters;
              dimensions nchar=%s;
              format symbols="01" missing=?;
              charstatelabels""" % len(cognate_class_names)))
        exportBEAUti.append(dedent("""\
            begin characters;
              dimensions nchar=%s;
              format symbols="01" missing=?;""" % len(cognate_class_names)))
        labels = []
        for i, cc in enumerate(cognate_class_names):
            labels.append("    %d %s" % (i + 1, cc))
        exportData.append(",\n".join(labels))
        exportData.append("  ;\n  matrix")
        exportBEAUti.append("  matrix")

    elif dialect == "MB":
        exportData.append(dedent("""\
            begin taxa;
              dimensions ntax=%s;
              taxlabels %s;
            end;
            """ % (len(languages),
                   " ".join(language_names))))
        appendExports(dedent("""\
            begin characters;
              dimensions nchar=%s;
              format missing=? datatype=restriction;
              matrix
            """ % len(cognate_class_names)))

    else:
        assert dialect == "BP"
        appendExports(dedent("""\
            begin data;
              dimensions ntax=%s nchar=%s;
              taxlabels %s;
              format symbols="01";
              matrix
            """ % (len(languages),
                   len(cognate_class_names),
                   " ".join(language_names))))

    if kwargs['label_cognate_sets']:
        row = [" " * 9] + [
            str(i).ljust(10) for i in
            range(len(cognate_class_names))[10::10]]
        appendExports("   %s[ %s ]" % (" " * max_len, "".join(row)))
        row = ".".join([" " * 9] * (int((len(cognate_class_names) + 9) / 10)))
        appendExports("   %s[ %s ]" % (" " * max_len, row))

    # matrix comments requested in #314:
    matrixComments = getMatrixCommentsFromCognateNames(
        cognate_class_names, padding=max_len + 4)
    appendExports(matrixComments + "\n")

    # write matrix
    for row in matrix:
        language_name, row = row[0], row[1:]
        if dialect == "NN":
            def quoted(s):
                return "'%s'" % s
        else:
            def quoted(s):
                return s
        appendExports("    %s %s%s" %
                      (quoted(language_name),
                       " " * (max_len - len(quoted(language_name))),
                       "".join(row)))
    # matrix comments requested in #314:
    appendExports(matrixComments)
    appendExports("  ;\nend;\n")

    if dialect == "BP":
        exportData.append(dedent("""\
            begin BayesPhylogenies;
                Chains 1;
                it 12000000;
                Model m1p;
                bf emp;
                cv 2;
                pf 10000;
                autorun;
            end;
            """))

    # write charset assumptions
    def writeCharsetAssumptions(appendTo):
        appendTo.append("begin assumptions;")
        for charset in assumptions:
            appendTo.append("    " + charset)
        appendTo.append("end;")
    if assumptions and dialect != "NN":
        writeCharsetAssumptions(exportData)
    # Always write charset assumptions to BEAUti export:
    writeCharsetAssumptions(exportBEAUti)

    # Add location data to BEAUti export:
    exportBEAUti.append(getNexusLocations(languages))
    # Add charstatelabels data to BEAUTi export:
    exportBEAUti.append(getCharstateLabels(cognate_class_names))

    # get contributor list:
    # lexical sources
    # lexemes coded by
    # cognate sources
    # cognates coded by

    # appendExports("[ %s ]" % " ".join(sys.argv))
    print("# Processed %s cognate sets from %s languages" %
          (len(cognate_class_names), len(matrix)), file=sys.stderr)
    # Data for exportBEAUti and constraints:
    memberships = cladeMembership(
        language_list, kwargs.get('excludeMarkedLanguages', True))
    calibrations = computeCalibrations(
        language_list, kwargs.get('excludeMarkedLanguages', True))
    exportBEAUti.append(memberships)
    exportBEAUti.append(calibrations)
    # timing
    seconds = int(time.time() - start_time)
    minutes = seconds // 60
    seconds %= 60
    appendExports("[ Processing time: %02d:%02d ]" % (minutes, seconds))
    # Return combined data:
    return {
        'exportData': "\n".join(exportData),      # Requested export
        'exportBEAUti': "\n".join(exportBEAUti),  # BEAUti specific export
        'cladeMemberships': memberships,
        'computeCalibrations': calibrations
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
        if isinstance(cc, int):
            return "%s_cognate_%s" % (gloss, cc)
        else:
            assert isinstance(cc, tuple)
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
            for cc in sorted(data[meaning.gloss],
                             key=lambda x: (str(x),) if type(x) == int else x):
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

    lines = []  # lines in string to be returned by dump_cognate_data
    print("Processed", cognate_judgements.count(),
          "cognate judgements", file=sys.stderr)
    lines.append("\t".join(["cc_alias",
                            "cc_id",
                            "language",
                            "lexeme",
                            "lexeme_id",
                            "status"]))
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

        lines.append("\t".join([
            cj.lexeme.meaning.gloss + "-" + cj.cognate_class.alias,
            cj.cognate_class.id,
            cj.lexeme.language.ascii_name,
            str(cj.lexeme.phon_form.strip() or
                cj.lexeme.romanised.strip()),
            cj.lexeme.id,
            loanword_flag]))
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
        lines.append("\t".join([
            lexeme.meaning.gloss,
            "",
            lexeme.language.ascii_name,
            str(lexeme.phon_form.strip() or
                lexeme.romanised.strip()),
            lexeme.id,
            loanword_flag]))

    return "\n".join(lines) + "\n"


def cladeMembership(language_list, excludeMarkedLanguages):
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
    if excludeMarkedLanguages:
        baseLanguages = language_list.languages.exclude(notInExport=True)
    else:
        baseLanguages = language_list.languages
    for clade in clades:
        languages = baseLanguages.filter(
            languageclade__clade=clade).values_list(
            'ascii_name', flat=True)
        if len(languages) >= 1:
            taxsets.append("taxset ts%s = %s;" %
                           (clade.taxonsetName, " ".join(languages)))
    return "begin sets;\n%s\nend;\n" % "\n".join(taxsets)


def computeCalibrations(language_list, excludeMarkedLanguages):
    '''
    Computes the {clade,language} calibrations as described in #161:

    begin assumptions;
    calibrate tsTocharian = offsetlognormal(1.650,0.200,0.900)
    calibrate Latin = normal(2.050,0.075)
    end;
    '''
    def getDistribution(abstractDistribution):

        def yearToFloat(year):
            if year is None:
                return 0.0
            return round(float(year) / 1000, 3)

        if abstractDistribution.distribution == 'U':
            upper = yearToFloat(abstractDistribution.uniformUpper)
            lower = yearToFloat(abstractDistribution.uniformLower)
            return "uniform(%.3f,%.3f)" % (upper, lower)
        if abstractDistribution.distribution == 'N':
            mean = yearToFloat(abstractDistribution.normalMean)
            stDev = yearToFloat(abstractDistribution.normalStDev)
            return "normal(%.3f,%.3f)" % (mean, stDev)
        if abstractDistribution.distribution == 'L':
            mean = yearToFloat(abstractDistribution.logNormalMean)
            stDev = abstractDistribution.logNormalStDev or 0.0
            return "lognormal(%.3f,%.3f)" % (mean, stDev)
        if abstractDistribution.distribution == 'O':
            mean = yearToFloat(abstractDistribution.logNormalMean)
            stDev = abstractDistribution.logNormalStDev or 0.0
            offset = yearToFloat(abstractDistribution.logNormalOffset)
            return "offsetlognormal(%.3f,%.3f,%.3f)" % (offset, mean, stDev)
        return None

    if excludeMarkedLanguages:
        baseLanguages = language_list.languages.exclude(notInExport=True)
    else:
        baseLanguages = language_list.languages
    calibrations = []
    for clade in Clade.objects.filter(export=True, exportDate=True).all():
        cal = getDistribution(clade)
        lCount = baseLanguages.filter(languageclade__clade=clade).count()
        if cal is not None and lCount >= 1:
            calibrations.append("calibrate ts%s = %s" %
                                (clade.taxonsetName, cal))
    for language in baseLanguages.filter(historical=True).all():
        cal = getDistribution(language)
        if cal is not None:
            calibrations.append("calibrate %s = %s" %
                                (language.ascii_name, cal))
    return "begin assumptions;\n%s\nend;\n" % "\n".join(calibrations)


def getNexusComments(
        language_list_name,
        meaning_list_name,
        dialect_full_name,
        **kwargs):
    lines = ["[ Language list: %s ]" % language_list_name,
             "[ Meaning list: %s ]" % meaning_list_name,
             "[ Nexus dialect: %s ]" % dialect_full_name]
    comments = [
        ('label_cognate_sets', "[ Cognate set labels: %s ]"),
        ('ascertainment_marker',
         "[ Mark meaning sets for ascertainment correction: %s ]"),
        ('excludeNotSwadesh', "[ Exclude lexemes: not Swadesh: %s ]"),
        ('excludePllDerivation', "[ Exclude cog. sets: Pll. Derivation: %s ]"),
        ('excludeIdeophonic', "[ Exclude cog. sets: Ideophonic: %s ]"),
        ('excludeDubious', "[ Exclude cog. sets: Dubious: %s ]"),
        ('excludeLoanword', "[ Exclude cog. sets: Loan event: %s ]"),
        ('excludePllLoan', "[ Exclude cog. sets: Pll Loan: %s ]"),
        ('includePllLoan',
         "[ Include Pll Loan as independent cog. sets: %s ]"),
        ('excludeMarkedLanguages',
         "[ Exclude languages marked as 'not for export': %s ]"),
        ('excludeMarkedMeanings',
         "[ Exclude meanings marked as 'not for export': %s ]")
    ]
    for k, v in comments:
        if k in kwargs:
            lines.append(v % kwargs[k])
    lines.append("[ File generated: %s ]\n" %
                 time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    return '\n'.join(lines)


def getNexusLocations(languages):
    '''
    This function computes a `locations` block from some languages.
    '''
    lines = []
    for language in languages:
        if language.latitude is None or language.longitude is None:
            continue
        lines.append("  %s = %s %s;" % (language.ascii_name,
                                        language.latitude,
                                        language.longitude))
    return "\nbegin locations;\n%s\nend;\n" % "\n".join(lines)


def getCharstateLabels(cognate_class_names):
    '''
    This function computes a `charstatelabels` block
    for a given set of cognate classes.
    '''
    labels = []
    for i, cc in enumerate(cognate_class_names):
        labels.append("    %d %s" % (i + 1, cc))
    return "\nbegin charstatelabels;\n%s\nend;\n" % "\n".join(labels)


def getMatrixCommentsFromCognateNames(cognate_class_names, padding=0):
    # cognate_class_names :: [String]
    meaningRow = []  # Pieces to be joined with ''
    flagRow = ''
    idBucket = []  # Matrix of id chars

    meaning = ''
    meaningLength = 0

    def nextMeaning(m):
        if m != meaning:
            label = (' ' + meaning)[:meaningLength].ljust(meaningLength, ' ')
            meaningRow.append(label)
            return m, 1
        return meaning, meaningLength + 1

    groupRegex = r'^(.+)_group$'
    lexemeRegex = r'^(.+)_lexeme_(.+)$'
    cognateRegex = r'^(.+)_cognate_(.+)$'

    for name in cognate_class_names:
        groupMatch = re.match(groupRegex, name)
        if groupMatch:
            meaning, meaningLength = nextMeaning(groupMatch.group(1))
            flagRow += ' '
            idBucket.append('')
            continue
        lexemeMatch = re.match(lexemeRegex, name)
        if lexemeMatch:
            meaning, meaningLength = nextMeaning(lexemeMatch.group(1))
            flagRow += 'L'
            idBucket.append(lexemeMatch.group(2))
            continue
        cognateMatch = re.match(cognateRegex, name)
        if cognateMatch:
            meaning, meaningLength = nextMeaning(cognateMatch.group(1))
            flagRow += 'C'
            idBucket.append(cognateMatch.group(2))
            continue
        # Nothing matches:
        meaning, meaningLength = nextMeaning('')
        flagRow += '?'
        idBucket.append('')
    nextMeaning('')  # Append last meaning to meaningRow

    # Create idRows by padding and transposing ids:
    idMaxLen = max(*[len(i) for i in idBucket])
    idRows = [[x for x in id.rjust(idMaxLen, '-')] for id in idBucket]
    idRows = [''.join(row) for row in zip(*idRows)]

    commentRows = []

    def addComment(c):
        commentRows.append(" " * (padding - 1) + "[ %s ]" % c)

    addComment(''.join(meaningRow))
    commentRows.append("")
    addComment(flagRow)
    commentRows.append("")
    for idRow in idRows:
        addComment(idRow)

    return '\n'.join(commentRows)
