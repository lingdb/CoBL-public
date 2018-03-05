# -*- coding: utf-8 -*-
import csv
import copy
import datetime
import logging
import io
import json
import re
import time
import zipfile
import codecs
from collections import defaultdict, deque, OrderedDict
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction, connection
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.forms import ValidationError
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, \
     Http404, QueryDict
from django.shortcuts import redirect, render, render_to_response
from django.template import RequestContext
from django.template import Template
from django.db.models.query_utils import DeferredAttribute
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_protect
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from reversion.models import Revision, Version
from ielex.settings import LIMIT_TO, META_TAGS
from ielex.forms import AddCitationForm, \
    AddCogClassTableForm, \
    AddLanguageListForm, \
    AddLanguageListTableForm, \
    AddMeaningListForm, \
    AddLexemeForm, \
    AuthorCreationForm, \
    AuthorDeletionForm, \
    AuthorTableForm, \
    AuthorRowForm, \
    ChooseCognateClassForm, \
    CladeCreationForm, \
    CladeDeletionForm, \
    CladeTableForm, \
    CloneLanguageForm, \
    CognateJudgementSplitTable, \
    EditCitationForm, \
    AddLanguageForm, \
    EditLanguageListForm, \
    EditLanguageListMembersForm, \
    EditLexemeForm, \
    EditMeaningForm, \
    EditMeaningListForm, \
    EditMeaningListMembersForm, \
    EditSourceForm, \
    LanguageListProgressForm, \
    EditSingleLanguageForm, \
    LexemeTableEditCognateClassesForm, \
    LexemeTableLanguageWordlistForm, \
    LexemeTableViewMeaningsForm, \
    MeaningListTableForm, \
    MergeCognateClassesForm, \
    SearchLexemeForm, \
    SndCompCreationForm, \
    SndCompDeletionForm, \
    SndCompTableForm, \
    make_reorder_languagelist_form, \
    make_reorder_meaninglist_form, \
    AddMissingLexemsForLanguageForm, \
    RemoveEmptyLexemsForLanguageForm, \
    CognateClassEditForm, \
    SourceDetailsForm, \
    SourceEditForm, \
    UploadBiBTeXFileForm, \
    CognateJudgementFormSet, \
    CognateClassFormSet, \
    LexemeFormSet, \
    AssignCognateClassesFromLexemeForm, \
    LanguageDistributionTableForm, \
    TwoLanguageWordlistTableForm
from ielex.lexicon.models import Author, \
    Clade, \
    CognateClass, \
    CognateClassCitation, \
    CognateJudgement, \
    CognateJudgementCitation, \
    Language, \
    LanguageClade, \
    LanguageList, \
    LanguageListOrder, \
    Lexeme, \
    LexemeCitation, \
    Meaning, \
    MeaningList, \
    SndComp, \
    Source, \
    NexusExport, \
    MeaningListOrder, \
    RomanisedSymbol
from ielex.lexicon.defaultModels import getDefaultLanguage, \
    getDefaultLanguageId, \
    getDefaultLanguagelist, \
    getDefaultLanguagelistId, \
    getDefaultMeaning, \
    getDefaultMeaningId, \
    getDefaultWordlist, \
    getDefaultWordlistId, \
    getDefaultSourceLanguage, \
    setDefaultLanguage, \
    setDefaultLanguageId, \
    setDefaultLanguagelist, \
    setDefaultMeaning, \
    setDefaultMeaningId, \
    setDefaultWordlist, \
    setDefaultSourceLanguage
from ielex.shortcuts import render_template
from ielex.utilities import next_alias, \
    anchored, oneline, logExceptions, fetchMarkdown
from ielex.languageCladeLogic import updateLanguageCladeRelations
from ielex.tables import SourcesTable, SourcesUpdateTable
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from django_tables2 import RequestConfig
from dal import autocomplete


# -- Database input, output and maintenance functions ------------------------


@logExceptions
def view_changes(request, username=None, revision_id=None, object_id=None):
    """Recent changes"""
    boring_models = [LanguageListOrder, LanguageList, MeaningList]
    boring_model_ids = [ContentType.objects.get_for_model(m).id for m in
                        boring_models]

    def interesting_versions(self):
        return self.version_set.exclude(content_type_id__in=boring_model_ids)
    Revision.add_to_class("interesting_versions", interesting_versions)

    if not username:
        recent_changes = Revision.objects.all().order_by("-id")
    else:
        recent_changes = Revision.objects.filter(
            user__username=username).order_by("-id")
    paginator = Paginator(recent_changes, 50)

    try:  # Make sure page request is an int. If not, deliver first page.
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:  # If page request is out of range, deliver last page of results.
        changes = paginator.page(page)
    except (EmptyPage, InvalidPage):
        changes = paginator.page(paginator.num_pages)

    userIds = set(Revision.objects.values_list("user", flat=True).distinct())
    contributors = sorted([(User.objects.get(id=user_id),
                            Revision.objects.filter(user=user_id).count())
                           for user_id in userIds
                           if user_id is not None],
                          key=lambda x: -x[1])

    return render_template(request, "view_changes.html",
                           {"changes": changes,
                            "contributors": contributors})


@login_required
@logExceptions
def revert_version(request, revision_id):
    """Roll back the object saved in a Version to the previous Version"""
    referer = request.META.get("HTTP_REFERER", "/")
    revision_obj = Revision.objects.get(pk=revision_id)
    revision_obj.revert()  # revert all associated objects too
    msg = "Rolled back revision %s" % (revision_obj.id)
    messages.info(request, msg)
    return HttpResponseRedirect(referer)


@logExceptions
def view_object_history(request, version_id):
    version = Version.objects.get(pk=version_id)
    obj = version.content_type.get_object_for_this_type(id=version.object_id)
    fields = [field.name for field in obj._meta.fields]
    versions = [[v.field_dict[f] for f in fields] + [v.id] for v in
                Version.objects.get_for_object(obj).order_by(
                    "revision__date_created")]
    return render_template(request, "view_object_history.html",
                           {"object": obj,
                            "versions": versions,
                            "fields": fields})


# -- General purpose queries and functions -----------------------------------

@logExceptions
def get_canonical_meaning(meaning):
    """Identify meaning from id number or partial name"""
    try:
        if meaning.isdigit():
            meaning = Meaning.objects.get(id=meaning)
        else:
            meaning = Meaning.objects.get(gloss=meaning)
    except Meaning.DoesNotExist:
        raise Http404("Meaning '%s' does not exist" % meaning)
    return meaning


@logExceptions
def get_canonical_language(language, request=None):
    """Identify language from id number or partial name"""
    if not language:
        raise Language.DoesNotExist
    if language.isdigit():
        language = Language.objects.get(id=language)
    else:
        try:
            language = Language.objects.get(ascii_name=language)
        except Language.DoesNotExist:
            try:
                language = Language.objects.get(
                    ascii_name__istartswith=language)
            except Language.MultipleObjectsReturned:
                if request:
                    messages.info(
                        request,
                        "There are multiple languages matching"
                        " '%s' in the database" % language)
                raise Http404
            except Language.DoesNotExist:
                if request:
                    messages.info(
                        request,
                        "There is no language named or starting"
                        " with '%s' in the database" % language)
                raise Http404
    return language


@logExceptions
def get_prev_and_next_languages(request, current_language, language_list=None):
    if language_list is None:
        language_list = LanguageList.objects.get(
            name=getDefaultLanguagelist(request))
    elif isinstance(language_list, str):
        language_list = LanguageList.objects.get(name=language_list)

    ids = list(language_list.languages.exclude(
        level0=0).values_list("id", flat=True))

    try:
        current_idx = ids.index(current_language.id)
    except ValueError:
        current_idx = 0
    try:
        prev_language = Language.objects.get(id=ids[current_idx - 1])
    except IndexError:
        try:
            prev_language = Language.objects.get(id=ids[len(ids) - 1])
        except IndexError:
            prev_language = current_language
    try:
        next_language = Language.objects.get(id=ids[current_idx + 1])
    except IndexError:
        try:
            next_language = Language.objects.get(id=ids[0])
        except IndexError:
            next_language = current_language
    return (prev_language, next_language)


@logExceptions
def get_prev_and_next_meanings(request, current_meaning, meaning_list=None):
    if meaning_list is None:
        meaning_list = MeaningList.objects.get(
            name=getDefaultWordlist(request))
    elif isinstance(meaning_list, str):
        meaning_list = MeaningList.objects.get(name=meaning_list)
    meanings = list(meaning_list.meanings.all().order_by("meaninglistorder"))

    ids = [m.id for m in meanings]
    try:
        current_idx = ids.index(current_meaning.id)
    except ValueError:
        current_idx = 0
    try:
        prev_meaning = meanings[current_idx - 1]
    except IndexError:
        prev_meaning = meanings[len(meanings) - 1]
    try:
        next_meaning = meanings[current_idx + 1]
    except IndexError:
        next_meaning = meanings[0]
    return (prev_meaning, next_meaning)


@logExceptions
def get_prev_and_next_lexemes(request, current_lexeme):
    """Get the previous and next lexeme from the same language, ordered
    by meaning and then alphabetically by form"""
    lexemes = list(Lexeme.objects.filter(
        language=current_lexeme.language).order_by(
            "meaning", "phon_form", "romanised", "id"))
    ids = [l.id for l in lexemes]
    try:
        current_idx = ids.index(current_lexeme.id)
    except ValueError:
        current_idx = 0
    prev_lexeme = lexemes[current_idx - 1]
    try:
        next_lexeme = lexemes[current_idx + 1]
    except IndexError:
        next_lexeme = lexemes[0]
    return (prev_lexeme, next_lexeme)


@logExceptions
def update_object_from_form(model_object, form):
    """Update an object with data from a form."""
    assert set(form.cleaned_data).issubset(set(model_object.__dict__))
    model_object.__dict__.update(form.cleaned_data)
    model_object.save()

# -- /language(s)/ ----------------------------------------------------------


@logExceptions
def get_canonical_language_list(language_list=None, request=None):
    """Returns a LanguageList object"""
    try:
        if language_list is None:
            language_list = LanguageList.objects.get(name=LanguageList.DEFAULT)
        elif language_list.isdigit():
            language_list = LanguageList.objects.get(id=language_list)
        else:
            language_list = LanguageList.objects.get(name=language_list)
    except LanguageList.DoesNotExist:
        if request:
            messages.info(
                request,
                "There is no language list matching"
                " '%s' in the database" % language_list)
        raise Http404
    return language_list


@logExceptions
def get_canonical_meaning_list(meaning_list=None, request=None):
    """Returns a MeaningList object"""
    try:
        if meaning_list is None:
            meaning_list = MeaningList.objects.get(name=MeaningList.DEFAULT)
        elif meaning_list.isdigit():
            meaning_list = MeaningList.objects.get(id=meaning_list)
        else:
            meaning_list = MeaningList.objects.get(name=meaning_list)
    except MeaningList.DoesNotExist:
        if request:
            messages.info(
                request,
                "There is no meaning list matching"
                " '%s' in the database" % meaning_list)
        raise Http404
    return meaning_list


@csrf_protect
@logExceptions
def view_language_list(request, language_list=None):
    current_list = get_canonical_language_list(language_list, request)
    setDefaultLanguagelist(request, current_list.name)
    languages = current_list.languages.all().prefetch_related(
        "lexeme_set", "lexeme_set__meaning",
        "languageclade_set", "clades")

    if (request.method == 'POST') and ('langlist_form' in request.POST):
        languageListTableForm = AddLanguageListTableForm(request.POST)
        try:
            languageListTableForm.validate()
        except Exception as e:
            logging.exception(
                'Exception in POST validation for view_language_list')
            messages.error(request, 'Sorry, the form data sent '
                           'did not pass server side validation: %s' % e)
            return HttpResponseRedirect(
                reverse("view-language-list", args=[current_list.name]))
        # Updating languages and gathering clades to update:
        updateClades = languageListTableForm.handle(request)
        # Updating clade relations for changes languages:
        if updateClades:
            updateLanguageCladeRelations(languages=updateClades)
        # Redirecting so that UA makes a GET.
        return HttpResponseRedirect(
            reverse("view-language-list", args=[current_list.name]))
    elif (request.method == 'POST') and ('cloneLanguage' in request.POST):
        # Cloning language and lexemes:
        form = CloneLanguageForm(request.POST)
        try:
            form.validate()
            form.handle(request, current_list)
            # Redirect to newly created language:
            messages.success(request, 'Language cloned.')
            return HttpResponseRedirect(
                reverse("view-language-list", args=[current_list.name]))
        except Exception as e:
            logging.exception('Problem cloning Language in view_language_list')
            messages.error(request, 'Sorry, a problem occured '
                           'when cloning the language: %s' % e)
            return HttpResponseRedirect(
                reverse("view-language-list", args=[current_list.name]))
    elif (request.method == 'GET') and ('exportCsv' in request.GET):
        # Handle csv export iff desired:
        return exportLanguageListCsv(request, languages)

    meaningList = MeaningList.objects.get(name=getDefaultWordlist(request))
    languages_editabletable_form = AddLanguageListTableForm()
    exportMethod = ''
    if request.method == 'GET':
        if 'onlyexport' in request.path.split('/'):
            exportMethod = 'onlyexport'
        elif 'onlynotexport' in request.path.split('/'):
            exportMethod = 'onlynotexport'
    for lang in languages:
        lang.idField = lang.id
        lang.computeCounts(meaningList, exportMethod)
        languages_editabletable_form.langlist.append_entry(lang)

    otherLanguageLists = LanguageList.objects.exclude(name=current_list).all()

    return render_template(request, "language_list.html",
                           {"languages": languages,
                            'lang_ed_form': languages_editabletable_form,
                            "current_list": current_list,
                            "otherLanguageLists": otherLanguageLists,
                            "wordlist": getDefaultWordlist(request),
                            "clades": Clade.objects.all()})


@csrf_protect
@logExceptions
def exportLanguageListCsv(request, languages=[]):
    """
      @param languages :: [Language]
    """
    fields = request.GET['exportCsv'].split(',')
    rows = [l.getCsvRow(*fields) for l in languages]
    rows.insert(0, ['"' + f + '"' for f in fields])  # Add headline
    # Composing .csv data:
    data = '\n'.join([','.join(row) for row in rows])
    # Filename:
    filename = "%s.%s.csv" % \
        (datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d'),
         getDefaultLanguagelist(request))
    # Answering request:
    response = HttpResponse(data)
    response['Content-Disposition'] = ('attachment;filename="%s"' % filename)
    response['Control-Type'] = 'text/csv; charset=utf-8'
    response['Pragma'] = 'public'
    response['Expires'] = 0
    response['Cache-Control'] = 'must-revalidate, post-check=0, pre-check=0'
    return response


@csrf_protect
@logExceptions
def view_clades(request):
    if request.method == 'POST':
        # Updating existing clades:
        if 'clades' in request.POST:
            cladeTableForm = CladeTableForm(request.POST)
            # Flag to see if a clade changed:
            cladeChanged = False
            # Updating individual clades:
            try:
                cladeTableForm.validate()
                cladeChanged = cladeTableForm.handle(request)
            except Exception as e:
                logging.exception('Problem updating clades in view_clades.')
                messages.error(request, 'Sorry, the server had problems '
                               'updating at least on clade: %s' % e)
            # Updating language clade relations for changed clades:
            if cladeChanged:
                updateLanguageCladeRelations()
        # Adding a new clade:
        elif 'addClade' in request.POST:
            cladeCreationForm = CladeCreationForm(request.POST)
            try:
                cladeCreationForm.validate()
                newClade = Clade(**cladeCreationForm.data)
                with transaction.atomic():
                    newClade.save(force_insert=True)
            except Exception as e:
                logging.exception('Problem creating clade in view_clades.')
                messages.error(request, 'Sorry, the server had problems '
                               'creating the clade: %s' % e)
        # Deleting an existing clade:
        elif 'deleteClade' in request.POST:
            cladeDeletionForm = CladeDeletionForm(request.POST)
            try:
                cladeDeletionForm.validate()
                with transaction.atomic():
                    # Making sure the clade exists:
                    clade = Clade.objects.get(**cladeDeletionForm.data)
                    # Make sure to update things referencing clade here!
                    # Deleting the clade:
                    Clade.objects.filter(id=clade.id).delete()
                    # Write message about clade deletion:
                    messages.success(request, 'Deleted clade "%s".' %
                                     clade.cladeName)
            except Exception as e:
                logging.exception('Problem deleting clade in view_clades.')
                messages.error(request, 'Sorry, the server had problems '
                               'deleting the clade: %s' % e)
        return HttpResponseRedirect('/clades/')

    # Extra handling for graphs. See #145.
    if request.method == 'GET':
        if 'plot' in request.GET:
            return render_template(request, "distributionPlot.html")

    form = CladeTableForm()
    for clade in Clade.objects.all():
        clade.idField = clade.id
        form.elements.append_entry(clade)

    return render_template(request,
                           "clades.html",
                           {'clades': form})


@csrf_protect
@logExceptions
def view_sndComp(request):
    if request.method == 'POST':
        if 'sndComps' in request.POST:
            form = SndCompTableForm(request.POST)
            for entry in form.elements:
                data = entry.data
                try:
                    with transaction.atomic():
                        sndComp = SndComp.objects.get(id=data['idField'])
                        if sndComp.isChanged(**data):
                            try:
                                problem = sndComp.setDelta(**data)
                                if problem is None:
                                    sndComp.save()
                                else:
                                    messages.error(
                                        request,
                                        sndComp.deltaReport(**problem))
                            except Exception:
                                logging.exception('Exception while saving '
                                                  'POST in view_sndComp.')
                                messages.error(request, 'The server had '
                                               'problems saving the change '
                                               'to "%s".' % sndComp.lgSetName)
                except Exception as e:
                    logging.exception('Exception while accessing '
                                      'entry in view_sndComp.',
                                      extra=data)
                    messages.error(request, 'Sorry, the server had problems '
                                   'saving at least one SndComp entry: %s' % e)
        # Adding a new SndComp:
        elif 'addSndComp' in request.POST:
            sndCompCreationForm = SndCompCreationForm(request.POST)
            try:
                sndCompCreationForm.validate()
                newSndComp = SndComp(**sndCompCreationForm.data)
                with transaction.atomic():
                    newSndComp.save(force_insert=True)
            except Exception as e:
                logging.exception('Problem creating entry in view_sndComp.')
                messages.error(request, 'Sorry, the server had problems '
                               'creating the SndComp language set: %s' % e)
        # Deleting an existing SndComp:
        elif 'deleteSndComp' in request.POST:
            sndCompDeletionForm = SndCompDeletionForm(request.POST)
            try:
                sndCompDeletionForm.validate()
                with transaction.atomic():
                    # Making sure the SndComp exists:
                    sndComp = SndComp.objects.get(**sndCompDeletionForm.data)
                    # Make sure to update things referencing SndCom here!
                    # Deleting the SndComp:
                    SndComp.objects.filter(id=sndComp.id).delete()
                    # Write message about SndComp deletion:
                    messages.success(request,
                                     'Deleted set "%s"' % sndComp.lgSetName)
            except Exception as e:
                logging.exception('Problem deleting entry in view_sndComp.')
                messages.error(request, 'Sorry, the server had problems '
                               'deleting the SndComp language set: %s' % e)

    form = SndCompTableForm()

    sndComps = SndComp.objects.order_by(
        "lv0", "lv1", "lv2", "lv3").all()

    for s in sndComps:
        s.idField = s.id

        c = s.getClade()
        if c is not None:
            s.cladeName = c.cladeName

        form.elements.append_entry(s)

    return render_template(request,
                           "sndComp.html",
                           {'sndComps': form})


@logExceptions
def reorder_language_list(request, language_list):
    language_id = getDefaultLanguageId(request)
    language_list = LanguageList.objects.get(name=language_list)
    languages = language_list.languages.all().order_by("languagelistorder")
    ReorderForm = make_reorder_languagelist_form(languages)
    if request.method == "POST":
        form = ReorderForm(request.POST, initial={"language": language_id})
        if form.is_valid():
            language_id = int(form.cleaned_data["language"])
            setDefaultLanguageId(request, language_id)
            language = Language.objects.get(id=language_id)
            if form.data["submit"] == "Finish":
                language_list.sequentialize()
                return HttpResponseRedirect(
                    reverse("view-language-list", args=[language_list.name]))
            else:
                if form.data["submit"] == "Move up":
                    move_language(language, language_list, -1)
                elif form.data["submit"] == "Move down":
                    move_language(language, language_list, 1)
                else:
                    assert False, "This shouldn't be able to happen"
                return HttpResponseRedirect(
                    reverse("reorder-language-list",
                            args=[language_list.name]))
        else:  # pressed Finish without submitting changes
            return HttpResponseRedirect(
                reverse("view-language-list",
                        args=[language_list.name]))
    else:  # first visit
        form = ReorderForm(initial={"language": language_id})
    return render_template(
        request, "reorder_language_list.html",
        {"language_list": language_list, "form": form})


@logExceptions
def reorder_meaning_list(request, meaning_list):
    meaning_id = getDefaultLanguageId(request)
    meaning_list = MeaningList.objects.get(name=meaning_list)
    meanings = meaning_list.meanings.all().order_by("meaninglistorder")
    ReorderForm = make_reorder_meaninglist_form(meanings)
    if request.method == "POST":
        form = ReorderForm(request.POST, initial={"meaning": meaning_id})
        if form.is_valid():
            meaning_id = int(form.cleaned_data["meaning"])
            setDefaultMeaningId(request, meaning_id)
            meaning = Meaning.objects.get(id=meaning_id)
            if form.data["submit"] == "Finish":
                meaning_list.sequentialize()
                return HttpResponseRedirect(
                    reverse("view-wordlist", args=[meaning_list.name]))
            else:
                if form.data["submit"] == "Move up":
                    move_meaning(meaning, meaning_list, -1)
                elif form.data["submit"] == "Move down":
                    move_meaning(meaning, meaning_list, 1)
                else:
                    assert False, "This shouldn't be able to happen"
                return HttpResponseRedirect(
                    reverse("reorder-meaning-list",
                            args=[meaning_list.name]))
        else:  # pressed Finish without submitting changes
            return HttpResponseRedirect(
                reverse("view-wordlist",
                        args=[meaning_list.name]))
    else:  # first visit
        form = ReorderForm(initial={"meaning": meaning_id})
    return render_template(
        request, "reorder_meaning_list.html",
        {"meaning_list": meaning_list, "form": form})


@logExceptions
def move_language(language, language_list, direction):
    assert direction in (-1, 1)
    languages = list(language_list.languages.order_by("languagelistorder"))
    index = languages.index(language)
    if index == 0 and direction == -1:
        language_list.remove(language)
        language_list.append(language)
    else:
        try:
            neighbour = languages[index + direction]
            language_list.swap(language, neighbour)
        except IndexError:
            language_list.insert(0, language)


@logExceptions
def move_meaning(meaning, meaning_list, direction):
    assert direction in (-1, 1)
    meanings = list(meaning_list.meanings.order_by("meaninglistorder"))
    index = meanings.index(meaning)
    if index == 0 and direction == -1:
        meaning_list.remove(meaning)
        meaning_list.append(meaning)
    else:
        try:
            neighbour = meanings[index + direction]
            meaning_list.swap(meaning, neighbour)
        except IndexError:
            meaning_list.insert(0, meaning)


@csrf_protect
@logExceptions
def view_language_wordlist(request, language, wordlist):
    setDefaultLanguage(request, language)
    setDefaultWordlist(request, wordlist)
    try:
        wordlist = MeaningList.objects.get(name=wordlist)
    except MeaningList.DoesNotExist:
        raise Http404("MeaningList '%s' does not exist" % wordlist)

    # clean language name
    try:
        language = Language.objects.get(ascii_name=language)
    except Language.DoesNotExist:
        language = get_canonical_language(language, request)
        return HttpResponseRedirect(
            reverse("view-language-wordlist",
                    args=[language.ascii_name, wordlist.name]))

    if request.method == 'POST':
        # Updating lexeme table data:
        if 'lex_form' in request.POST:
            try:
                form = LexemeTableLanguageWordlistForm(request.POST)
                form.validate()
                form.handle(request)
            except Exception as e:
                logging.exception('Problem updating lexemes '
                                  'in view_language_wordlist.')
                messages.error(request, 'Sorry, the server had problems '
                               'updating at least one lexeme: %s' % e)
        elif 'editCognateClass' in request.POST:
            try:
                form = LexemeTableEditCognateClassesForm(request.POST)
                form.validate()
                form.handle(request)
            except Exception:
                logging.exception('Problem handling editCognateClass.')
        elif 'addMissingLexemes' in request.POST:
            try:
                form = AddMissingLexemsForLanguageForm(request.POST)
                form.validate()
                form.handle(request)
            except Exception as e:
                logging.exception(
                    'Problem with AddMissingLexemsForLanguageForm '
                    'in view_language_wordlist')
                messages.error(request, 'Sorry, the server had problems '
                                        'adding missing lexemes: %s' % e)
        elif 'removeEmptyLexemes' in request.POST:
            try:
                form = RemoveEmptyLexemsForLanguageForm(request.POST)
                form.validate()
                form.handle(request)
            except Exception as e:
                logging.exception(
                    'Problem with RemoveEmptyLexemsForLanguageForm '
                    'in view_language_wordlist')
                messages.error(request, 'Sorry, the server had problems '
                                        'removing empty lexemes: %s' % e)

        return HttpResponseRedirect(
            reverse("view-language-wordlist",
                    args=[language.ascii_name, wordlist.name]))

    # collect data
    lexemes = Lexeme.objects.filter(
        language=language,
        meaning__in=wordlist.meanings.all()
        ).select_related(
            "meaning", "language").order_by(
                "meaning__gloss").prefetch_related(
                    "cognatejudgement_set",
                    "cognatejudgement_set__cognatejudgementcitation_set",
                    "cognate_class",
                    "lexemecitation_set")

    # Used for #219:
    cIdCognateClassMap = {}  # :: CognateClass.id -> CognateClass

    notTargetCountPerMeaning = {}
    for lex in lexemes:
        if lex.meaning in notTargetCountPerMeaning:
            if lex.not_swadesh_term:
                notTargetCountPerMeaning[lex.meaning] += 1
        else:
            if lex.not_swadesh_term:
                notTargetCountPerMeaning[lex.meaning] = 1
            else:
                notTargetCountPerMeaning[lex.meaning] = 0

    lexemes_editabletable_form = LexemeTableLanguageWordlistForm()
    for lex in lexemes:
        lex.notTargetCountPerMeaning = notTargetCountPerMeaning[lex.meaning]
        lexemes_editabletable_form.lexemes.append_entry(lex)
        ccs = lex.cognate_class.all()
        for cc in ccs:
            cIdCognateClassMap[cc.id] = cc

    otherMeaningLists = MeaningList.objects.exclude(id=wordlist.id).all()

    languageList = LanguageList.objects.prefetch_related('languages').get(
        name=getDefaultLanguagelist(request))
    typeahead = json.dumps({
        l.utf8_name: reverse(
            "view-language-wordlist", args=[l.ascii_name, wordlist.name])
        for l in languageList.languages.all()})

    prev_language, next_language = \
        get_prev_and_next_languages(request, language,
                                    language_list=languageList)
    cognateClasses = json.dumps([{'id': c.id,
                                  'alias': c.alias,
                                  'placeholder': c.combinedRootPlaceholder}
                                 for c in cIdCognateClassMap.values()])
    return render_template(request, "language_wordlist.html",
                           {"language": language,
                            "lexemes": lexemes,
                            "prev_language": prev_language,
                            "next_language": next_language,
                            "wordlist": wordlist,
                            "otherMeaningLists": otherMeaningLists,
                            "lex_ed_form": lexemes_editabletable_form,
                            "cognateClasses": cognateClasses,
                            "notTargetCountPerMeaning": notTargetCountPerMeaning,
                            "typeahead": typeahead})


@login_required
@logExceptions
def view_language_check(request, language=None, wordlist=None):
    '''
    Provides an html snipped that contains some sanity checks
    for a given language against a given wordlist.
    If language or wordlist are omitted they are inferred vie defaultModels.
    This function is a result of #159.
    @param language :: str | None
    @param wordlist :: str | None
    '''
    # Infer defaultModels where neccessary:
    if language is None:
        language = getDefaultLanguage(request)
    if wordlist is None:
        wordlist = getDefaultWordlist(request)
    # Fetch data to work with:
    language = Language.objects.get(ascii_name=language)
    wordlist = MeaningList.objects.get(name=wordlist)
    meanings = wordlist.meanings.all()
    # Calculate meaningCounts:
    meaningCountDict = {m.id: 0 for m in meanings}
    mIds = Lexeme.objects.filter(
        language=language,
        meaning__in=meanings,
        not_swadesh_term=0).values_list(
            "meaning_id", flat=True)
    for mId in mIds:
        meaningCountDict[mId] += 1
    meaningCounts = [{'count': meaningCountDict[m.id],
                      'meaning': m.gloss}
                     for m in meanings
                     if meaningCountDict[m.id] != 1]
    meaningCounts.sort(key=lambda x: x['count'])
    # Render report:
    return render_template(request, "language_check.html",
                           {"meaningCounts": meaningCounts})


@login_required
@logExceptions
def add_language_list(request):
    """Start a new language list by cloning an old one"""
    if request.method == "POST":
        form = AddLanguageListForm(request.POST)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-all-languages"))
        if form.is_valid():
            form.save()
            new_list = LanguageList.objects.get(name=form.cleaned_data["name"])
            other_list = LanguageList.objects.get(
                name=form.cleaned_data["language_list"])
            otherLangs = other_list.languages.all().order_by(
                "languagelistorder")
            for language in otherLangs:
                new_list.append(language)
            # edit_language_list(request,
            #                    language_list=form.cleaned_data["name"])
            return HttpResponseRedirect(reverse(
                "edit-language-list", args=[form.cleaned_data["name"]]))
    else:
        form = AddLanguageListForm()
    return render_template(request, "add_language_list.html",
                           {"form": form})


@login_required
@logExceptions
def edit_language_list(request, language_list=None):
    language_list = get_canonical_language_list(
        language_list, request)  # a language list object
    language_list_all = LanguageList.objects.get(name=LanguageList.ALL)
    included_languages = language_list.languages.all().order_by(
        "languagelistorder")
    excluded_languages = language_list_all.languages.exclude(
        id__in=language_list.languages.values_list(
            "id", flat=True)).order_by("languagelistorder")
    if request.method == "POST":
        name_form = EditLanguageListForm(request.POST, instance=language_list)
        if "cancel" in name_form.data:
            # has to be tested before data is cleaned
            return HttpResponseRedirect(
                reverse('view-language-list', args=[language_list.name]))
        list_form = EditLanguageListMembersForm(request.POST)
        list_form.fields["included_languages"].queryset = included_languages
        list_form.fields["excluded_languages"].queryset = excluded_languages
        if name_form.is_valid() and list_form.is_valid():
            changed_members = False
            exclude = list_form.cleaned_data["excluded_languages"]
            include = list_form.cleaned_data["included_languages"]
            if include:
                language_list.remove(include)
                changed_members = True
            if exclude:
                language_list.append(exclude)
                changed_members = True
            if changed_members:
                language_list.save()
                name_form.save()
                return HttpResponseRedirect(
                    reverse('edit-language-list', args=[language_list.name]))
            # changed name
            name_form.save()
            return HttpResponseRedirect(
                reverse('view-language-list',
                        args=[name_form.cleaned_data["name"]]))
    else:
        name_form = EditLanguageListForm(instance=language_list)
        list_form = EditLanguageListMembersForm()
        list_form.fields["included_languages"].queryset = included_languages
        list_form.fields["excluded_languages"].queryset = excluded_languages
    return render_template(request, "edit_language_list.html",
                           {"name_form": name_form,
                            "list_form": list_form,
                            "n_included": included_languages.count(),
                            "n_excluded": excluded_languages.count()})


@login_required
@logExceptions
def delete_language_list(request, language_list):
    language_list = LanguageList.objects.get(name=language_list)
    language_list.delete()
    return HttpResponseRedirect(reverse("view-all-languages"))


@login_required
@logExceptions
def language_add_new(request, language_list):
    language_list = LanguageList.objects.get(name=language_list)
    if request.method == 'POST':
        form = AddLanguageForm(request.POST)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-language-list",
                                                args=[language_list.name]))
        if form.is_valid():
            with transaction.atomic():
                form.save()
                language = Language.objects.get(
                    ascii_name=form.cleaned_data["ascii_name"])
                try:
                    language_list.append(language)
                except IntegrityError:
                    pass  # automatically inserted into LanguageList.DEFAULT
            return HttpResponseRedirect(reverse("language-edit",
                                                args=[language.ascii_name]))
    else:  # first visit
        form = AddLanguageForm()
    return render_template(request, "language_add_new.html",
                           {"form": form})


@login_required
@user_passes_test(lambda u: u.is_staff)
@logExceptions
def edit_language(request, language):
    try:
        language = Language.objects.get(ascii_name=language)
    except Language.DoesNotExist:
        language = get_canonical_language(language, request)
        return HttpResponseRedirect(reverse("language-edit",
                                            args=[language.ascii_name]))

    if request.method == 'POST':
        form = EditSingleLanguageForm(request.POST)
        try:
            form.validate()
            data = form.data
            language = Language.objects.get(id=data['idField'])
            if language.isChanged(**data):
                problem = language.setDelta(request, **data)
                if problem is None:
                    language.save()
                    return HttpResponseRedirect(reverse("view-all-languages"))
                else:
                    messages.error(request, language.deltaReport(**problem))
        except Exception as e:
            logging.exception('Problem updating single language '
                              'in edit_language.')
            messages.error(request, 'Sorry, the server could not update '
                           'the language. %s' % e)
    language.idField = language.id
    form = EditSingleLanguageForm(obj=language)

    return render_template(request, "language_edit.html",
                           {"language": language,
                            "form": form})


@logExceptions
def overview_language(request, language):
    try:
        language = Language.objects.get(ascii_name=language)
    except Language.DoesNotExist:
        language = get_canonical_language(language, request)
        return HttpResponseRedirect(reverse("language-overview",
                                            args=[language.ascii_name]))

    fileName = "Language-Chapter:-%s.md" % (language.ascii_name)
    admin_notes = ''
    if request.user.is_authenticated:
        admin_notes = """
  _For contributors copy the beneath mentioned first template text and follow the link to [create a new page](https://github.com/lingdb/CoBL/wiki/%s)_
```
#### Notes on Orthography
To be written soon.

#### Notes on Transliteration (if appropriate)
To be written soon.

#### Problematic Meanings
To be written soon.
```
  _and follow this link to [create a new public page](https://github.com/lingdb/CoBL-public/wiki/Language-Chapter:-%s) with the following template:_

```
Content comming soon. This article is currently worked on in [private](https://github.com/lingdb/CoBL/wiki/Language-Chapter:-%s).
```
    """ % (fileName, fileName, fileName)

    return render_template(
        request, "language_overview.html",
        {"language": language, "content": fetchMarkdown(fileName, admin_notes)})


@login_required
@logExceptions
def delete_language(request, language):
    try:
        language = Language.objects.get(ascii_name=language)
    except Language.DoesNotExist:
        language = get_canonical_language(language, request)
        return HttpResponseRedirect(reverse("language-delete"),
                                    args=[language.ascii_name])

    language.delete()
    return HttpResponseRedirect(reverse("view-all-languages"))

# -- /meaning(s)/ and /wordlist/ ------------------------------------------


@logExceptions
def view_wordlists(request):
    wordlists = MeaningList.objects.all()
    return render_template(request, "wordlists_list.html",
                           {"wordlists": wordlists})


@csrf_protect
@logExceptions
def view_wordlist(request, wordlist=MeaningList.DEFAULT):
    try:
        wordlist = MeaningList.objects.get(name=wordlist)
    except MeaningList.DoesNotExist:
        raise Http404("MeaningList '%s' does not exist" % wordlist)
    setDefaultWordlist(request, wordlist.name)
    if request.method == 'POST':
        if 'wordlist' in request.POST:
            mltf = MeaningListTableForm(request.POST)
            mltf.validate()
            mltf.handle(request)

    try:
        languageList = LanguageList.objects.get(
            name=getDefaultLanguagelist(request))
    except LanguageList.DoesNotExist:
        raise Http404("LanguageList '%s' does not exist"
                      % getDefaultLanguagelist(request))
    mltf = MeaningListTableForm()
    meanings = wordlist.meanings.order_by(
        "meaninglistorder").prefetch_related('lexeme_set').all()
    for meaning in meanings:
        meaning.computeCounts(languageList=languageList)
        mltf.meanings.append_entry(meaning)

    return render_template(request, "wordlist.html",
                           {"mltf": mltf,
                            "wordlist": wordlist})


@login_required
@logExceptions
def edit_wordlist(request, wordlist):
    wordlist = MeaningList.objects.get(name=wordlist)

    if request.method == 'POST':
        form = EditMeaningListForm(request.POST, instance=wordlist)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-wordlist",
                                                args=[wordlist.name]))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("view-wordlist",
                                                args=[wordlist.name]))
    else:
        form = EditMeaningListForm(instance=wordlist)

    return render_template(request, "edit_wordlist.html",
                           {"wordlist": wordlist,
                            "form": form})


@login_required
@logExceptions
def reorder_wordlist(request, wordlist):
    meaning_id = getDefaultMeaningId(request)
    wordlist = MeaningList.objects.get(name=wordlist)
    meanings = wordlist.meanings.all().order_by("meaninglistorder")

    ReorderForm = make_reorder_meaninglist_form(meanings)
    if request.method == "POST":
        form = ReorderForm(request.POST, initial={"meaning": meaning_id})
        if form.is_valid():
            meaning_id = int(form.cleaned_data["meaning"])
            setDefaultMeaningId(request, meaning_id)
            meaning = Meaning.objects.get(id=meaning_id)
            if form.data["submit"] == "Finish":
                return HttpResponseRedirect(reverse("view-wordlist",
                                                    args=[wordlist.name]))
            else:
                if form.data["submit"] == "Move up":
                    move_meaning(meaning, wordlist, -1)
                elif form.data["submit"] == "Move down":
                    move_meaning(meaning, wordlist, 1)
                else:
                    assert False, "This shouldn't be able to happen"
                return HttpResponseRedirect(reverse("reorder-wordlist",
                                                    args=[wordlist.name]))
        else:  # pressed Finish without submitting changes
            return HttpResponseRedirect(reverse("view-wordlist",
                                                args=[wordlist.name]))
    else:  # first visit
        form = ReorderForm(initial={"meaning": meaning_id})
    return render_template(request, "reorder_wordlist.html",
                           {"wordlist": wordlist, "form": form})


@logExceptions
def move_meaning(meaning, wordlist, direction):
    assert direction in (-1, 1)
    meanings = list(wordlist.meanings.all().order_by("meaninglistorder"))
    index = meanings.index(meaning)
    if index == 0 and direction == -1:
        wordlist.remove(meaning)
        wordlist.append(meaning)
    else:
        try:
            neighbour = meanings[index + direction]
            wordlist.swap(meaning, neighbour)
        except IndexError:
            wordlist.insert(0, meaning)


@login_required
@logExceptions
def add_meaning_list(request):
    """Start a new meaning list by cloning an old one if desired"""
    if request.method == "POST":
        form = AddMeaningListForm(request.POST)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-all-meanings"))
        if form.is_valid():
            form.save()
            new_list = MeaningList.objects.get(name=form.cleaned_data["name"])
            """check if user wants a clone"""
            try:
                other_list = MeaningList.objects.get(
                    name=form.cleaned_data["meaning_list"])
                otherMeanings = other_list.meanings.all().order_by(
                    "meaninglistorder")
                for m in otherMeanings:
                    new_list.append(m)
            except ObjectDoesNotExist:
                """create only a new empty meaning list"""
                pass
            setDefaultWordlist(request, form.cleaned_data["name"])
            return HttpResponseRedirect(reverse(
                "edit-meaning-list", args=[form.cleaned_data["name"]]))
    else:
        form = AddMeaningListForm()
    return render_template(request, "add_meaning_list.html",
                           {"form": form})


@login_required
@logExceptions
def edit_meaning_list(request, meaning_list=None):
    if meaning_list == None:
        meaning_list = getDefaultWordlist(request)
    meaning_list = get_canonical_meaning_list(
        meaning_list, request)  # a meaning list object
    meaning_list_all = MeaningList.objects.get(name=MeaningList.ALL)
    included_meanings = meaning_list.meanings.all().order_by(
        "meaninglistorder")
    excluded_meanings = meaning_list_all.meanings.exclude(
        id__in=meaning_list.meanings.values_list(
            "id", flat=True)).order_by("meaninglistorder")
    if request.method == "POST":
        name_form = EditMeaningListForm(request.POST, instance=meaning_list)
        if "cancel" in name_form.data:
            # has to be tested before data is cleaned
            return HttpResponseRedirect(
                reverse('view-wordlist', args=[meaning_list.name]))
        if "delete" in name_form.data:
            mname = meaning_list.name
            try:
                ml = MeaningListOrder.objects.filter(
                    meaning_list_id=meaning_list.id)
                ml.delete()
            except:
                setDefaultWordlist(request, MeaningList.DEFAULT)
                messages.error(request, 'Error while deleting "' + mname +
                    '": meanings in meaninglistorder could not be deleted!')
                return HttpResponseRedirect(
                    reverse('view-frontpage'))
            try:
                ml = MeaningList.objects.filter(
                    name=mname)
                ml.delete()
            except:
                setDefaultWordlist(request, MeaningList.DEFAULT)
                messages.error(request, 'Error while deleting "'+ mname +
                    '": meaninglist "' + mname + '" does not exist!')
                return HttpResponseRedirect(
                    reverse('view-frontpage'))
            setDefaultWordlist(request, MeaningList.DEFAULT)
            messages.success(request, 'The meaning list "' + mname +
                '" was successfully deleted.')
            return HttpResponseRedirect(
                reverse('edit-meaning-list', args=[MeaningList.DEFAULT]))
        list_form = EditMeaningListMembersForm(request.POST)
        list_form.fields["included_meanings"].queryset = included_meanings
        list_form.fields["excluded_meanings"].queryset = excluded_meanings
        if name_form.is_valid() and list_form.is_valid():
            changed_members = False
            exclude = list_form.cleaned_data["excluded_meanings"]
            include = list_form.cleaned_data["included_meanings"]
            if include:
                meaning_list.remove(include)
                changed_members = True
            if exclude:
                meaning_list.append(exclude)
                changed_members = True
            if changed_members:
                meaning_list.save()
                name_form.save()
                return HttpResponseRedirect(
                    reverse('edit-meaning-list', args=[meaning_list.name]))
            # changed name
            name_form.save()
            return HttpResponseRedirect(
                reverse('view-wordlist',
                        args=[name_form.cleaned_data["name"]]))
    else:
        name_form = EditMeaningListForm(instance=meaning_list)
        list_form = EditMeaningListMembersForm()
        list_form.fields["included_meanings"].queryset = included_meanings
        list_form.fields["excluded_meanings"].queryset = excluded_meanings
    return render_template(request, "edit_meaning_list.html",
                           {"name_form": name_form,
                            "list_form": list_form,
                            "n_included": included_meanings.count(),
                            "n_excluded": excluded_meanings.count()})


@login_required
@logExceptions
def meaning_add_new(request):
    if request.method == 'POST':
        form = EditMeaningForm(request.POST)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-meanings"))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse("meaning-report", args=[form.cleaned_data["gloss"]]))
    else:  # first visit
        form = EditMeaningForm()
    return render_template(request, "meaning_add_new.html",
                           {"form": form})


@login_required
@logExceptions
def edit_meaning(request, meaning):
    try:
        meaning = Meaning.objects.get(gloss=meaning)
    except Meaning.DoesNotExist:
        meaning = get_canonical_meaning(meaning)
        return HttpResponseRedirect(
            reverse("edit-meaning", args=[meaning.gloss]))
    if request.method == 'POST':
        form = EditMeaningForm(request.POST, instance=meaning)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(meaning.get_absolute_url())
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(meaning.get_absolute_url())
    else:
        form = EditMeaningForm(instance=meaning)
    return render_template(request, "meaning_edit.html",
                           {"meaning": meaning,
                            "form": form})


@logExceptions
def view_citations_inline_form(request, model):
    assert model == Lexeme or model == CognateClass, "Unexpected model"
    instance = model.objects.get(id=request.POST.get("id"))

    def getEntries(query):
        entries = []
        for citation in query:
            entries.append({
                'id': citation.id,
                'source_id': citation.source_id,
                'source_name': citation.source.shorthand,
                'pages': citation.pages,
                'comment': citation.comment})
        return entries

    if model == Lexeme:
        entries = getEntries(
            instance.lexemecitation_set.all().select_related('source'))
        return JsonResponse({
            'id': instance.id,
            'model': 'Lexeme',
            'entries': entries
        })
    elif model == CognateClass:
        entries = getEntries(
            instance.cognateclasscitation_set.all().select_related('source'))
        return JsonResponse({
            'id': instance.id,
            'model': 'CognateClass',
            'entries': entries
        })


@logExceptions
def submit_citations_inline_form(request, model):
    assert model == Lexeme or model == CognateClass, "Unexpected model"
    instance = model.objects.get(id=request.POST.get("id"))

    if model == Lexeme:
        citationModel = LexemeCitation
        querySet = instance.lexemecitation_set
    elif model == CognateClass:
        citationModel = CognateClassCitation
        querySet = instance.cognateclasscitation_set

    citations = {str(citation.id): citation for citation in querySet.all()}

    for entry in json.loads(request.POST.get("source_data")):
        if 'id' in entry and entry['id'] in citations:
            citation = citations.pop(entry['id'])
            citation.source_id = int(entry['source_id'])
            citation.pages = entry['pages']
            citation.comment = entry['comment']
            citation.save()
        elif model == Lexeme:
            LexemeCitation.objects.create(
                lexeme_id=instance.id,
                source_id=int(entry['source_id']),
                pages=entry['pages'],
                comment=entry['comment'])
        elif model == CognateClass:
            CognateClassCitation.objects.create(
                cognate_class_id=instance.id,
                source_id=int(entry['source_id']),
                pages=entry['pages'],
                comment=entry['comment'],
                rfcWeblink=entry[rfcWeblink])
    citationModel.objects.filter(id__in=citations.keys()).delete()

    return JsonResponse({
        'id': instance.id,
        'model': request.POST.get("model"),
        'badgeUpdate': querySet.count()})


@login_required
@csrf_protect
@logExceptions
def citation_form_event(request):
    model_dict = {'CognateClass': CognateClass,
                  'Lexeme': Lexeme}
    handlerDict = {'viewCit': view_citations_inline_form,
                   'Submit': submit_citations_inline_form}
    if request.POST.get("model") not in model_dict or\
            request.POST.get("action") not in handlerDict:
        return None
    model = model_dict[request.POST.get("model")]
    return handlerDict[request.POST.get("action")](request, model)


@csrf_protect
@logExceptions
def view_meaning(request, meaning, language_list, lexeme_id=None):
    if request.user.is_authenticated:
        cit_form_response = citation_form_event(request)
        if cit_form_response:
            return cit_form_response

    setDefaultMeaning(request, meaning)
    if language_list is None:
        language_list = getDefaultLanguagelist(request)
    setDefaultLanguagelist(request, language_list)

    # Normalize calling parameters
    canonical_gloss = get_canonical_meaning(meaning).gloss
    current_language_list = get_canonical_language_list(language_list, request)
    mNonCan = meaning != canonical_gloss
    lNonCur = language_list != current_language_list.name
    if mNonCan or lNonCur:
        return HttpResponseRedirect(
            reverse("view-meaning-languages",
                    args=[canonical_gloss, current_language_list.name]))
    else:
        meaning = Meaning.objects.get(gloss=meaning)

    # Handling POST requests:
    if request.method == 'POST':
        # Handling LexemeTableViewMeaningsForm:
        if 'meang_form' in request.POST:
            try:
                lexemesTableForm = LexemeTableViewMeaningsForm(request.POST)
                lexemesTableForm.validate()
                lexemesTableForm.handle(request)
            except Exception as e:
                logging.exception('Problem updating lexemes in view_meaning.')
                messages.error(request, "Sorry, the server had problems "
                                        "updating at least one lexeme: %s" % e)

            return HttpResponseRedirect(
                reverse("view-meaning-languages",
                        args=[canonical_gloss, current_language_list.name]))
        # Handling editCognateClass (#219):
        elif 'editCognateClass' in request.POST:
            try:
                form = LexemeTableEditCognateClassesForm(request.POST)
                form.validate()
                form.handle(request)
            except Exception:
                logging.exception('Problem handling editCognateClass.')

            return HttpResponseRedirect(
                reverse("view-meaning-languages",
                        args=[canonical_gloss, current_language_list.name]))
        # Handling ChooseCognateClassForm:
        else:  # not ('meang_form' in request.POST)
            cognate_form = ChooseCognateClassForm(request.POST)
            if cognate_form.is_valid():
                cj = cognate_form.handle(request, lexeme_id)

                # change this to a reverse() pattern
                return HttpResponseRedirect(anchored(
                    reverse("lexeme-add-cognate-citation",
                            args=[lexeme_id, cj.id])))

    # Gather lexemes:
    lexemes = Lexeme.objects.filter(
        meaning=meaning,
        language__in=current_language_list.languages.exclude(level0=0).all(),
        language__languagelistorder__language_list=current_language_list
        ).order_by(
            "language"
            ).select_related(
                "language",
                "meaning").prefetch_related(
                    "cognatejudgement_set",
                    "cognatejudgement_set__cognatejudgementcitation_set",
                    "lexemecitation_set",
                    "cognate_class",
                    "language__languageclade_set",
                    "language__clades")
    # Gather cognate classes and provide form:
    cognateClasses = CognateClass.objects.filter(lexeme__in=lexemes).distinct()
    cognate_form = ChooseCognateClassForm()
    cognate_form.fields["cognate_class"].queryset = cognateClasses

    # Fill lexemes_editabletable_form:
    lexemes_editabletable_form = LexemeTableViewMeaningsForm()
    for lex in lexemes:
        lexemes_editabletable_form.lexemes.append_entry(lex)
    # Fetch meaningList:
    meaningList = MeaningList.objects.prefetch_related("meanings").get(
        name=getDefaultWordlist(request))
    # Compute typeahead:
    typeahead = json.dumps({
        m.gloss: reverse(
            "view-meaning-languages", args=[m.gloss, current_language_list.name])
        for m in meaningList.meanings.all()})
    # Calculate prev/next meanings:
    prev_meaning, next_meaning = get_prev_and_next_meanings(
        request, meaning, meaning_list=meaningList)

    return render_template(
        request, "view_meaning.html",
        {"meaning": meaning,
         "prev_meaning": prev_meaning,
         "next_meaning": next_meaning,
         "lexemes": lexemes,
         "cognate_form": cognate_form,
         "cognateClasses": json.dumps([{'id': c.id,
                                        'alias': c.alias,
                                        'placeholder':
                                            c.combinedRootPlaceholder}
                                       for c in cognateClasses]),
         "add_cognate_judgement": lexeme_id,
         "lex_ed_form": lexemes_editabletable_form,
         "typeahead": typeahead,
         "clades": Clade.objects.all()})


@csrf_protect
@logExceptions
def view_cognateclasses(request, meaning):
    if request.user.is_authenticated:
        cit_form_response = citation_form_event(request)
        if cit_form_response:
            return cit_form_response
    setDefaultMeaning(request, meaning)
    # Handle POST of AddCogClassTableForm:
    if request.method == 'POST':
        if 'cogclass_form' in request.POST:
            try:
                cogClassTableForm = AddCogClassTableForm(request.POST)
                cogClassTableForm.validate()
                cogClassTableForm.handle(request)
            except ValidationError as e:
                logging.exception(
                    'Validation did not work in view_cognateclasses.')
                messages.error(request, ' '.join(e.messages))
            except Exception as e:
                logging.exception('Problem updating CognateClasses '
                                  'in view_cognateclasses.')
                messages.error(request, 'Sorry, the server had problems '
                               'updating at least one entry: %s' % e)
        elif 'mergeCognateClasses' in request.POST:
            try:
                # Parsing and validating data:
                mergeCCForm = MergeCognateClassesForm(request.POST)
                mergeCCForm.validate()
                mergeCCForm.handle(request)
            except Exception as e:
                logging.exception('Problem merging CognateClasses '
                                  'in view_cognateclasses.')
                messages.error(request, 'Sorry, the server had problems '
                               'merging cognate classes: %s' % e)
        else:
            logging.error('Unexpected POST request in view_cognateclasses.')
            messages.error(request, 'Sorry, the server did '
                           'not understand your request.')
        return HttpResponseRedirect(reverse("edit-cogclasses",
                                            args=[meaning]))
    # Acquiring languageList:
    try:
        languageList = LanguageList.objects.get(
            name=getDefaultLanguagelist(request))
    except LanguageList.DoesNotExist:
        languageList = LanguageList.objects.get(
            name=LanguageList.ALL)
    # languageIds implicated:
    languageIds = languageList.languagelistorder_set.exclude(
        language__level0=0).values_list(
            'language_id', flat=True)
    # Cognate classes to use:
    ccl_ordered = CognateClass.objects.filter(
        cognatejudgement__lexeme__meaning__gloss=meaning,
        cognatejudgement__lexeme__language_id__in=languageIds
    ).prefetch_related('lexeme_set').order_by('alias').distinct()
    # Citations count
    ccl_ordered = ccl_ordered.extra({'citCount':
                                     'SELECT COUNT(*) '
                                     'FROM lexicon_cognateclasscitation '
                                     'WHERE '
                                     'lexicon_cognateclasscitation.'
                                     'cognate_class_id '
                                     '= lexicon_cognateclass.id',
                                    })
    # Computing counts for ccs:
    for cc in ccl_ordered:
        cc.computeCounts(languageList=languageList)

    def cmpKey(x):
        return [-x.cladeCount, -x.lexemeCount, len(x.alias)]
    ccl_ordered = sorted(ccl_ordered, key=cmpKey)
    # Clades to use for #112:
    clades = Clade.objects.filter(
        id__in=LanguageClade.objects.filter(
            language__languagelistorder__language_list=languageList
        ).values_list('clade_id', flat=True)).exclude(
            hexColor='').exclude(shortName='').all()
    # Compute clade <-> cc connections:
    for c in clades:
        c.computeCognateClassConnections(ccl_ordered, languageList)
    # Filling cogclass_editabletable_form:
    cogclass_editabletable_form = AddCogClassTableForm(cogclass=ccl_ordered)
    # Fetch meaningList for typeahead and prev/next calculation:
    meaningList = MeaningList.objects.prefetch_related("meanings").get(
        name=getDefaultWordlist(request))
    # Compute typeahead:
    typeahead = json.dumps({m.gloss: reverse("edit-cogclasses", args=[m.gloss])
                            for m in meaningList.meanings.all()})
    # {prev_,next_,}meaning:
    try:
        meaning = Meaning.objects.get(gloss=meaning)
    except Meaning.DoesNotExist:
        raise Http404("Meaning '%s' does not exist" % meaning)
    prev_meaning, next_meaning = get_prev_and_next_meanings(
        request, meaning, meaning_list=meaningList)
    # Render and done:
    return render_template(request, "view_cognateclass_editable.html",
                           {"meaning": meaning,
                            "prev_meaning": prev_meaning,
                            "next_meaning": next_meaning,
                            "clades": clades,
                            "cogclass_editable_form":
                                cogclass_editabletable_form,
                            "typeahead": typeahead})

##################################################################


@login_required
@logExceptions
def delete_meaning(request, meaning):

    # normalize meaning
    if meaning.isdigit():
        meaning = Meaning.objects.get(id=int(meaning))
        # if there are actions and lexeme_ids these should be preserved too
        return HttpResponseRedirect(reverse("meaning-report",
                                            args=[meaning.gloss]))
    else:
        meaning = Meaning.objects.get(gloss=meaning)

    meaning.delete()
    return HttpResponseRedirect(reverse("view-meanings"))

# -- /lexeme/ -------------------------------------------------------------


@logExceptions
def view_lexeme(request, lexeme_id):
    """For un-logged-in users, view only"""
    try:
        lexeme = Lexeme.objects.get(id=lexeme_id)
    except Lexeme.DoesNotExist:
        messages.info(request,
                      "There is no lexeme with id=%s" % lexeme_id)
        raise Http404
    prev_lexeme, next_lexeme = get_prev_and_next_lexemes(request, lexeme)
    return render_template(request, "lexeme_report.html",
                           {"lexeme": lexeme,
                            "prev_lexeme": prev_lexeme,
                            "next_lexeme": next_lexeme})


@login_required
@logExceptions
def lexeme_edit(request, lexeme_id, action="", citation_id=0, cogjudge_id=0):
    try:
        lexeme = Lexeme.objects.get(id=lexeme_id)
    except Lexeme.DoesNotExist:
        messages.info(request,
                      "There is no lexeme with id=%s" % lexeme_id)
        raise Http404
    citation_id = int(citation_id)
    cogjudge_id = int(cogjudge_id)
    form = None

    def DELETE_CITATION_WARNING_MSG():
        messages.warning(
            request,
            oneline("""Deletion of the final citation is not allowed. If
            you need to, add a new one before deleting the current
            one."""))

    def DELETE_COGJUDGE_WARNING_MSG(citation):
        msg = Template(oneline("""Deletion of final cognate citation is not
            allowed (Delete the cognate class {{ alias }} itself
            instead, if that's what you mean)"""))
        context = RequestContext(request)
        context["alias"] = citation.cognate_judgement.cognate_class.alias
        messages.warning(
            request,
            msg.render(context))

    def warn_if_lacking_cognate_judgement_citation():
        for cognate_judgement in CognateJudgement.objects.filter(
                lexeme=lexeme):
            if CognateJudgementCitation.objects.filter(
                    cognate_judgement=cognate_judgement).count() == 0:
                msg = Template(oneline("""<a
                href="{% url 'lexeme-add-cognate-citation' lexeme_id
                cogjudge_id %}#active">Lexeme has been left with
                cognate judgements lacking citations for cognate
                class {{ alias }}.
                Please fix this [click this message].</a>"""))
                context = RequestContext(request)
                context["lexeme_id"] = lexeme.id
                context["cogjudge_id"] = cognate_judgement.id
                context["alias"] = cognate_judgement.cognate_class.alias
                messages.warning(request, msg.render(context))

    if action:  # actions are: edit, edit-citation, add-citation
        def get_redirect_url(form, citation=None):
            """Pass citation objects to anchor the view in the lexeme
            page"""
            form_data = form.data["submit"].lower()
            if "new lexeme" in form_data:
                redirect_url = reverse("language-add-lexeme",
                                       args=[lexeme.language.ascii_name])
            elif "back to language" in form_data:
                redirect_url = reverse('language-report',
                                       args=[lexeme.language.ascii_name])
            elif "back to meaning" in form_data:
                redirect_url = '%s#lexeme_%s' % (
                    reverse("meaning-report",
                            args=[lexeme.meaning.gloss]),
                    lexeme.id)
            elif citation:
                redirect_url = citation.get_absolute_url()
            else:
                redirect_url = lexeme.get_absolute_url()
            return redirect_url

        # Handle POST data
        if request.method == 'POST':
            if action == "edit":
                form = EditLexemeForm(request.POST, instance=lexeme)
                if "cancel" in form.data:
                    # has to be tested before data is cleaned
                    return HttpResponseRedirect(lexeme.get_absolute_url())
                if form.is_valid():
                    form.save()
                    return HttpResponseRedirect(get_redirect_url(form))
            elif action == "edit-citation":
                form = EditCitationForm(request.POST)
                if "cancel" in form.data:
                    # has to be tested before data is cleaned
                    return HttpResponseRedirect(lexeme.get_absolute_url())
                if form.is_valid():
                    citation = LexemeCitation.objects.get(id=citation_id)
                    update_object_from_form(citation, form)
                    request.session["previous_citation_id"] = citation.id
                    return HttpResponseRedirect(
                        get_redirect_url(form, citation))
            elif action == "add-citation":
                form = AddCitationForm(request.POST)
                if "cancel" in form.data:
                    # has to be tested before data is cleaned
                    return HttpResponseRedirect(lexeme.get_absolute_url())
                if form.is_valid():
                    cd = form.cleaned_data
                    citation = LexemeCitation(
                        lexeme=lexeme,
                        source=cd["source"],
                        pages=cd["pages"],
                        reliability="A",  # `High`
                        comment=cd["comment"])
                    try:
                        citation.save()
                    except IntegrityError:
                        messages.warning(
                            request,
                            oneline("""Lexeme citations must be unique.
                                This source is already cited for this
                                lexeme."""))
                    request.session["previous_citation_id"] = citation.id
                    return HttpResponseRedirect(
                        get_redirect_url(form, citation))
            elif action == "add-new-citation":
                form = AddCitationForm(request.POST)
                if "cancel" in form.data:
                    # has to be tested before data is cleaned
                    return HttpResponseRedirect(lexeme.get_absolute_url())
                if form.is_valid():
                    cd = form.cleaned_data
                    citation = LexemeCitation(
                        lexeme=lexeme,
                        source=cd["source"],
                        pages=cd["pages"],
                        reliability=cd["reliability"],
                        comment=cd["comment"])
                    citation.save()
                    request.session["previous_citation_id"] = citation.id
                    return HttpResponseRedirect(
                        get_redirect_url(form, citation))
            elif action == "delink-citation":
                citation = LexemeCitation.objects.get(id=citation_id)
                try:
                    citation.delete()
                except IntegrityError:
                    DELETE_CITATION_WARNING_MSG()
                return HttpResponseRedirect(lexeme.get_absolute_url())
            elif action == "delink-cognate-citation":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                try:
                    citation.delete()
                except IntegrityError:
                    DELETE_COGJUDGE_WARNING_MSG(citation)
                # warn_if_lacking_cognate_judgement_citation()
                return HttpResponseRedirect(get_redirect_url(form))
            elif action == "edit-cognate-citation":
                form = EditCitationForm(request.POST)
                if "cancel" in form.data:
                    # has to be tested before data is cleaned
                    return HttpResponseRedirect(lexeme.get_absolute_url())
                if form.is_valid():
                    citation = CognateJudgementCitation.objects.get(
                        id=citation_id)
                    update_object_from_form(citation, form)
                    request.session[
                        "previous_cognate_citation_id"] = citation.id
                    return HttpResponseRedirect(
                        get_redirect_url(form, citation))
            elif action == "add-cognate-citation":
                form = AddCitationForm(request.POST)
                if "cancel" in form.data:
                    warn_if_lacking_cognate_judgement_citation()
                    return HttpResponseRedirect(lexeme.get_absolute_url())
                if form.is_valid():
                    judgements = CognateJudgement.objects.get(id=cogjudge_id)
                    citation = CognateJudgementCitation.objects.create(
                        cognate_judgement=judgements, **form.cleaned_data)
                    request.session[
                        "previous_cognate_citation_id"] = citation.id
                    return HttpResponseRedirect(
                        get_redirect_url(form, citation))
            elif action == "add-cognate":
                languagelist = get_canonical_language_list(
                    getDefaultLanguagelist(request), request)
                redirect_url = '%s#lexeme_%s' % (
                    reverse("view-meaning-languages-add-cognate",
                            args=[lexeme.meaning.gloss,
                                  languagelist,
                                  lexeme.id]),
                    lexeme.id)
                return HttpResponseRedirect(redirect_url)
            else:
                assert not action

        # first visit, preload form with previous answer
        else:
            redirect_url = reverse('view-lexeme', args=[lexeme_id])
            if action == "edit":
                form = EditLexemeForm(instance=lexeme)
                # initial={"romanised":lexeme.romanised,
                # "phon_form":lexeme.phon_form,
                # "notes":lexeme.notes,
                # "meaning":lexeme.meaning})
            elif action == "edit-citation":
                citation = LexemeCitation.objects.get(id=citation_id)
                form = EditCitationForm(
                    initial={"pages": citation.pages,
                             "reliability": citation.reliability,
                             "comment": citation.comment})
            elif action in ("add-citation", "add-new-citation"):
                previous_citation_id = request.session.get(
                    "previous_citation_id")
                try:
                    citation = LexemeCitation.objects.get(
                        id=previous_citation_id)
                    form = AddCitationForm(
                        initial={"source": citation.source.id,
                                 "pages": citation.pages,
                                 "reliability": citation.reliability})
                except LexemeCitation.DoesNotExist:
                    form = AddCitationForm()
            elif action == "edit-cognate-citation":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                form = EditCitationForm(
                    initial={"pages": citation.pages,
                             "reliability": citation.reliability,
                             "comment": citation.comment})
            elif action == "delink-cognate":
                cj = CognateJudgement.objects.get(id=cogjudge_id)
                cj.delete()
                return HttpResponseRedirect(redirect_url)
            elif action == "add-cognate-citation":
                previous_citation_id = request.session.get(
                    "previous_cognate_citation_id")
                try:
                    citation = CognateJudgementCitation.objects.get(
                        id=previous_citation_id)
                    form = AddCitationForm(
                        initial={"source": citation.source.id,
                                 "pages": citation.pages,
                                 "reliability": citation.reliability})
                    # "comment":citation.comment})
                except CognateJudgementCitation.DoesNotExist:
                    form = AddCitationForm()
                # form = AddCitationForm()
            elif action == "add-cognate":
                languagelist = get_canonical_language_list(
                    getDefaultLanguagelist(request), request)
                redirect_url = '%s#lexeme_%s' % (
                    reverse("view-meaning-languages-add-cognate",
                            args=[lexeme.meaning.gloss,
                                  languagelist,
                                  lexeme.id]),
                    lexeme.id)
                return HttpResponseRedirect(redirect_url)
                # redirect_url = '%s#lexeme_%s' % (reverse("meaning-report",
                #        args=[lexeme.meaning.gloss]), lexeme.id)
                # return HttpResponseRedirect(redirect_url)
            elif action == "delink-citation":
                citation = LexemeCitation.objects.get(id=citation_id)
                try:
                    citation.delete()
                except IntegrityError:
                    DELETE_CITATION_WARNING_MSG()
                return HttpResponseRedirect(redirect_url)
            elif action == "delink-cognate-citation":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                try:
                    citation.delete()
                except IntegrityError:
                    DELETE_COGJUDGE_WARNING_MSG(citation)
                # warn_if_lacking_cognate_judgement_citation()
                return HttpResponseRedirect(redirect_url)
            elif action == "add-new-cognate":
                current_aliases = CognateClass.objects.filter(
                    lexeme__in=Lexeme.objects.filter(
                        meaning=lexeme.meaning)
                ).distinct().values_list("alias", flat=True)
                new_alias = next_alias(list(current_aliases))
                cognate_class = CognateClass.objects.create(
                    alias=new_alias)
                cj = CognateJudgement.objects.create(
                    lexeme=lexeme, cognate_class=cognate_class)
                return HttpResponseRedirect(anchored(
                    reverse('lexeme-add-cognate-citation',
                            args=[lexeme_id, cj.id])))
            elif action == "delete":
                redirect_url = reverse("view-language-wordlist",
                                       args=[lexeme.language.ascii_name,
                                               getDefaultWordlist(request)])
                lexeme.delete()
                return HttpResponseRedirect(redirect_url)
            else:
                assert not action

    prev_lexeme, next_lexeme = get_prev_and_next_lexemes(request, lexeme)
    return render_template(request, "lexeme_report.html",
                           {"lexeme": lexeme,
                            "prev_lexeme": prev_lexeme,
                            "next_lexeme": next_lexeme,
                            "action": action,
                            "form": form,
                            "active_citation_id": citation_id,
                            "active_cogjudge_citation_id": cogjudge_id})


@login_required
@logExceptions
def lexeme_duplicate(request, lexeme_id):
    """Useful for processing imported data; currently only available
    through direct url input, e.g. /lexeme/0000/duplicate/"""
    original_lexeme = Lexeme.objects.get(id=int(lexeme_id))
    SPLIT_RE = re.compile("[,;]")   # split on these characters
    done_split = False

    if SPLIT_RE.search(original_lexeme.romanised):
        original_romanised, new_romanised = [
            e.strip() for e in SPLIT_RE.split(original_lexeme.romanised, 1)]
        done_split = True
    else:
        original_romanised, new_romanised = original_lexeme.romanised, ""

    if SPLIT_RE.search(original_lexeme.phon_form):
        original_phon_form, new_phon_form = [
            e.strip() for e in SPLIT_RE.split(original_lexeme.phon_form, 1)]
        done_split = True
    else:
        original_phon_form, new_phon_form = original_lexeme.phon_form, ""

    if done_split:
        new_lexeme = Lexeme.objects.create(
            language=original_lexeme.language,
            meaning=original_lexeme.meaning,
            romanised=new_romanised,
            phon_form=new_phon_form,
            notes=original_lexeme.notes)
        for lc in original_lexeme.lexemecitation_set.all():
            LexemeCitation.objects.create(
                lexeme=new_lexeme,
                source=lc.source,
                pages=lc.pages,
                reliability=lc.reliability)
        for cj in original_lexeme.cognatejudgement_set.all():
            new_cj = CognateJudgement.objects.create(
                lexeme=new_lexeme,
                cognate_class=cj.cognate_class)
            for cjc in cj.cognatejudgementcitation_set.all():
                CognateJudgementCitation.objects.create(
                    cognate_judgement=new_cj,
                    source=cjc.source,
                    pages=cjc.pages,
                    reliability=cjc.reliability)

        original_lexeme.romanised = original_romanised
        original_lexeme.phon_form = original_phon_form
        original_lexeme.save()
    redirect_to = "%s#lexeme_%s" % (
        reverse("meaning-report",
                args=[original_lexeme.meaning.gloss]),
        original_lexeme.id)
    return HttpResponseRedirect(redirect_to)


@login_required
@csrf_protect
@logExceptions
def lexeme_add(request, meaning=None, language=None):

    if request.method == "POST":
        form = AddLexemeForm(request.POST)
        try:
            form.validate()
            l = Lexeme(**form.data)
            l.bump(request)
            l.save()
            messages.success(request, 'Created lexeme %s.' % l.id)
            return HttpResponseRedirect(
                reverse("view-language-wordlist",
                        args=[l.language.ascii_name,
                              getDefaultWordlist(request)]))
        except Exception as e:
            logging.exception('Problem adding Lexeme in lexeme_add.')
            messages.error(request, 'Sorry, the server could not '
                           'add the requested lexeme: %s' % e)

    data = {}
    if language:
        language = get_canonical_language(language, request)
        data['language_id'] = language.id
    if meaning:
        meaning = get_canonical_meaning(meaning)
        data["meaning_id"] = meaning.id
    # Computing typeahead info:
    languageTypeahead = json.dumps(dict(
        Language.objects.filter(
            languagelist__name=getDefaultLanguagelist(request)
        ).values_list(
            'utf8_name', 'id')))
    meaningTypeahead = json.dumps(dict(
        Meaning.objects.filter(
            meaninglist__name=getDefaultWordlist(request)
        ).values_list('gloss', 'id')))

    return render_template(request, "lexeme_add.html",
                           {"form": AddLexemeForm(data=data),
                            "languageTypeahead": languageTypeahead,
                            "meaningTypeahead": meaningTypeahead})


@logExceptions
def redirect_lexeme_citation(request, lexeme_id):
    """From a lexeme, redirect to the first citation"""
    lexeme = Lexeme.objects.get(id=lexeme_id)
    try:
        first_citation = lexeme.lexemecitation_set.all()[0]
        return HttpResponseRedirect(redirect("lexeme-citation-detail",
                                             args=[first_citation.id]))
    except IndexError:
        msg = "Operation failed: this lexeme has no citations"
        messages.warning(request, msg)
        return HttpResponseRedirect(lexeme.get_absolute_url())


# -- /cognate/ ------------------------------------------------------------


@logExceptions
def cognate_report(request, cognate_id=0, meaning=None, code=None):

    if cognate_id:
        cognate_class = CognateClass.objects.get(id=int(cognate_id))
    # elif cognate_name:
    #     cognate_class = CognateClass.objects.get(name=cognate_name)
    else:
        assert meaning and code
        cognate_classes = CognateClass.objects.filter(
            alias=code,
            cognatejudgement__lexeme__meaning__gloss=meaning).distinct()
        try:
            assert len(cognate_classes) == 1
            cognate_class = cognate_classes[0]
        except AssertionError:
            msg = u"""error: meaning=‘%s’, cognate code=‘%s’ identifies %s
            cognate sets""" % (meaning, code, len(cognate_classes))
            messages.info(request, oneline(msg))
            return HttpResponseRedirect(reverse('meaning-report',
                                                args=[meaning]))

    # Handling of CognateJudgementSplitTable:
    if request.method == 'POST':
        if 'cognateJudgementSplitTable' in request.POST:
            form = CognateJudgementSplitTable(request.POST)
            try:
                form.validate()
                form.handle(request)
            except Exception as e:
                logging.exception('Problem when splitting CognateClasses '
                                  'in cognate_report.')
                messages.error(request, 'Sorry, the server had trouble '
                               'understanding the request: %s' % e)
        elif 'deleteCognateClass' in request.POST:
            try:
                cognate_class.delete()
                messages.success(request, 'Deleted cognate class.')
                return HttpResponseRedirect('/cognateclasslist/')
            except Exception:
                logging.exception('Failed to delete CognateClass %s '
                                  'in cognate_report.', cognate_class.id)
                messages.error(request, 'Sorry, the server could not delete '
                               'the requested cognate class %s.'
                               % cognate_class.id)
        elif 'deleteCitation' in request.POST:
            try:
                citation = CognateClassCitation.objects.get(
                    id=int(request.POST['citationId']))
                citation.delete()
                messages.success(request, 'Deleted citation.')
            except Exception:
                logging.exception('Failed to delete citation '
                                  'in cognate_report.')
                messages.error(request, 'Sorry, the server could not delete '
                               'the citation.')
        elif 'cognateClassEditForm' in request.POST:
            try:
                form = CognateClassEditForm(request.POST)
                form.validate()
                form.handle(request)
            except ValidationError as e:
                messages.error(
                    request,
                    'Sorry, the server had trouble understanding '
                    'the request: %s' % e)
                # recreate data to provide errorneous form data to the user
                language_list = LanguageList.objects.get(
                    name=getDefaultLanguagelist(request))
                splitTable = CognateJudgementSplitTable()
                ordLangs = language_list.languages.all().order_by("languagelistorder")
                for language in ordLangs:
                    for cj in cognate_class.cognatejudgement_set.filter(
                            lexeme__language=language).all():
                        cj.idField = cj.id
                        splitTable.judgements.append_entry(cj)
                return render(request, 'cognate_report.html', {"cognate_class": cognate_class,
                            "cognateClassForm": form,
                            "splitTable": splitTable})
            except Exception as e:
                logging.exception('Problem handling CognateClassEditForm.')
                messages.error(
                    request,
                    'Sorry, the server had trouble understanding '
                    'the request: %s' % e)
        return HttpResponseRedirect(reverse(
            'cognate-set', args=[cognate_id]))

    language_list = LanguageList.objects.get(
        name=getDefaultLanguagelist(request))
    splitTable = CognateJudgementSplitTable()
    # for language_id in language_list.language_id_list:
    ordLangs = language_list.languages.all().order_by(
        "languageclade__clade_id", "languageclade__cladesOrder" ,"ascii_name")
    for language in ordLangs:
        for cj in cognate_class.cognatejudgement_set.filter(
                lexeme__language=language).all():
            cj.idField = cj.id
            cj.cladeHexColor = Clade.objects.filter(
                languageclade__language_id=language.id,
                languageclade__cladesOrder=3).values_list('hexColor', flat=True).first()
            splitTable.judgements.append_entry(cj)

    # replace markups for note field (used in non-edit mode)
    s = Source.objects.all().filter(deprecated=False)
    notes = cognate_class.notes
    pattern = re.compile(r'(\{ref +([^\{]+?)(:[^\{]+?)? *\})')
    pattern2 = re.compile(r'(\{ref +[^\{]+?(:[^\{]+?)? *\})')
    for m in re.finditer(pattern, notes):
        foundSet = s.filter(shorthand=m.group(2))
        if foundSet.count() == 1:
            notes = re.sub(pattern2, lambda match: '<a href="/sources/'
                + str(foundSet.first().id)
                + '" title="' + foundSet.first().citation_text.replace('"', '\"')
                + '">' + foundSet.first().shorthand + '</a>', notes, 1)
    # replace markups for justificationDiscussion field (used in non-edit mode)
    s = Source.objects.all().filter(deprecated=False)
    justificationDiscussion = cognate_class.justificationDiscussion
    pattern = re.compile(r'(\{ref +([^\{]+?)(:[^\{]+?)? *\})')
    pattern2 = re.compile(r'(\{ref +[^\{]+?(:[^\{]+?)? *\})')
    for m in re.finditer(pattern, justificationDiscussion):
        foundSet = s.filter(shorthand=m.group(2))
        if foundSet.count() == 1:
            justificationDiscussion = re.sub(pattern2, lambda match: '<a href="/sources/'
                + str(foundSet.first().id)
                + '" title="' + foundSet.first().citation_text.replace('"', '\"')
                + '">' + foundSet.first().shorthand + '</a>', justificationDiscussion, 1)


    return render_template(request, "cognate_report.html",
                           {"cognate_class": cognate_class,
                            "notesExpandedMarkups": notes,
                            "justificationDiscussionExpandedMarkups": justificationDiscussion,
                            "cognateClassForm": CognateClassEditForm(
                                obj=cognate_class),
                            "splitTable": splitTable})

# -- /source/ -------------------------------------------------------------


@logExceptions
def source_view(request, source_id):
    source = Source.objects.get(id=source_id)
    return render_template(request, 'source_edit.html', {
        "form": None,
        "source": source,
        "action": ""})


@login_required
@logExceptions
def source_edit(request, source_id=0, action="", cogjudge_id=0, lexeme_id=0):
    source_id = int(source_id)
    cogjudge_id = int(cogjudge_id)
    lexeme_id = int(lexeme_id)
    if source_id:
        source = Source.objects.get(id=source_id)
    else:
        source = None
    if request.method == 'POST':
        form = EditSourceForm(request.POST, instance=source)
        if "cancel" in form.data:
            return HttpResponseRedirect(reverse("view-sources"))
        if form.is_valid():
            if action == "add":
                source = Source.objects.create(**form.cleaned_data)
                if cogjudge_id:  # send back to origin
                    judgement = CognateJudgement.objects.get(id=cogjudge_id)
                    citation = CognateJudgementCitation.objects.create(
                        cognate_judgement=judgement,
                        source=source)
                    return HttpResponseRedirect(
                        reverse('lexeme-edit-cognate-citation',
                                args=[judgement.lexeme.id,
                                      citation.id]))
                if lexeme_id:
                    lexeme = Lexeme.objects.get(id=lexeme_id)
                    citation = LexemeCitation.objects.create(
                        lexeme=lexeme,
                        source=source)
                    return HttpResponseRedirect(reverse(
                        'lexeme-edit-citation', args=[lexeme.id, citation.id]))
            elif action == "edit":
                form.save()
            return HttpResponseRedirect(reverse('view-source',
                                                args=[source.id]))
    else:
        if action == "add":
            form = EditSourceForm()
        elif action == "edit":
            form = EditSourceForm(instance=source)
        elif action == "delete":
            source.delete()
            return HttpResponseRedirect(reverse("view-sources"))
        else:
            form = None
    return render_template(request, 'source_edit.html', {
        "form": form,
        "source": source,
        "action": action})


def source_perms_check(user):
    if user.has_perm('lexicon.change_source') or \
       user.has_perm('lexicon.add_source') or \
       user.has_perm('lexicon.delete_source'):
        return True
    return False


@logExceptions
def source_list(request):

    if request.POST.get("postType") == 'details':
        source_obj = Source.objects.get(pk=request.POST.get("id"))
        response = HttpResponse()
        response.write(SourceDetailsForm(instance=source_obj).as_table())
        return response
    elif request.POST.get("postType") == 'add' and \
            source_perms_check(request.user):
        response = HttpResponse()
        response.write(SourceEditForm().as_table())
        return response
    elif request.POST.get("postType") == 'edit' and \
            source_perms_check(request.user):
        source_obj = Source.objects.get(pk=request.POST.get("id"))
        response = HttpResponse()
        response.write(SourceEditForm(instance=source_obj).as_table())
        return response
    elif request.POST.get("postType") == 'update' and \
            source_perms_check(request.user):
        source_data = QueryDict(request.POST['source_data'].encode('ASCII'))
        if request.POST.get("action") == 'Delete':
            source_obj = Source.objects.get(pk=request.POST.get("id"))
            source_obj.delete()
        elif request.POST.get("action") == 'Update':
            source_obj = Source.objects.get(pk=request.POST.get("id"))
            form = SourceEditForm(source_data, instance=source_obj)
            if form.is_valid():
                form.save()
            else:
                print(form.errors)
        elif request.POST.get("action") == 'Add':
            form = SourceEditForm(source_data)
            if form.is_valid():
                form.save()
            else:
                print(form.errors)
        return HttpResponse()
    elif request.POST.get("postType") == 'deprecated-change' and \
            source_perms_check(request.user):
        source_obj = Source.objects.get(pk=request.POST.get("id"))
        status = {u'true': True, 'false': False}[request.POST.get("status")]
        source_obj.deprecated = status
        source_obj.save()
        return HttpResponse()
    elif request.POST.get("postType") == 'TRS-change' and \
            source_perms_check(request.user):
        source_obj = Source.objects.get(pk=request.POST.get("id"))
        status = {u'true': True, 'false': False}[request.POST.get("status")]
        source_obj.TRS = status
        source_obj.save()
        return HttpResponse()
    elif request.POST.get("postType") == 'filter':
        filter_dict = json.loads(request.POST.getlist("filter_dict[]")[0])
        kwargs = {}
        for key in filter_dict.keys():
            value = filter_dict[key]
            if value not in [u'', None]:
                if key == 'entrytype':
                    key = 'ENTRYTYPE'
                kwargs['{0}__{1}'.format(key, 'icontains')] = value
        if kwargs != {}:
            queryset = Source.objects.filter(**kwargs)
        else:
            queryset = Source.objects.all()
        sources_table = get_sources_table(request, queryset)
        response = HttpResponse()
        RequestConfig(
            request, paginate={'per_page': 1000}).configure(sources_table)
        response.write(sources_table.as_html(request))
        return response
    else:
        sources_table = get_sources_table(request)
        RequestConfig(
            request, paginate={'per_page': 1000}).configure(sources_table)
        return render_template(request, "source_list.html",
                               {"sources": sources_table,
                                "perms": source_perms_check(request.user),
                               })


def get_language_list_obj(request):
    languageList = LanguageList.objects.get(
        id=getDefaultLanguagelistId(request))
    return languageList


def get_meaning_list_obj(request):
    meaningList = MeaningList.objects.get(
        id=getDefaultWordlistId(request))
    return meaningList


def get_default_lexemes(request):
    lexemes = Lexeme.objects.all().filter(
        language_id__in=get_language_list_obj(request).languages.all(),
        meaning_id__in=get_meaning_list_obj(request).meanings.all())
    return lexemes


def get_default_cognatejudgements(request):
    cognatejudgements = CognateJudgement.objects.all().filter(
        lexeme__in=get_default_lexemes(request))
    return cognatejudgements


def get_default_cognateclasses(request):
    ids_lst = get_default_cognatejudgements(request).values_list(
        'cognate_class_id', flat=True)
    cognateclasses = CognateClass.objects.all().filter(id__in=ids_lst)
    return cognateclasses


def get_sources_table(request, queryset=''):
    if queryset == '':
        queryset = Source.objects.all()
    lexeme_ids = list(get_default_lexemes(request).values_list('id',
                                                               flat=True))
    cognatejudgement_ids = list(get_default_cognatejudgements(request)
                                .values_list('id', flat=True))
    cognateclass_ids = list(get_default_cognateclasses(request)
                            .values_list('id', flat=True))
    queryset = queryset.extra({'cognacy_count':
                               'SELECT COUNT(*) '
                               'FROM lexicon_cognatejudgementcitation '
                               'WHERE '
                               'lexicon_cognatejudgementcitation.source_id '
                               '= lexicon_source.id AND '
                               'lexicon_cognatejudgementcitation.'
                               'cognate_judgement_id IN (%s)'
                               % (', '.join(str(v)
                                            for v in cognatejudgement_ids)),
                               'cogset_count':
                               'SELECT COUNT(*) '
                               'FROM lexicon_cognateclasscitation '
                               'WHERE '
                               'lexicon_cognateclasscitation.source_id '
                               '= lexicon_source.id AND '
                               'lexicon_cognateclasscitation.'
                               'cognate_class_id IN (%s)'
                               % (', '.join(str(v)
                                            for v in cognateclass_ids)),
                               'lexeme_count':
                               'SELECT COUNT(*) '
                               'FROM lexicon_lexemecitation '
                               'WHERE '
                               'lexicon_lexemecitation.source_id '
                               '= lexicon_source.id AND '
                               'lexicon_lexemecitation.'
                               'lexeme_id IN (%s)'
                               % (', '.join(str(v)
                                            for v in lexeme_ids))
                              })
    return SourcesTable(queryset)


def export_bibtex(request):
    response = HttpResponse(content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="export.bib"'

    db = BibDatabase()
    writer = BibTexWriter()
    for source_obj in Source.objects.all():
        db.entries.append(source_obj.bibtex_dictionary)
    response.write(writer.write(db))
    return response


class source_import(FormView):

    form_class = UploadBiBTeXFileForm
    template_name = 'source_import.html'
    success_url = '/sources/'  # Replace with your URL or reverse().
    source_attr_lst = Source().bibtex_attr_lst

    @method_decorator(logExceptions)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(source_import, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        return render_template(
            request,
            self.template_name, {'form': form, 'update_sources_table': None})

    def post(self, request, *args, **kwargs):
        if request.POST.get("postType") == 'import':
            for update_dict in request.POST.getlist('changes[]'):
                update_dict = json.loads(update_dict)
                if update_dict['id'] == u'new':
                    s = Source()
                else:
                    s = Source.objects.get(pk=update_dict['id'])
                for key in update_dict.keys():
                    if key not in ['id']:
                        value = update_dict[key]
                        if value == u'None':
                            value = u''
                        setattr(s, key, value)
                s.save()
            return HttpResponseRedirect(reverse("view-sources"))
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            files = request.FILES.getlist('file')
            if form.is_valid():
                update_sources_dict_lst = []
                new_sources_dict_lst = []
                for f in files:
                    result = self.get_bibtex_data(f)
                    update_sources_dict_lst += result['update']
                    new_sources_dict_lst += result['new']
                update_sources_table = new_sources_table = ''
                if update_sources_dict_lst:
                    update_sources_table = SourcesUpdateTable(
                        update_sources_dict_lst)
                    RequestConfig(
                        request,
                        paginate={'per_page': 1000}
                    ).configure(update_sources_table)
                if new_sources_dict_lst:
                    new_sources_table = SourcesUpdateTable(
                        new_sources_dict_lst)
                    RequestConfig(
                        request,
                        paginate={'per_page': 1000}
                    ).configure(new_sources_table)
                return render_template(request, self.template_name, {
                    'form': self.form_class(),
                    'update_sources_table': update_sources_table,
                    'new_sources_table': new_sources_table,
                })
            else:
                return self.form_invalid(form)

    def get_bibtex_data(self, f):

        parser = BibTexParser()
        parser.ignore_nonstandard_types = False
        bib_database = bibtexparser.loads(f.read().decode('utf-8'), parser)
        update_sources_dict_lst = []
        new_sources_dict_lst = []
        for entry in bib_database.entries:
            result = self.get_comparison_dict(entry)
            if result['status'] == 'update':
                update_sources_dict_lst.append(result['dictionary'])
            else:
                new_sources_dict_lst.append(result['dictionary'])
        return {'update': update_sources_dict_lst, 'new': new_sources_dict_lst}

    def get_comparison_dict(self, entry):

        if entry['ID']:
            try:
                source_obj = Source.objects.get(pk=entry['ID'])
                return self.get_update_dict(entry, source_obj)
            except (ValueError, ObjectDoesNotExist):
                return self.get_new_dict(entry)
        return self.get_new_dict(entry)

    def get_update_dict(self, entry, source_obj):

        comparison_dict = {}
        comparison_dict['pk'] = entry['ID']
        for key in [key for key in entry.keys()
                    if key not in ['ID', 'date', 'type']]:
            if key in ['trs', 'deprecated']:
                entry[key] = json.loads(entry[key].lower())
            if key in ['trs']:
                entry[key.upper()] = entry[key]
                key = key.upper()
            if getattr(source_obj, key) == entry[key]:
                comparison_dict[key] = [entry[key], 'same']
            else:
                old_value = getattr(source_obj, key)
                if old_value in ['', u'—', None]:
                    old_value = 'None'
                new_value = entry[key]
                if new_value in ['', u'—', None]:
                    new_value = 'None'
                comparison_dict[key] = [
                    '<p class="oldValue">%s</p>'
                    '<p class="newValue">%s</p>' %
                    (old_value, new_value), 'changed']
        for key in self.source_attr_lst:
            if key not in comparison_dict.keys():
                if getattr(source_obj, key) not in ['', None]:
                    comparison_dict[key] = [
                        '<p class="oldValue">%s</p>'
                        '<p class="newValue">None</p>' %
                        (getattr(source_obj, key)), 'changed']

        return {'status': 'update', 'dictionary': comparison_dict}

    def get_new_dict(self, entry):

        comparison_dict = {}
        comparison_dict['pk'] = 'new'
        for key in entry.keys():
            comparison_dict[key] = [entry[key], 'new']
        return {'status': 'new', 'dictionary': comparison_dict}


def source_related(request, formset, name, source_obj):
    return render_template(request, "source_related_inline.html",
                           {"formset": formset,
                            "name": name,
                            "source": source_obj.shorthand
                           })


def source_cognacy(request, source_id):
    source_obj = Source.objects.get(pk=source_id)
    formset = CognateJudgementFormSet(
        instance=source_obj,
        queryset=CognateJudgementCitation.objects.filter(
            cognate_judgement__in=get_default_cognatejudgements(request)))
    name = "Cognacy"
    return source_related(request, formset, name, source_obj)


def source_cogset(request, source_id):
    source_obj = Source.objects.get(pk=source_id)
    formset = CognateClassFormSet(
        instance=source_obj,
        queryset=CognateClassCitation.objects.filter(
            cognate_class__in=get_default_cognateclasses(request)))
    name = "Cognate Sets"
    return source_related(request, formset, name, source_obj)


def source_lexeme(request, source_id):
    source_obj = Source.objects.get(pk=source_id)
    formset = LexemeFormSet(
        instance=source_obj,
        queryset=LexemeCitation.objects.filter(
            lexeme__in=get_default_lexemes(request)))
    name = "Lexemes"
    return source_related(request, formset, name, source_obj)


class SourceAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return Source.objects.none()
        qs = Source.objects.all()
        if self.q:
            qs = qs.filter(shorthand__icontains=self.q)
        return qs

# -- /source end/ -------------------------------------------------------------


@logExceptions
def lexeme_search(request):
    if request.method == 'POST':
        form = SearchLexemeForm(request.POST)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-frontpage"))
        if form.is_valid():
            regex = form.cleaned_data["regex"]
            languages = form.cleaned_data["languages"]
            if not languages:
                languages = Language.objects.all()
            if form.cleaned_data["search_fields"] == "L":
                # Search language fields
                lexemes = Lexeme.objects.filter(
                    Q(phon_form__regex=regex) |
                    Q(romanised__regex=regex),
                    language__in=languages)[:LIMIT_TO]
            else:
                # Search English fields
                assert form.cleaned_data["search_fields"] == "E"
                lexemes = Lexeme.objects.filter(
                    Q(gloss__regex=regex) |
                    Q(notes__regex=regex) |
                    Q(meaning__gloss__regex=regex),
                    language__in=languages)[:LIMIT_TO]
            language_names = [(l.utf8_name or l.ascii_name) for l in languages]
            return render_template(request, "lexeme_search_results.html",
                                   {"regex": regex,
                                    "language_names": language_names,
                                    "lexemes": lexemes,
                                   })
    else:
        form = SearchLexemeForm()
    return render_template(request, "lexeme_search.html",
                           {"form": form})


@logExceptions
def viewDefaultLanguage(request):
    language = getDefaultLanguage(request)
    wordlist = getDefaultWordlist(request)
    return view_language_wordlist(request, language, wordlist)


@logExceptions
def viewDefaultMeaning(request):
    meaning = getDefaultMeaning(request)
    languagelist = getDefaultLanguagelist(request)
    return view_meaning(request, meaning, languagelist)


@logExceptions
def viewDefaultCognateClassList(request):
    meaning = getDefaultMeaning(request)
    return view_cognateclasses(request, meaning)


@logExceptions
def viewAbout(request, page):
    """
    @param page :: str
    This function renders an about page.
    """
    if page == 'statistics':
        return viewStatistics(request)
    pageTitleMap = {
        'contact': 'Contact',
        'furtherInfo': 'Further Info',
        'home': 'Home'
    }
    baseUrl = 'https://raw.githubusercontent.com/wiki/lingdb/CoBL-public/'
    pageUrlMap = {
        'contact': baseUrl + 'About-Page:-Contact.md',
        'furtherInfo': baseUrl + 'About-Page:-Further-Info.md',
        'home': baseUrl + 'About-Page:-Home.md'
    }
    return render_template(request, "about.html",
                           {'title': pageTitleMap.get(page, 'Error'),
                            'content': fetchMarkdown(pageUrlMap[page])})


@logExceptions
def viewStatistics(request):
    return render_template(
        request, "statistics.html",
        {"lexemes": Lexeme.objects.count(),
         "cognate_classes": CognateClass.objects.count(),
         "languages": Language.objects.count(),
         "meanings": Meaning.objects.count(),
         "coded_characters": CognateJudgement.objects.count(),
         "google_site_verification": META_TAGS})


@csrf_protect
@logExceptions
def viewAuthors(request):
    if request.method == 'POST':
        '''
        We need to distinguish several cases here:
        * Creation of a new author
        * Modification of an existing author
        * Deletion of an author
        '''
        if 'addAuthor' in request.POST:
            authorCreationForm = AuthorCreationForm(request.POST)
            try:
                authorCreationForm.validate()
                newAuthor = Author(**authorCreationForm.data)
                with transaction.atomic():
                    newAuthor.save(force_insert=True)
            except Exception as e:
                logging.exception('Problem creating author in viewAuthors.')
                messages.error(request, 'Sorry, the server could not '
                               'create new author as requested: %s' % e)
        elif 'authors' in request.POST:
            authorData = AuthorTableForm(request.POST)
            try:
                authorData.validate()
                authorData.handle(request)
            except Exception as e:
                logging.exception('Problem updating authors in viewAuthors.')
                messages.error(request, 'Sorry, the server had problems '
                               'updating at least one author: %s' % e)
        elif 'deleteAuthor' in request.POST:
            deleteAuthor = AuthorDeletionForm(request.POST)
            try:
                deleteAuthor.validate()
                deleteAuthor.handle(request)
            except Exception as e:
                logging.exception('Problem deleting author in viewAuthors.')
                messages.error(request, 'Sorry, the server had problems '
                               'deleting the requested author: %s' % e)
        elif 'currentAuthorForm' in request.POST:
            currentAuthorForm = AuthorRowForm(request.POST)
            try:
                currentAuthorForm.validate()
                currentAuthorForm.handle(request)
            except Exception as e:
                logging.exception('Problem updating current author.')
                messages.error(request, 'Sorry, the server had problems '
                               'updating the requested author: %s' % e)
        else:
            logging.error('Unexpected POST request in viewAuthors.')
            messages.error(request, 'Sorry, the server did not '
                           'understand the request.')
        return HttpResponseRedirect(
            reverse("viewAuthors", args=[]))

    languageList = LanguageList.objects.get(
        name=getDefaultLanguagelist(request))
    languageData = languageList.languages.values_list(
        'utf8_name', 'author')

    authors = Author.objects.all()
    form = AuthorTableForm()
    for author in authors:

        author.idField = author.id
        form.elements.append_entry(author)
        authored = 0
        namesOfLanguages = []
        for aName, aString in languageData:
            if author.fullName in set(aString.split(' and ')):
                authored += 1
                namesOfLanguages.append(aName)
        author.nol = str(authored)
        author.nolgs = ', '.join(namesOfLanguages)

    currentAuthorForm = None
    if request.user.is_authenticated:
        query = Author.objects.filter(user_id=request.user.id)
        if Author.objects.filter(user_id=request.user.id).exists():
            currentAuthor = query.all()[0]
            currentAuthor.idField = currentAuthor.id
            currentAuthorForm = AuthorRowForm(obj=currentAuthor)

    return render_template(
        request, "authors.html", {'authors': form,
                                  'currentAuthorForm': currentAuthorForm})


@csrf_protect
@logExceptions
def viewAuthor(request, initials):
    try:
        author = Author.objects.get(initials=initials)
    except Author.DoesNotExist:
        messages.error(request, "Unknown Author initials: %s." % initials)
        return HttpResponseRedirect(reverse("viewAuthors"))
    languageList = LanguageList.objects.get(
        name=getDefaultLanguagelist(request))
    languageData = languageList.languages.values_list(
        'ascii_name', 'utf8_name', 'author', 'reviewer')
    authored = []
    reviewed = []
    for aName, uName, aString, rString in languageData:
        if author.fullName in set(aString.split(' and ')):
            authored.append((aName, uName))
        if author.fullName in set(rString.split(' and ')):
            reviewed.append((aName, uName))
    return render_template(
        request, "author.html", {
            'author': author,
            'authored': authored,
            'reviewed': reviewed,
            'wordlist': getDefaultWordlist(request),
            'content': fetchMarkdown(
                "Author-description:-%s.md" % author.initials)})


@logExceptions
def changeDefaults(request):
    # Functions to get defaults:
    getDefaults = {
        'language': getDefaultLanguage,
        'meaning': getDefaultMeaning,
        'wordlist': getDefaultWordlist,
        'languagelist': getDefaultLanguagelist}
    # Current defaults:
    defaults = {k: v(request) for (k, v) in getDefaults.items()}
    # Defaults that can be changed:
    actions = {
        'language': setDefaultLanguage,
        'meaning': setDefaultMeaning,
        'wordlist': setDefaultWordlist,
        'languagelist': setDefaultLanguagelist}
    # Changing defaults for given parameters:
    for k, v in actions.items():
        if k in request.GET:
            v(request, request.GET[k])
    # Find changed defaults to substitute in url:
    substitutes = {}
    for k, v in getDefaults.items():
        default = v(request)
        if defaults[k] != default:
            substitutes[defaults[k]] = default
    # Url to redirect clients to:
    url = request.GET['url'] if 'url' in request.GET else '/'
    # Substitute defaults in url:
    for k, v in substitutes.items():
        url = url.replace(k, v)
    # Redirect to target url:
    return redirect(url)


@logExceptions
def view_frontpage(request):
    return viewAbout(request, 'home')


@logExceptions
@csrf_protect
@login_required
def view_nexus_export(request, exportId=None):
    if exportId is not None:
        if request.method == 'GET':
            try:
                export = NexusExport.objects.get(id=exportId)
                if not export.pending:
                    return export.generateResponse(
                        constraints='constraints' in request.GET,
                        beauti='beauti' in request.GET,
                        tabledata='datatable' in request.GET,
                        matrix='matrix' in request.GET)
                # Message if pending:
                messages.info(request,
                              "Sorry, the server is still "
                              "computing export %s." % exportId)
            except NexusExport.DoesNotExist:
                messages.error(request,
                               "Sorry, but export %s does not "
                               "exist in the database." % exportId)
        elif request.method == 'POST' and 'delete' in request.POST:
            NexusExport.objects.filter(id=exportId).delete()
            messages.info(request, "Deleted export %s." % exportId)
            return HttpResponseRedirect(reverse("view_nexus_export_base"))

    exports = NexusExport.objects.order_by('-id').all()
    languageListNames = set([e.language_list_name for e in exports])
    meaningListNames = set([e.meaning_list_name for e in exports])

    def num(s):
        try:
            return int(s)
        except ValueError:
            return -1

    # get the meaning and language counts at the moment of export via saved exportName
    # since the counts of meanings and languages can change over time
    for e in exports:
        try:
            c = re.search('_Lgs(\d+)', e.exportName).group(1)
        except AttributeError:
            c = -1
        e.languageListCount = num(c)
        try:
            c = re.search('_Mgs(\d+)', e.exportName).group(1)
        except AttributeError:
            c = -1
        e.meaningListCount = num(c)
        e.shortNameAuthor = re.sub('[^A-Z]', '', e.lastEditedBy)

    return render_template(
        request, "view_nexus_export.html",
        {'exports': exports})


@csrf_protect
@logExceptions
def view_two_languages_wordlist(request,
                                targetLang=None,
                                sourceLang=None,
                                wordlist=None):
    '''
    Implements two languages * all meanings view for #256
    targetLang :: str | None
    sourceLang :: str | None
    wordlist :: str | None
    If targetLang is given it will be treated as the default language.
    '''
    # Setting defaults if possible:
    if targetLang is not None:
        setDefaultLanguage(request, targetLang)
    if sourceLang is not None:
        setDefaultSourceLanguage(request, sourceLang)
    if wordlist is not None:
        setDefaultWordlist(request, wordlist)
    # Fetching targetLang to operate on:
    if targetLang is None:
        targetLang = getDefaultLanguage(request)
    try:
        targetLang = Language.objects.get(ascii_name=targetLang)
    except Language.DoesNotExist:
        raise Http404("Language '%s' does not exist" % targetLang)
    # Fetching sourceLang to operate on:
    if sourceLang is None:
        sourceLang = getDefaultSourceLanguage(request)
    if sourceLang is not None:
        try:
            sourceLang = Language.objects.get(ascii_name=sourceLang)
        except Language.DoesNotExist:
            sourceLang = None
    # Fetching wordlist to operate on:
    if wordlist is None:
        wordlist = getDefaultWordlist(request)
    try:
        wordlist = MeaningList.objects.get(name=wordlist)
    except MeaningList.DoesNotExist:
        raise Http404("MeaningList '%s' does not exist" % wordlist)

    if request.method == 'POST':
        # Handling cognate class assignments (#312):
        if 'assigncognates' in request.POST:
            form = AssignCognateClassesFromLexemeForm(request.POST)
            return form.handle()
        # Updating lexeme table data:
        elif 'lex_form' in request.POST:
            try:
                form = TwoLanguageWordlistTableForm(request.POST)
                form.validate()
                form.handle(request)
            except Exception as e:
                logging.exception('Problem updating lexemes '
                                  'in view_two_languages_wordlist.')
                messages.error(request, 'Sorry, the server had problems '
                               'updating at least one lexeme: %s' % e)
            return HttpResponseRedirect(
                reverse("view-two-languages",
                        args=[targetLang.ascii_name,
                              sourceLang.ascii_name if sourceLang else None,
                              wordlist.name]))

    def getLexemesForBothLanguages(targetLang, sourceLang):
        # Helper function to fetch lexemes
        # sourceLang will marked via column sourceLg by 1 for sorting and identifying
        return Lexeme.objects.filter(
            language__in=[targetLang, sourceLang],
            meaning__meaninglist=wordlist
        ).annotate(sourceLg=RawSQL("select (CASE WHEN language_id = %s THEN 1 ELSE 0 END)", (sourceLang,))
        ).select_related("meaning", "language").prefetch_related(
            "cognatejudgement_set",
            "cognatejudgement_set__cognatejudgementcitation_set",
            "cognate_class",
            "lexemecitation_set").order_by("meaning__gloss", "sourceLg", "romanised")

    # collect data:
    mIdOrigLexDict = defaultdict(list)  # Meaning.id -> [Lexeme]
    if sourceLang:
        mergedLexemes = getLexemesForBothLanguages(targetLang.id, sourceLang.id)
        for l in mergedLexemes.filter(language=sourceLang):
            mIdOrigLexDict[l.meaning_id].append(l)
    else:
        mergedLexemes = getLexemesForBothLanguages(targetLang, -1)

    # define colours for highlighting shared cognate sets
    # colours will be rotated
    ccColors = deque(['#FFCCCB','#FFCC00'])

    # init some stats counter helpers
    numOfSwadeshMeaningsSharedCC = set()
    numOfSwadeshMeaningsNotTargetSharedCC = set()
    numOfSwadeshMeanings = set()
    hasNotTargets = set()

    # - highlight same cognate classes per meaning
    # - calculating some stats
    matchedCC = False
    matchedSwadeshCC = False
    for l in mergedLexemes:
        # find shared cognate classes
        l.ccBackgroundColor = "#FFFFFF" # default background color for cognate set
        if l.meaning_id in mIdOrigLexDict:
            if l.not_swadesh_term:
                hasNotTargets.add(l.meaning_id)
            if l.sourceLg:
                # since targetLang will be detected first
                # check via matchedCC (set of lexeme ids) whether there's a possible match
                if matchedCC and matchedCC in l.allCognateClasses:
                    l.ccBackgroundColor = ccColors[0]
                    ccColors.rotate(1)
            else:
                m = mIdOrigLexDict[l.meaning.id]
                # store source info for merging
                l.originalIds = [{'id':s.id, 'romanised':s.romanised} for s in m]
                # iterate through all lexemes of both languages for given meaning
                for cc in l.allCognateClasses:
                    for cc1 in m:
                        if cc in cc1.allCognateClasses:
                            l.ccBackgroundColor = ccColors[0]
                            matchedCC = cc
                            # counter for shared Swadesh only cognate classes
                            if not cc1.not_swadesh_term and not l.not_swadesh_term:
                                numOfSwadeshMeaningsSharedCC.add(l.meaning_id)
                            else:
                                numOfSwadeshMeaningsNotTargetSharedCC.add(l.meaning_id)
                        # counter for Swadesh only meaning sets
                        if not cc1.not_swadesh_term and not l.not_swadesh_term:
                            numOfSwadeshMeanings.add(l.meaning_id)

    # add new boolean data for filtering shared cognate classes
    # column will be hidden in HTML
    for l in mergedLexemes:
        l.ccSwdKind = (l.meaning_id in numOfSwadeshMeaningsSharedCC)
        if l.meaning_id in numOfSwadeshMeaningsNotTargetSharedCC and l.meaning_id in numOfSwadeshMeanings and l.ccBackgroundColor != "#FFFFFF":
            l.notTargetCC = True
            l.ccBackgroundColor = "#FFFFFF"
        else:
            l.notTargetCC = False
        l.hasNotTargets = (l.meaning_id in hasNotTargets)

    lexemeTable = TwoLanguageWordlistTableForm(lexemes=mergedLexemes)

    otherMeaningLists = MeaningList.objects.exclude(id=wordlist.id).all()

    languageList = LanguageList.objects.prefetch_related('languages').get(
        name=getDefaultLanguagelist(request))
    typeahead1 = json.dumps({
        l.utf8_name: reverse(
            "view-two-languages",
            args=[l.ascii_name,
                  sourceLang.ascii_name if sourceLang else None,
                  wordlist.name])
        for l in languageList.languages.all()})
    typeahead2 = json.dumps({
        l.utf8_name: reverse(
            "view-two-languages",
            args=[targetLang.ascii_name, l.ascii_name, wordlist.name])
        for l in languageList.languages.all()})

    if len(numOfSwadeshMeanings) != 0:
        numOfSharedCCPerSwadeshMeanings = "%.1f%%" % float(
                                    len(numOfSwadeshMeaningsSharedCC)/len(numOfSwadeshMeanings)*100)
    else:
        numOfSharedCCPerSwadeshMeanings = ""

    return render_template(request, "twoLanguages.html",
                           {"targetLang": targetLang,
                            "sourceLang": sourceLang,
                            "wordlist": wordlist,
                            "otherMeaningLists": otherMeaningLists,
                            "lex_ed_form": lexemeTable,
                            "numOfSwadeshMeaningsSharedCC": len(numOfSwadeshMeaningsSharedCC),
                            "numOfSwadeshMeanings": len(numOfSwadeshMeanings),
                            "numOfSharedCCPerSwadeshMeanings": numOfSharedCCPerSwadeshMeanings,
                            "typeahead1": typeahead1,
                            "typeahead2": typeahead2})


@csrf_protect
@logExceptions
def view_language_progress(request, language_list=None):
    current_list = get_canonical_language_list(language_list, request)
    setDefaultLanguagelist(request, current_list.name)

    if (request.method == 'POST') and ('progress_form' in request.POST):
        form = LanguageListProgressForm(request.POST)
        try:
            form.validate()
        except Exception as e:
            logging.exception(
                'Exception in POST validation for view_language_list')
            messages.error(request, 'Sorry, the form data sent '
                           'did not pass server side validation: %s' % e)
            return HttpResponseRedirect(
                reverse("view-language-progress", args=[current_list.name]))
        # Updating languages and gathering clades to update:
        updateClades = form.handle(request)
        # Updating clade relations for changes languages:
        if updateClades:
            updateLanguageCladeRelations(languages=updateClades)
        # Redirecting so that UA makes a GET.
        exportMethod = ''
        if 'onlyexport' in request.path.split('/'):
            exportMethod = 'onlyexport'
        elif 'onlynotexport' in request.path.split('/'):
            exportMethod = 'onlynotexport'
        return HttpResponseRedirect(
            reverse("view-language-progress", args=[current_list.name,exportMethod]))

    languages = current_list.languages.all().prefetch_related(
        "lexeme_set", "lexeme_set__meaning",
        "languageclade_set", "clades")
    meaningList = MeaningList.objects.get(name=getDefaultWordlist(request))
    form = LanguageListProgressForm()
    exportMethod = ''
    if request.method == 'GET':
        if 'onlyexport' in request.path.split('/'):
            exportMethod = 'onlyexport'
        elif 'onlynotexport' in request.path.split('/'):
            exportMethod = 'onlynotexport'
    for lang in languages:
        lang.idField = lang.id
        lang.computeCounts(meaningList, exportMethod)
        form.langlist.append_entry(lang)

    otherLanguageLists = LanguageList.objects.exclude(name=current_list).all()

    noexportbutton = {}

    if request.method == 'GET':
        if 'onlyexport' in request.path.split('/'):
            noexportbutton = {
                "note": "based on only those meanings marked for 'export'",
                "url": "/".join(request.path.split('/')[0:-1]) + "/onlynotexport", 
                "tooltip": "Show statistics based on all meanings which are marked only for 'not export'", 
                "state": "btn-success", 
                "icon": "glyphicon glyphicon-ok"}
        elif 'onlynotexport' in request.path.split('/'):
            noexportbutton = {
                "note": "based on only those meanings marked for 'not for export'",
                "url": "/".join(request.path.split('/')[0:-1]), 
                "tooltip": "Show statistics based on all meanings including those which are marked for 'not export'", 
                "state": "btn-danger", 
                "icon": "glyphicon glyphicon-remove"}
        else:
            noexportbutton = {
                "note": "based on all meanings including those marked for 'not for export'",
                "url": request.path + "onlyexport", 
                "tooltip": "Show statistics based on only those meanings which are marked for 'export'", 
                "state": "btn-default", 
                "icon": "glyphicon-question-sign"}

    return render_template(request, "language_progress.html",
                           {"languages": languages,
                            'form': form,
                            "current_list": current_list,
                            "otherLanguageLists": otherLanguageLists,
                            "noexportbutton": noexportbutton,
                            "wordlist": getDefaultWordlist(request),
                            "clades": Clade.objects.all()})


@csrf_protect
@logExceptions
def view_language_distributions(request, language_list=None):
    current_list = get_canonical_language_list(language_list, request)
    setDefaultLanguagelist(request, current_list.name)
    languages = current_list.languages.all().prefetch_related(
        "lexeme_set", "lexeme_set__meaning",
        "languageclade_set", "clades")

    if (request.method == 'POST') and ('langlist_form' in request.POST):
        form = LanguageDistributionTableForm(request.POST)
        try:
            form.validate()
            form.handle(request)
        except Exception as e:
            logging.exception(
                'Exception in POST validation for view_language_distributions')
            messages.error(request, 'Sorry, the form data sent '
                           'did not pass server side validation: %s' % e)
            return HttpResponseRedirect(
                reverse("view_language_distributions",
                        args=[current_list.name]))
        # Redirecting so that UA makes a GET.
        return HttpResponseRedirect(
            reverse("view-language-distributions", args=[current_list.name]))

    meaningList = MeaningList.objects.get(name=getDefaultWordlist(request))
    languages_editabletable_form = LanguageDistributionTableForm()
    exportMethod = ''
    if request.method == 'GET':
        if 'onlyexport' in request.path.split('/'):
            exportMethod = 'onlyexport'
        elif 'onlynotexport' in request.path.split('/'):
            exportMethod = 'onlynotexport'
    for lang in languages:
        lang.idField = lang.id
        lang.computeCounts(meaningList, exportMethod)
        languages_editabletable_form.langlist.append_entry(lang)

    otherLanguageLists = LanguageList.objects.exclude(name=current_list).all()

    return render_template(request, "language_distributions.html",
                           {"languages": languages,
                            'lang_ed_form': languages_editabletable_form,
                            "current_list": current_list,
                            "otherLanguageLists": otherLanguageLists,
                            "wordlist": getDefaultWordlist(request),
                            "clades": Clade.objects.all()})


@logExceptions
def json_cognateClass_placeholders(request):
    if request.method == 'GET' and 'lexemeid' in request.GET:
        meaningIds = Lexeme.objects.filter(
            id=int(request.GET['lexemeid'])).values_list(
                'meaning_id', flat=True)
        cognateClasses = CognateClass.objects.filter(
            lexeme__meaning_id__in=meaningIds).distinct()
        # lexemes = [int(s) for s in request.GET['lexemes'].split(',')]
        # cognateClasses = CognateClass.objects.filter(
        # lexeme__in=lexemes).distinct()
        dump = json.dumps([{'id': c.id,
                            'alias': c.alias,
                            'placeholder':
                                c.combinedRootPlaceholder}
                           for c in cognateClasses]),
        return HttpResponse(dump)
    return HttpResponse(
        "Please provide `lexemes` parameter detailing lexeme ids.")


@logExceptions
def view_cladecognatesearch(request):
    # Handle POST of AddCogClassTableForm:
    if request.method == 'POST':
        if 'AddCogClassTableForm' in request.POST:
            try:
                cogClassTableForm = AddCogClassTableForm(request.POST)
                cogClassTableForm.validate()
                cogClassTableForm.handle(request)
            except ValidationError as e:
                logging.exception(
                    'Validation did not work in view_cladecognatesearch.')
                messages.error(request, ' '.join(e.messages))
            except Exception as e:
                logging.exception('Problem updating CognateClasses '
                                  'in view_cladecognatesearch.')
                messages.error(request, 'Sorry, the server had problems '
                               'updating at least one entry: %s' % e)
        redirect_url = request.path
        if request.GET and 'clades' in request.GET:
            redirect_url += '?clades=%s' % request.GET['clades']
        return HttpResponseRedirect(redirect_url)
    # Acquiring meaningList:
    try:
        meaningList = MeaningList.objects.get(name=getDefaultWordlist(request))
    except meaningList.DoesNotExist:
        meaningList = MeaningList.objects.get(name=MeaningList.DEFAULT)
    # Acquiring languageList:
    try:
        languageList = LanguageList.objects.get(
            name=getDefaultLanguagelist(request))
    except LanguageList.DoesNotExist:
        languageList = LanguageList.objects.get(
            name=LanguageList.ALL)

    allClades = Clade.objects.all()

    # Figuring out clades to search for:
    currentClades = []
    includeMode = False
    if request.method == 'GET' and 'clades' in request.GET:
        cladeNames = [n.strip() for n in request.GET['clades'].split(',')]
        if 'nonunique' in cladeNames:
            includeMode = True
        currentClades = Clade.objects.filter(
            taxonsetName__in=cladeNames).all()

    # Searching cognateClassIds by clades:
    cognateClassIds = set()
    for clade in currentClades:
        newIds = CognateClass.objects.filter(
            lexeme__language__languageclade__clade=clade,
            lexeme__language__in=languageList.languages.all(),
            lexeme__meaning__in=meaningList.meanings.all()
        ).values_list('id', flat=True)
        if cognateClassIds:
            if includeMode:
                cognateClassIds.update(newIds)
            else:
                cognateClassIds &= set(newIds)
        else:
            cognateClassIds = set(newIds)

    # Removing unwanted entries from cognateClassIds:
    if currentClades:
        unwantedLanguages = languageList.languages.exclude(
            languageclade__clade__in=currentClades
        ).exclude(level0=0).values_list('id', flat=True)

        removeCognateClassIds = set(CognateClass.objects.filter(
            lexeme__language__in=unwantedLanguages,
            lexeme__meaning__in=meaningList.meanings.all()
        ).values_list('id', flat=True))

        cognateClassIds -= removeCognateClassIds

    # Form for cognateClasses:
    cognateClasses = CognateClass.objects.filter(
        id__in=cognateClassIds,
        lexeme__language__in=languageList.languages.all(),
        lexeme__meaning__in=meaningList.meanings.all()
    ).prefetch_related(
        'lexeme_set',
        'lexeme_set__language',
        'lexeme_set__meaning').distinct().all()
    for c in cognateClasses:
        c.computeCounts(languageList)
    form = AddCogClassTableForm(cogclass=cognateClasses)

    # Computing cladeLinks:
    def mkCladeLink(clade, currentTaxonsetNames, includeMode):
        targetSet = currentTaxonsetNames ^ set([clade.taxonsetName])
        if includeMode:
            targetSet.add('nonunique')
        return {'name': clade.shortName,
                'active': clade.taxonsetName in currentTaxonsetNames,
                'color': clade.hexColor,
                'href': '?clades=%s' % ','.join(targetSet)}
    currentTaxonsetNames = set([c.taxonsetName for c in currentClades])
    cladeLinks = [mkCladeLink(c, currentTaxonsetNames, includeMode)
                  for c in allClades
                  if c.shortName]
    if includeMode:
        cladeLinks.append({
            'name': 'Non-Unique Mode',
            'active': True,
            'color': '#999999',
            'href': '?clades=%s' % (','.join(currentTaxonsetNames))})
    else:
        cladeLinks.append({
            'name': 'Non-Unique Mode',
            'active': False,
            'color': '#999999',
            'href': '?clades=%s%s' % (','.join(currentTaxonsetNames), ',nonunique')})

    return render_template(
        request, "view_cladecognatesearch.html",
        {"cladeTitle": ", ".join([c.shortName for c in currentClades]),
         "cladeLinks": cladeLinks,
         "allClades": allClades,
         "AddCogClassTableForm": form})


def query_to_dicts(query_string, *query_args):
    cursor = connection.cursor()
    cursor.execute(query_string, query_args)
    col_names = list(map(str.upper, [desc[0] for desc in cursor.description]))
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = OrderedDict(zip(col_names, row))
        yield row_dict
    return

@user_passes_test(lambda u: u.is_staff)
@logExceptions
def view_csvExport(request):

    def modelToFieldnames(model):
        def isWantedField(field):
            if field.startswith('_'):
                return False
            return isinstance(getattr(model, field), DeferredAttribute)
        return [f for f in dir(model) if isWantedField(f)]

    def modelToDicts(querySet, fieldnames):
        return [{field: getattr(entry, field) for field in fieldnames}
                for entry in querySet.all()]

    if 'full' in request.GET:
        models = {Author: Author.objects,
                  Clade: Clade.objects,
                  CognateClass: CognateClass.objects,
                  CognateClassCitation: CognateClassCitation.objects,
                  CognateJudgement: CognateJudgement.objects,
                  CognateJudgementCitation: CognateJudgementCitation.objects,
                  Language: Language.objects,
                  LanguageClade: LanguageClade.objects,
                  LanguageList: LanguageList.objects,
                  LanguageListOrder: LanguageListOrder.objects,
                  Lexeme: Lexeme.objects,
                  LexemeCitation: LexemeCitation.objects,
                  Meaning: Meaning.objects,
                  MeaningList: MeaningList.objects,
                  MeaningListOrder: MeaningListOrder.objects,
                  SndComp: SndComp.objects,
                  Source: Source.objects}
    elif 'cognate' in request.GET:
        meaningListId = getDefaultWordlistId(request)
        languageListId = getDefaultLanguagelistId(request)
        models_org = list(query_to_dicts("""
SELECT *
FROM (
SELECT 
0 as ID, 
cj.cognate_class_id as COGID, 
cc.root_form as ROOT_FORM, 
cj.lexeme_id as LEXEME_ID, 
m.gloss as CONCEPT, 
l.phon_form as IPA,
l."phoneMic" as PHONEMIC, 
l.romanised as ROMANISED, 
lg.ascii_name as DOCULECT,
l.not_swadesh_term as NOT_TARGET
FROM 
lexicon_lexeme as l,
lexicon_cognatejudgement as cj,
lexicon_language as lg,
lexicon_meaning as m,
lexicon_cognateclass as cc

WHERE 
l.id = cj.lexeme_id AND 
l.language_id = lg.id AND 
l.meaning_id = m.id AND 
cj.cognate_class_id = cc.id AND
l.language_id in (
select language_id from lexicon_languagelistorder where language_list_id = %d) AND
l.meaning_id in (
select meaning_id from lexicon_meaninglistorder where meaning_list_id = %d) 

UNION

SELECT 
0 as ID, 
0 as COGID, 
'' as ROOT_FORM, 
l.id as LEXEME_ID, 
m.gloss as CONCEPT, 
l.phon_form as IPA,
l."phoneMic" as PHONEMIC, 
l.romanised as ROMANISED, 
lg.ascii_name as DOCULECT,
l.not_swadesh_term as NOT_TARGET
FROM 
lexicon_lexeme as l,
lexicon_language as lg,
lexicon_meaning as m

WHERE 
l.id not in (

SELECT 
cj.lexeme_id
FROM 
lexicon_lexeme as l,
lexicon_cognatejudgement as cj,
lexicon_language as lg,
lexicon_meaning as m,
lexicon_cognateclass as cc

WHERE 
l.id = cj.lexeme_id AND 
l.language_id = lg.id AND 
l.meaning_id = m.id AND 
cj.cognate_class_id = cc.id AND
l.language_id in (
SELECT language_id from lexicon_languagelistorder where language_list_id = %d) AND
l.meaning_id in (
SELECT meaning_id from lexicon_meaninglistorder where meaning_list_id = %d) 


) AND 
l.language_id = lg.id AND 
l.meaning_id = m.id AND 
l.language_id in (
SELECT language_id from lexicon_languagelistorder where language_list_id = %d) AND
l.meaning_id in (
SELECT meaning_id from lexicon_meaninglistorder where meaning_list_id = %d) 
) t
ORDER BY (doculect, concept)
        """ % ((languageListId,meaningListId) * 3)))

        zipBuffer = io.BytesIO()
        zipFile = zipfile.ZipFile(zipBuffer, 'w')

        filename = 'CoBL_export_%s/%s.csv' % (time.strftime("%Y-%m-%d"), 'cognates_all')
        if len(models_org) > 0:
            models = []
            cnt = 1
            for i in range(len(models_org)):
                r = copy.deepcopy(models_org[i])
                r["ID"] = cnt
                del r["NOT_TARGET"]
                models.append(r)
                cnt += 1
            fieldnames = models[0].keys()
            modelBuffer = io.StringIO()
            writer = csv.DictWriter(modelBuffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(models)
            zipFile.writestr(filename, modelBuffer.getvalue())

            models = []
            cnt = 1
            for i in range(len(models_org)):
                r = copy.deepcopy(models_org[i])
                if not r["NOT_TARGET"]:
                    r["ID"] = cnt
                    del r["NOT_TARGET"]
                    models.append(r)
                    cnt += 1
            filename = 'CoBL_export_%s/%s.csv' % (time.strftime("%Y-%m-%d"), 'cognates_only_target')
            modelBuffer = io.StringIO()
            writer = csv.DictWriter(modelBuffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(models)
            zipFile.writestr(filename, modelBuffer.getvalue())

        zipFile.close()

        resp = HttpResponse(zipBuffer.getvalue(),
                            content_type='application/x-zip-compressed')
        cdHeader = "attachment; filename=%s.export.zip" % time.strftime("%Y-%m-%d")
        resp['Content-Disposition'] = cdHeader
        return resp
    else:
        meaningList = getDefaultWordlist(request)
        languageList = getDefaultLanguagelist(request)
        models = {
            Author: Author.objects,
            Language: Language.objects.filter(
                languagelist__name=languageList),
            LanguageList: LanguageList.objects.filter(name=languageList),
            LanguageListOrder: LanguageListOrder.objects.filter(
                language_list__name=languageList),
            Meaning: Meaning.objects.filter(meaninglist__name=meaningList),
            MeaningList: MeaningList.objects.filter(name=meaningList),
            MeaningListOrder: MeaningListOrder.objects.filter(
                meaning_list__name=meaningList),
            SndComp: SndComp.objects,
            Source: Source.objects}
        models[Lexeme] = Lexeme.objects.filter(
            language__in=models[Language],
            meaning__in=models[Meaning])
        models[CognateJudgement] = CognateJudgement.objects.filter(
            lexeme__in=models[Lexeme])
        models[CognateClass] = CognateClass.objects.filter(
            lexeme__in=models[Lexeme])
        models[LexemeCitation] = LexemeCitation.objects.filter(
            lexeme__in=models[Lexeme])
        models[CognateJudgementCitation] = \
            CognateJudgementCitation.objects.filter(
                cognate_judgement__in=models[CognateJudgement])
        models[CognateClassCitation] = \
            CognateClassCitation.objects.filter(
                cognate_class__in=models[CognateClass])
        models[LanguageClade] = LanguageClade.objects.filter(
            language__in=models[Language])
        models[Clade] = Clade.objects.filter(
            languageclade__in=models[LanguageClade])

    zipBuffer = io.BytesIO()
    zipFile = zipfile.ZipFile(zipBuffer, 'w')
    for model, querySet in models.items():
        filename = 'CoBL_export_%s/%s.csv' % (time.strftime("%Y-%m-%d"), model.__name__)
        fieldnames = modelToFieldnames(model)
        modelBuffer = io.StringIO()
        writer = csv.DictWriter(modelBuffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(modelToDicts(querySet, fieldnames))
        zipFile.writestr(filename, modelBuffer.getvalue())
    zipFile.close()

    resp = HttpResponse(zipBuffer.getvalue(),
                        content_type='application/x-zip-compressed')
    cdHeader = "attachment; filename=%s.export.zip" % time.strftime("%Y-%m-%d")
    resp['Content-Disposition'] = cdHeader
    return resp


@user_passes_test(lambda u: u.is_staff)
@csrf_protect
@logExceptions
def viewProblematicRomanised(request):
    if request.method == 'POST':
        symbol = bytes(request.POST['symbol'], 'utf-8').decode('unicode_escape')
        if request.POST['action'] == 'add':
            rSymbol = RomanisedSymbol.objects.create(symbol=symbol)
            rSymbol.bump(request)
        elif request.POST['action'] == 'remove':
            RomanisedSymbol.objects.filter(symbol=symbol).delete()

    languageList = LanguageList.objects.get(name=getDefaultLanguagelist(request))
    meaningList = MeaningList.objects.get(name=getDefaultWordlist(request))
    lexemes = Lexeme.objects.filter(
        language__in=languageList.languages.all(),
        meaning__in=meaningList.meanings.all()).select_related('meaning')
    allowedSymbols = RomanisedSymbol.objects.all()
    okSet = set([allowed.symbol for allowed in allowedSymbols])

    offendingLexemes = []
    for lexeme in lexemes:
        offendingSymbols = set(lexeme.romanised) - okSet
        if offendingSymbols:
            lexeme.offendingSymbols = [
                RomanisedSymbol(symbol=o) for o in offendingSymbols]
            offendingLexemes.append(lexeme)

    return render_template(request, "problematicRomanised.html",
                           {"allowedSymbols": allowedSymbols,
                            "offendingLexemes": offendingLexemes})
