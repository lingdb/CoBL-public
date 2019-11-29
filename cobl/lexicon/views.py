from __future__ import print_function
from textwrap import dedent
from string import ascii_uppercase
import re
import sys
import time
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from cobl.shortcuts import render_template
from django.views.generic import CreateView, UpdateView, TemplateView
from cobl import settings
from cobl.lexicon.models import CognateClass, \
    CognateClassCitation, \
    CognateJudgement, \
    LanguageList, \
    LanguageClade, \
    Lexeme, \
    MeaningList, \
    NexusExport, \
    NEXUS_DIALECT_CHOICES, \
    Source, \
    Clade
from cobl.forms import EditCognateClassCitationForm
from cobl.shortcuts import minifiedJs
from cobl.lexicon.forms import ChooseNexusOutputForm, DumpSnapshotForm
from cobl.lexicon.functions import nexus_comment
from cobl.lexicon.defaultModels import getDefaultWordlistId, \
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

    def post(self, request, pk, **kwargs):
        instance = CognateClassCitation.objects.get(id=pk)
        form = EditCognateClassCitationForm(request.POST, instance=instance)
        try:
            # validate {ref foo ...}
            s = Source.objects.all().filter(deprecated=False)
            pattern = re.compile(r'(\{ref +([^\{]+?)(:[^\{]+?)? *\})')
            for m in re.finditer(pattern, form.data['comment']):
                foundSet = s.filter(shorthand=m.group(2))
                if not foundSet.count() == 1:
                    raise ValidationError('In field “Comment” source shorthand “%(name)s” is unknown.', 
                                                params={'name': m.group(2)})
            form.save()
        except ValidationError as e:
            messages.error(
                request,
                'Sorry, the server had problems updating the cognate citation. %s' % e)
            return self.render_to_response({"form": form})
        return HttpResponseRedirect(reverse('cognate-class-citation-detail', args=[pk]))

    def get_context_data(self, **kwargs):
        context = super(
            CognateClassCitationUpdateView, self).get_context_data(**kwargs)
        cc_id = context["object"].cognate_class.id
        context["title"] = "New cognate class citation"
        context["heading"] = "Citation %s (referring to cognate class %s)" % (context["object"].id, cc_id)
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
        if len(NexusExport.objects.filter(_exportData=None).all()) > 0:
            form = None
        else:
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
                "calculateMatrix": 1,
                "excludeMarkedMeanings": 1,
                "excludeMarkedLanguages": 1}
            form = ChooseNexusOutputForm(defaults)
        return self.render_to_response({"form": form})

    def post(self, request):
        form = ChooseNexusOutputForm(request.POST)
        if form.is_valid():
            export = NexusExport(
                exportName=self.fileNameForForm(form),
                description=form.cleaned_data["description"])
            export.setSettings(form)
            export.bump(request)
            export.save()
            theId = export.id
            e = NexusExport.objects.get(id=theId)
            e.exportName = "Exp%04d_%s" % (theId, e.exportName)
            e.save()
            return HttpResponseRedirect('/nexus/export/')
        messages.error(request,"Please provide a short description.")
        return self.render_to_response({"form": form})

    def fileNameForForm(self, form):
        meanings = form.cleaned_data["meaning_list"].meanings
        languages = form.cleaned_data["language_list"].languages

        if form.cleaned_data["excludeMarkedMeanings"]:
            meanings = meanings.exclude(exclude=True)
        if form.cleaned_data["excludeMarkedLanguages"]:
            languages = languages.exclude(notInExport=True)

        return "%s_CoBL-IE_Lgs%03d_Mgs%03d.nex" % (
            time.strftime("%Y-%m-%d"),
            # settings.project_short_name,
            languages.count(),
            meanings.count())


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
    calculateMatrix :: bool
    excludeMarkedLanguages :: bool | missing in older settings
    excludeMarkedMeanings :: bool | missing in older settings
    Returns:
    {exportData :: str,
     exportBEAUti :: str,
     exportTableData :: str,
     exportMatrix :: str,
     cladeMemberships :: str,
     computeCalibrations :: str}
    '''
    start_time = time.time()
    dialect_full_name = dict(NEXUS_DIALECT_CHOICES)[dialect]

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

    matrix, cognate_class_names, assumptions, dataTable = construct_matrix(
        languages, meanings, **kwargs)

    # Export data to compose:
    exportData = []
    exportBEAUti = []
    exportTableData = []
    exportMatrix = []

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

    # get stats for each language for csv header data table
    langStats = {}
    for l in languages:
        langStats[l.id] = l.computeCounts(meaning_list, 'onlyexport')

    # write CSV header
    # add header Excess Synonyms
    exportTableData.append("\"Excess Synonyms\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [langStats[l.id]['excessCount'] for l in languages])))
    # add header Orphan Meanings
    exportTableData.append("\"Orphan Meanings\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [langStats[l.id]['orphansCount'] for l in languages])))
    # add header Loan Events
    exportTableData.append("\"Loan Events\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [langStats[l.id]['cogLoanCount'] for l in languages])))
    # add header Parallel Loans
    exportTableData.append("\"Parallel Loans\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [langStats[l.id]['cogParallelLoanCount'] for l in languages])))
    # add header Ideophonic
    exportTableData.append("\"Ideophonic\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [langStats[l.id]['cogIdeophonicCount'] for l in languages])))
    # add header Parallel Derivation
    exportTableData.append("\"Parallel Derivation\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [langStats[l.id]['cogPllDerivationCount'] for l in languages])))
    # add header Dubious
    exportTableData.append("\"Dubious\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [langStats[l.id]['cogDubSetCount'] for l in languages])))
    # add header language URL Names
    exportTableData.append("\"Language URL Name\",,,%s" % ",".join(
        map(lambda x : '\"%s\"' % x, language_names)))
    # add header language Display Names
    exportTableData.append("\"Language Display Name\",,,%s" % ",".join(
        map(lambda x : '\"%s\"' % x, [l.utf8_name for l in languages])))
    # add header language Cl 0
    exportTableData.append("\"Cl 0\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [l.level0 for l in languages])))
    # add header language Cl 1
    exportTableData.append("\"Cl 1\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [l.level1 for l in languages])))
    # add header language Cl 0 hex colour
    exportTableData.append("\"Language clade colour hex code\",,,%s" % ",".join(
        map(lambda x : '\"#%s\"' % x, [l.level0Color for l in languages])))
    # add header Historical
    exportTableData.append("\"Historical\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [int(l.historical) for l in languages])))
    # add header Fragmentary? - empty @TODO 
    exportTableData.append("\"Fragmentary?\",,,%s" % ",".join(
        map(lambda x : '%s' % x, [int(l.fragmentary) for l in languages])))

    # if kwargs['label_cognate_sets']:
    #     row = [" " * 9] + [
    #         str(i).ljust(10) for i in
    #         range(len(cognate_class_names))[10::10]]
    #     appendExports("   %s[ %s ]" % (" " * max_len, "".join(row)))
    #     row = ".".join([" " * 9] * (int((len(cognate_class_names) + 9) / 10)))
    #     appendExports("   %s[ %s ]" % (" " * max_len, row))

    # matrix comments requested in #314:
    matrixComments = getMatrixCommentsFromCognateNames(
        cognate_class_names, padding=max_len + 4)
    appendExports(matrixComments + "\n")

    # write exportTableData
    current_m = ""
    empty_line = "," * (len(language_names)+1)
    for row in sorted(dataTable):
        m, cc_cnt, cc, lexid = (row.split("___") + [''] * 4)[:4]
        if current_m != m:
            exportTableData.append(empty_line)
            exportTableData.append(empty_line)
            exportTableData.append(empty_line)
            exportTableData.append(empty_line)
            exportTableData.append(empty_line)
            exportTableData.append(empty_line)
        exportTableData.append("%s,%s,%s,%s" % (m, re.sub(r'[A-Z]', '', str(cc)), lexid, ",".join(map(lambda x : '%s' % x, dataTable[row]))))
        current_m = m

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

    if kwargs.get('calculateMatrix', True):
        # calculate data matrix
        if kwargs.get('excludeMarkedLanguages', True):
            allLgs = [l for l in language_list.languages.all() if not l.notInExport]
        else:
            allLgs = [l for l in language_list.languages.all()]
        seenLgs = {}
        cclCache ={}

        # write header
        line = []
        line.append('')
        line.extend(allLgs)
        # add header language URL Names
        exportMatrix.append("\"Language URL Name\",%s" % ",".join(
            map(lambda x : '\"%s\"' % x, language_names)))
        # add header language Display Names
        exportMatrix.append("\"Language Display Name\",%s" % ",".join(
            map(lambda x : '\"%s\"' % x, [l.utf8_name for l in languages])))
        # add header language Cl 0
        exportMatrix.append("\"Cl 0\",%s" % ",".join(
            map(lambda x : '%s' % x, [l.level0 for l in languages])))
        # add header language Cl 1
        exportMatrix.append("\"Cl 1\",%s" % ",".join(
            map(lambda x : '%s' % x, [l.level1 for l in languages])))
        # add header language Cl 0 hex colour
        exportMatrix.append("\"Language clade colour hex code\",%s" % ",".join(
            map(lambda x : '\"#%s\"' % x, [l.level0Color for l in languages])))
        # add header Historical
        exportMatrix.append("\"Historical\",%s" % ",".join(
            map(lambda x : '%s' % x, [int(l.historical) for l in languages])))
        # add header Fragmentary?
        exportMatrix.append("\"Fragmentary?\",%s" % ",".join(
            map(lambda x : '%s' % x, [int(l.fragmentary) for l in languages])))

        # calculate the distance matrix
        if kwargs.get('excludeMarkedMeanings', True):
            relevantLexemes = Lexeme.objects.filter(meaning__meaninglist=meaning_list,
                meaning__exclude=False
                ).select_related("meaning", "language"
                ).prefetch_related("cognate_class")
        else:
            relevantLexemes = Lexeme.objects.filter(meaning__meaninglist=meaning_list
                ).select_related("meaning", "language"
                ).prefetch_related("cognate_class")

        if kwargs.get('excludeNotSwadesh', True):
            relevantLexemes = relevantLexemes.filter(not_swadesh_term=False)

        for l1 in allLgs:
            line = []
            line.append(l1)
            for l2 in allLgs:
                if l1.id == l2.id:
                    line.append("100")
                    continue
                if "%s-%s" % (l2.id, l1.id) in seenLgs:
                    line.append(seenLgs["%s-%s" % (l2.id, l1.id)])
                    continue

                # collect data:
                mIdOrigLexDict = defaultdict(list)  # Meaning.id -> [Lexeme]
                for l in relevantLexemes.filter(language=l2):
                    mIdOrigLexDict[l.meaning_id].append(l)

                # init stats counter
                numOfMeaningsSharedCC = set()
                numOfMeanings = set()

                for l in relevantLexemes.filter(
                        language=l1,
                        meaning_id__in=mIdOrigLexDict):

                    if l.id in cclCache:
                        allcc = cclCache[l.id]
                    else:
                        allcc = l.allCognateClasses
                        if kwargs.get('excludePllDerivation', True):
                            allcc = allcc.filter(parallelDerivation=False)
                        if kwargs.get('excludeIdeophonic', True):
                            allcc = allcc.filter(ideophonic=False)
                        if kwargs.get('excludeDubious', True):
                            allcc = allcc.filter(dubiousSet=False)
                        if kwargs.get('excludeLoanword', True):
                            allcc = allcc.filter(loanword=False)
                        elif kwargs.get('excludePllLoan', True):
                            allcc = allcc.filter(parallelLoanEvent=False)
                        cclCache[l.id] = allcc

                    for cc in allcc:
                        for cc1 in mIdOrigLexDict[l.meaning.id]:
                            numOfMeanings.add(l.meaning_id)
                            if cc1 in cclCache:
                                allcc1 = cclCache[cc1]
                            else:
                                allcc1 = cc1.allCognateClasses
                                if kwargs.get('excludePllDerivation', True):
                                    allcc1 = allcc1.filter(parallelDerivation=False)
                                if kwargs.get('excludeIdeophonic', True):
                                    allcc1 = allcc1.filter(ideophonic=False)
                                if kwargs.get('excludeDubious', True):
                                    allcc1 = allcc1.filter(dubiousSet=False)
                                if kwargs.get('excludeLoanword', True):
                                    allcc1 = allcc1.filter(loanword=False)
                                elif kwargs.get('excludePllLoan', True):
                                    allcc1 = allcc1.filter(parallelLoanEvent=False)
                                cclCache[cc1] = allcc1
                            if cc in allcc1:
                                numOfMeaningsSharedCC.add(l.meaning_id)

                if len(numOfMeanings) != 0:
                    numOfSharedCCPerMeanings = "%.1f" % float(
                                                len(numOfMeaningsSharedCC)/len(numOfMeanings)*100)
                else:
                    numOfSharedCCPerMeanings = "0"

                line.append(numOfSharedCCPerMeanings)
                seenLgs["%s-%s" % (l1.id, l2.id)] = numOfSharedCCPerMeanings

            exportMatrix.append(",".join(str(x) for x in line))

    # timing
    seconds = int(time.time() - start_time)
    minutes = seconds // 60
    seconds %= 60
    appendExports("[ Processing time: %02d:%02d ]" % (minutes, seconds))

    # Return combined data:
    return {
        'exportData': "\n".join(exportData),      # Requested export
        'exportBEAUti': "\n".join(exportBEAUti),  # BEAUti specific export
        'exportTableData': "\n".join(exportTableData),  # exportTableData = matrix as CSV table
        'exportMatrix': "\n".join(exportMatrix),
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
        pass
    # synonymous cognate classes (i.e. cognate reflexes representing
    # a single Swadesh meaning)
    cognate_classes = defaultdict(list)
    for cc, meaning_id in wantedCJs.order_by(
        "lexeme__meaning",
        "cognate_class").values_list(
        "cognate_class__id",
            "lexeme__meaning__id").distinct():
        cognate_classes[meaning_id].append(cc)

    # Lexemes which shall be excluded:
    exclude_lexemes = set()  # :: set(lexeme.id)
    if excludeNotSwadesh:
        exclude_lexemes |= set(Lexeme.objects.filter(
            not_swadesh_term=True).values_list("id", flat=True))

    # languages having a reflex for a cognate set
    '''
        data :: meaning.gloss -> cognate_classes[meaning.id] -> [language]
        '''
    data = dict()
    pllloan_lexemes = []
    lex_order_due_lgs = [x.id for x in languages]
    for meaning in meanings: #@TODO speed optimation
        cj_for_current_meaning = CognateJudgement.objects.filter(lexeme__meaning_id=meaning.id)
        plls = []
        for cc in cognate_classes[meaning.id]:
            matches = [
                cj.lexeme.language.id for cj in
                cj_for_current_meaning.filter(cognate_class=cc) if cj.lexeme.language in
                languages and cj.lexeme.id not in exclude_lexemes]
            if matches:
                data.setdefault(meaning.id, dict())[cc] = matches
                if includePllLoan:
                    r_cc = CognateClass.objects.get(id=cc)
                    if r_cc.parallelLoanEvent:
                        cjs = []
                        for cj in cj_for_current_meaning.filter(cognate_class=cc):
                            if cj.lexeme.language in languages and cj.lexeme.id not in exclude_lexemes:
                                cjs.append((cj.lexeme.language.id, cj))
                        l_cnt = 25
                        # sort lexemes according language list order
                        for cj in sorted(cjs, key = lambda x: lex_order_due_lgs.index(x[0])):
                            pllloan_lexemes.append(cj[1].lexeme.id)
                            data[meaning.id].setdefault(
                                ("Z", "%s%s" % (cc, ascii_uppercase[l_cnt]), cj[1].lexeme.id) , list()).append(cj[1].lexeme.language.id)
                            l_cnt -= 1

    # adds a cc code for all singletons
    # (lexemes which are not registered as
    # belonging to a cognate class), and add to cognate_class_dict
    for lexeme in Lexeme.objects.filter(
            language__in=languages,
            meaning__in=meanings,
            cognate_class__isnull=True):
        if lexeme.id not in exclude_lexemes and lexeme.id not in pllloan_lexemes:
            cc = ("U", lexeme.id)  # use tuple for sorting
            data[lexeme.meaning.id].setdefault(
                cc, list()).append(lexeme.language.id)

    def cognate_class_name_formatter(cc, gloss):
        # gloss = cognate_class_dict[cc]
        if isinstance(cc, int):
            return "%s_cognate_%s" % (gloss, cc)
        if isinstance(cc, (list, tuple)):
            if len(cc) == 2:
                return "%s_lexeme_%s" % (gloss, cc[1])
            elif len(cc) == 3:
                return "%s_cognate_%s_pllloanlexeme_%s" % (gloss, cc[1], cc[2])
        return "%s_ERROR_%s" % (gloss, str(cc))

    def get_cognate_class_id_for_dataTable(cnt, cc):
        # is used for the later sorting of dict keys and preserving
        # the order of passed cognate set IDs
        if isinstance(cc, int):
            return "%s___%s" % (str(cnt).zfill(3), str(cc))
        if isinstance(cc, (list, tuple)):
            if len(cc) == 2:
                return "%s___%s" % (str(cnt).zfill(3), str(cc[1]))
            elif len(cc) == 3:
                return "%s___%s___%s" % (str(cnt).zfill(3), str(cc[1]), str(cc[2]))
        return "000___0"

    # make matrix
    matrix, cognate_class_names, assumptions = list(), list(), list()
    make_header = True
    col_num = 0
    dataTableDict = defaultdict(list)

    # get for all languages the clade ids for sorting cognate classes
    allInvolvedClades = Clade.objects.filter(
                languageclade__language__id__in=languages).exclude(
                hexColor='').exclude(shortName='').values_list('id', 'languageclade__language__id')
    languageClades = {}
    for clade_id, lg_id in allInvolvedClades:
        languageClades[lg_id]=clade_id

    for language in languages:
        row = [language.ascii_name]
        if excludeNotSwadesh:
            meaningIDsForLanguage = set(language.lexeme_set.filter(not_swadesh_term=False).values_list('meaning_id', flat=True))
        else:
            meaningIDsForLanguage = set(language.lexeme_set.values_list('meaning_id', flat=True))
        for meaning in meanings:
            is_lg_missing_mng = not meaning.id in meaningIDsForLanguage
            if ascertainment_marker:
                if is_lg_missing_mng:
                    row.append("?")
                else:
                    row.append("0")
                if make_header:
                    col_num += 1
                    start_range = col_num
                    cognate_class_names.append("%s_group" % meaning.gloss)

            if meaning.id in data:
                cnt = 0 # needed for preserving the cc order after sorting meaning keys in dict
                data_mng_id = data[meaning.id]

                # generate sort order for cognate class ids = order by (cladeCount, lexCount)
                cc_sortorder = {}
                for cc0 in data_mng_id.keys():
                    cc = cc0
                    if isinstance(cc0, (list, tuple)):
                        cc = str(cc0[1]).zfill(6)
                    lexCount = len(data_mng_id[cc0])
                    if lexCount == 1 :
                        cc_sortorder["%04d_%06d_%s" % (1, 1, cc)] = cc0
                    else:
                        clds = set()
                        for l in data_mng_id[cc0]:
                            if l in languageClades:
                                clds.add(languageClades[l])
                        cc_sortorder["%04d_%06d_%s" % (len(clds), lexCount, cc)] = cc0

                for cc0 in sorted(cc_sortorder, reverse=True):
                    cc = cc_sortorder[cc0]
                    if make_header and ascertainment_marker:
                        col_num += 1
                        cognate_class_names.append(
                            cognate_class_name_formatter(cc, meaning.gloss))
                    if is_lg_missing_mng:
                        row.append("?")
                        dataTableDict["%s___%s" % (meaning.gloss, get_cognate_class_id_for_dataTable(cnt, cc))].append("?")
                    elif language.id in data_mng_id[cc]:
                        row.append("1")
                        dataTableDict["%s___%s" % (meaning.gloss, get_cognate_class_id_for_dataTable(cnt, cc))].append("1")
                    else:
                        row.append("0")
                        dataTableDict["%s___%s" % (meaning.gloss, get_cognate_class_id_for_dataTable(cnt, cc))].append("0")
                    cnt += 1
            if ascertainment_marker and make_header:
                end_range = col_num
                assumptions.append(
                    "charset %s = %s-%s;" %
                    (meaning.gloss, start_range, end_range))

        matrix.append(row)
        make_header = False

    return matrix, list(map(lambda x: re.sub(r'[A-Z]', '', x), cognate_class_names)), assumptions, dataTableDict


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
            str(cj.cognate_class.id),
            cj.lexeme.language.ascii_name,
            str(cj.lexeme.phon_form.strip() or
                cj.lexeme.romanised.strip()),
            str(cj.lexeme.id),
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
            str(lexeme.id),
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
    pllloanRegex = r'^(.+)_cognate_(.+?)_pllloanlexeme_(.+)$'

    for name in cognate_class_names:
        groupMatch = re.match(groupRegex, name)
        if groupMatch:
            meaning, meaningLength = nextMeaning(groupMatch.group(1))
            flagRow += ' '
            idBucket.append('|')
            continue
        pllloanMatch = re.match(pllloanRegex, name)
        if pllloanMatch:
            meaning, meaningLength = nextMeaning(pllloanMatch.group(1))
            flagRow += 'P'
            idBucket.append("%s|%s" % (pllloanMatch.group(2), pllloanMatch.group(3)))
            continue
        lexemeMatch = re.match(lexemeRegex, name)
        if lexemeMatch:
            meaning, meaningLength = nextMeaning(lexemeMatch.group(1))
            flagRow += 'L'
            idBucket.append("%s|" % (lexemeMatch.group(2)))
            continue
        cognateMatch = re.match(cognateRegex, name)
        if cognateMatch:
            meaning, meaningLength = nextMeaning(cognateMatch.group(1))
            flagRow += 'C'
            idBucket.append("%s|" % (cognateMatch.group(2)))
            continue
        # Nothing matches:
        meaning, meaningLength = nextMeaning('')
        flagRow += '?'
        idBucket.append('')
    nextMeaning('')  # Append last meaning to meaningRow

    # Create idRows by padding and transposing ids:
    idMaxLenCC = max(*[len(i.split('|')[0]) for i in idBucket])
    idMaxLenLEX = max(*[len(i.split('|')[1]) for i in idBucket])
    idRows = []
    for id in idBucket:
        (ccid, lexid) = id.split('|')
        idRows.append([x for x in "%s|%s" % (ccid.rjust(idMaxLenCC, '-'), lexid.ljust(idMaxLenLEX, '-'))])
    idRows = [''.join(row) for row in zip(*idRows)]

    commentRows = []

    def addComment(c):
        commentRows.append(" " * (padding - 1) + "[ %s ]" % c)

    # add nexus set ids on top of the comment
    nex_ccs = []
    max_len = len(str(len(cognate_class_names)))
    for n in range(1, len(cognate_class_names) + 1):
        nex_ccs.append(str(n).rjust(max_len, '-'))
    for r in [''.join(row) for row in zip(*nex_ccs)]:
        addComment(r)

    addComment(''.join(meaningRow))
    commentRows.append("")
    addComment(flagRow)
    commentRows.append("")
    for idRow in idRows:
        addComment(idRow)

    return '\n'.join(commentRows)
