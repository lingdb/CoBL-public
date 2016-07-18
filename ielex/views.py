# -*- coding: utf-8 -*-
import bisect
import csv
import datetime
import json
import re
import requests
import textwrap
import time
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import redirect
from django.template import RequestContext
from django.template import Template
from django.template.loader import get_template
from reversion.models import Revision, Version
# from reversion import revision
from ielex.settings import LIMIT_TO, META_TAGS
from ielex.forms import *
from ielex.lexicon.models import *
from ielex.lexicon.defaultModels import *
# from ielex.citations.models import *
from ielex.extensional_semantics.views import *
from ielex.shortcuts import render_template
from ielex.utilities import next_alias, confirm_required, anchored, oneline
from ielex.languageCladeLogic import updateLanguageCladeRelations

from collections import defaultdict
from django.views.decorators.csrf import csrf_protect
from django_tables2 import RequestConfig
from ielex.tables import *
from werkzeug.datastructures import MultiDict
from itertools import izip_longest

# Refactoring:
# - rename the functions which render to response with the format
# view_TEMPLATE_NAME(request, ...). Put subsiduary functions under their main
# caller.

# -- Database input, output and maintenance functions ------------------------


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
    paginator = Paginator(recent_changes, 50)  # was 200

    try:  # Make sure page request is an int. If not, deliver first page.
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:  # If page request is out of range, deliver last page of results.
        changes = paginator.page(page)
    except (EmptyPage, InvalidPage):
        changes = paginator.page(paginator.num_pages)

    contributors = sorted([(User.objects.get(id=user_id),
                            Revision.objects.filter(user=user_id).count())
                           for user_id in Revision.objects.values_list("user",
                           flat=True).distinct() if user_id is not None],
                          lambda x, y: -cmp(x[1], y[1]))
    # reverse sort by second element in tuple
    # TODO user_id should never be None

    return render_template(request, "view_changes.html",
                           {"changes": changes,
                            "contributors": contributors})


@login_required
def revert_version(request, revision_id):
    """Roll back the object saved in a Version to the previous Version"""
    # TODO
    # - redirect this to somewhere more useful
    # - get the rollback revision and add a useful comment
    referer = request.META.get("HTTP_REFERER", "/")
    revision_obj = Revision.objects.get(pk=revision_id)
    revision_obj.revert()  # revert all associated objects too
    msg = "Rolled back revision %s" % (revision_obj.id)
    messages.add_message(request, messages.INFO, msg)
    return HttpResponseRedirect(referer)


def view_object_history(request, version_id):
    version = Version.objects.get(pk=version_id)
    obj = version.content_type.get_object_for_this_type(id=version.object_id)
    fields = [field.name for field in obj._meta.fields]
    versions = [[v.field_dict[f] for f in fields]+[v.id] for v in
                Version.objects.get_for_object(obj).order_by(
                    "revision__date_created")]
    return render_template(request, "view_object_history.html",
                           {"object": obj,
                            "versions": versions,
                            "fields": fields})


# -- General purpose queries and functions -----------------------------------

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
                    messages.add_message(
                        request, messages.INFO,
                        ("There are multiple languages matching"
                         " '%s' in the database") % language)
                raise Http404
            except Language.DoesNotExist:
                if request:
                    messages.add_message(
                        request, messages.INFO,
                        ("There is no language named or starting"
                         " with '%s' in the database") % language)
                raise Http404
    return language


def get_prev_and_next_languages(request, current_language, language_list=None):
    if language_list is None:
        language_list = LanguageList.objects.get(
            name=getDefaultLanguagelist(request))
    elif type(language_list) == str or type(language_list) == unicode:
        language_list = LanguageList.objects.get(name=language_list)

    ids = list(language_list.languages.values_list("id", flat=True))

    try:
        current_idx = ids.index(current_language.id)
    except ValueError:
        current_idx = 0
    prev_language = Language.objects.get(id=ids[current_idx-1])
    try:
        next_language = Language.objects.get(id=ids[current_idx+1])
    except IndexError:
        next_language = Language.objects.get(id=ids[0])
    return (prev_language, next_language)


def get_prev_and_next_meanings(request, current_meaning, meaning_list=None):
    if meaning_list is None:
        meaning_list = MeaningList.objects.get(
            name=getDefaultWordlist(request))
    elif type(meaning_list) == str or type(meaning_list) == unicode:
        meaning_list = MeaningList.objects.get(name=meaning_list)
    meanings = list(meaning_list.meanings.all().order_by("meaninglistorder"))

    ids = [m.id for m in meanings]
    try:
        current_idx = ids.index(current_meaning.id)
    except ValueError:
        current_idx = 0
    if len(meanings) == 0:
        return (current_meaning, current_meaning)
    try:
        prev_meaning = meanings[current_idx-1]
    except IndexError:
        prev_meaning = meanings[len(meanings) - 1]
    try:
        next_meaning = meanings[current_idx+1]
    except IndexError:
        next_meaning = meanings[0]
    return (prev_meaning, next_meaning)


def get_prev_and_next_lexemes(request, current_lexeme):
    """Get the previous and next lexeme from the same language, ordered
    by meaning and then alphabetically by form"""
    current_meaning = current_lexeme.meaning
    lexemes = list(Lexeme.objects.filter(
        language=current_lexeme.language).order_by(
            "meaning", "phon_form", "source_form", "id"))
    ids = [l.id for l in lexemes]
    try:
        current_idx = ids.index(current_lexeme.id)
    except ValueError:
        current_idx = 0
    prev_lexeme = lexemes[current_idx-1]
    try:
        next_lexeme = lexemes[current_idx+1]
    except IndexError:
        next_lexeme = lexemes[0]
    return (prev_lexeme, next_lexeme)


def update_object_from_form(model_object, form):
    """Update an object with data from a form."""
    # XXX This is only neccessary when not using a model form: otherwise
    # form.save() does all this automatically
    # TODO Refactor this function away
    assert set(form.cleaned_data).issubset(set(model_object.__dict__))
    model_object.__dict__.update(form.cleaned_data)
    model_object.save()

# -- /language(s)/ ----------------------------------------------------------


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
            messages.add_message(
                request, messages.INFO,
                ("There is no language list matching"
                 " '%s' in the database") % language_list)
        raise Http404
    return language_list


@csrf_protect
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
        except Exception, e:
            print('Exception in POST  validation: ', e)
            messages.error(request, 'Sorry, the form data sent '
                           'did not pass server side validation.')
            return HttpResponseRedirect(
                reverse("view-language-list", args=[current_list.name]))
        # Languages that may need clade updates:
        updateClades = []
        # Iterating form to update languages:
        for entry in languageListTableForm.langlist:
            data = entry.data
            try:
                lang = Language.objects.get(id=data['idField'])
                if lang.isChanged(**data):
                    try:
                        problem = lang.setDelta(request, **data)
                        if problem is None:
                            lang.save()
                            # Making sure we update clades
                            # for changed languages:
                            updateClades.append(lang)
                        else:
                            messages.error(request,
                                           lang.deltaReport(**problem))
                    except Exception, e:
                        print('Exception while saving POST: ', e)
                        messages.error(request, 'Sorry, the server failed '
                                       'to save "%s".' % data['ascii_name'])
            except Exception, e:
                print('Exception while accessing Language object: ',
                      e, '; POST items are: ', data)
                messages.error(request, 'Sorry, the server had problems '
                               'saving at least one language entry.')
        # Updating clade relations for changes languages:
        if len(updateClades) > 0:
            updateLanguageCladeRelations(languages=updateClades)
        # Redirecting so that UA makes a GET.
        return HttpResponseRedirect(
            reverse("view-language-list", args=[current_list.name]))
    elif (request.method == 'POST') and ('cloneLanguage' in request.POST):
        # Cloning language and lexemes:
        form = CloneLanguageForm(request.POST)
        try:
            form.validate()
            with transaction.atomic():
                # Creating language clone:
                clone = Language(ascii_name=form.data['languageName'],
                                 utf8_name=form.data['languageName'])
                clone.bump(request)
                clone.save()
                # Adding language to current language list, if not viewing all:
                if current_list.name != LanguageList.ALL:
                    current_list.append(clone)
                # Wordlist to use:
                meaningIds = MeaningListOrder.objects.filter(
                    meaning_list__name=getDefaultWordlist(request)
                    ).values_list(
                    "meaning_id", flat=True)
                # Lexemes to copy:
                sourceLexemes = Lexeme.objects.filter(
                    language__ascii_name=form.data['sourceLanguageName'],
                    meaning__in=meaningIds).all(
                    ).prefetch_related('meaning')
                # Copy lexemes to clone language:
                newLexemes = []
                order = 1  # Increasing values for _order fields of Lexemes
                for sLexeme in sourceLexemes:
                    # Basic data:
                    data = {'language': clone,
                            'meaning': sLexeme.meaning,
                            '_order': order}
                    order += 1
                    # Copying lexeme data if specified:
                    if not form.data['emptyLexemes']:
                        for f in sLexeme.timestampedFields():
                            data[f] = getattr(sLexeme, f)
                    # Setting lastEditedBy:
                    data['lastEditedBy'] = ' '.join(
                        [request.user.first_name,
                         request.user.last_name])
                    # Appending for creation:
                    newLexemes.append(Lexeme(**data))
                Lexeme.objects.bulk_create(newLexemes)
                # Redirect to newly created language:
                messages.success(request, 'Language cloned.')
                return HttpResponseRedirect(
                    reverse("view-language-list", args=[current_list.name]))
        except Exception, e:
            print('Problem cloning Language:', e)
            messages.error(request, 'Sorry, a problem occured '
                           'when cloning the language.')
            return HttpResponseRedirect(
                reverse("view-language-list", args=[current_list.name]))
    elif (request.method == 'GET') and ('exportCsv' in request.GET):
        # Handle csv export iff desired:
        return exportLanguageListCsv(request, languages)

    meaningList = MeaningList.objects.get(name=getDefaultWordlist(request))
    languages_editabletable_form = AddLanguageListTableForm()
    for lang in languages:
        lang.idField = lang.id
        lang.computeCounts(meaningList)
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
def exportLanguageListCsv(request, languages=[]):
    """
      @param languages :: [Language]
    """
    fields = request.GET['exportCsv'].split(',')
    rows = [l.getCsvRow(*fields) for l in languages]
    rows.insert(0, ['"'+f+'"' for f in fields])  # Add headline
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
                idCladeMap = {c.id: c for c in Clade.objects.all()}
                for entry in cladeTableForm.elements:
                    data = entry.data
                    try:
                        clade = idCladeMap[data['idField']]
                        if clade.isChanged(**data):
                            problem = clade.setDelta(request, **data)
                            if problem is None:
                                with transaction.atomic():
                                    clade.save()
                                    cladeChanged = True
                            else:
                                messages.error(
                                    request, clade.deltaReport(**problem))
                    except Exception, e:
                        print('Problem while saving clade: ', e)
                        messages.error(request,
                                       'Problem saving clade data: %s' % data)
            except Exception, e:
                print('Problem updating clades:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'updating at least on clade.')
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
            except Exception, e:
                print('Problem creating clade:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'creating the clade.')
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
            except Exception, e:
                print('Problem deleting clade:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'deleting the clade.')
        return HttpResponseRedirect('/clades/')

    form = CladeTableForm()
    for clade in Clade.objects.all():
        clade.idField = clade.id
        form.elements.append_entry(clade)

    return render_template(request,
                           "clades.html",
                           {'clades': form})


@csrf_protect
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
                            except Exception, e:
                                print('Exception while saving POST:', e)
                                messages.error(request, 'The server had '
                                               'problems saving the change '
                                               'to "%s".' % sndComp.lgSetName)
                except Exception, e:
                    print('Exception while accessing SndComp object: ',
                          e, '; POST items are: ', data)
                    messages.error(request, 'Sorry, the server had problems '
                                   'saving at least one SndComp entry.')
        # Adding a new SndComp:
        elif 'addSndComp' in request.POST:
            sndCompCreationForm = SndCompCreationForm(request.POST)
            try:
                sndCompCreationForm.validate()
                newSndComp = SndComp(**sndCompCreationForm.data)
                with transaction.atomic():
                    newSndComp.save(force_insert=True)
            except Exception, e:
                print('Problem creating SndComp:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'creating the SndComp language set.')
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
            except Exception, e:
                print('Problem deleting SndComp:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'deleting the SndComp language set.')

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
            # TODO might be good to zap the session variable once finished
            # request.session["current_meaning_id"] = None
            return HttpResponseRedirect(
                reverse("view-language-list",
                        args=[language_list.name]))
    else:  # first visit
        form = ReorderForm(initial={"language": language_id})
    return render_template(
        request, "reorder_language_list.html",
        {"language_list": language_list, "form": form})


def move_language(language, language_list, direction):
    assert direction in (-1, 1)
    languages = list(language_list.languages.order_by("languagelistorder"))
    index = languages.index(language)
    if index == 0 and direction == -1:
        language_list.remove(language)
        language_list.append(language)
    else:
        try:
            neighbour = languages[index+direction]
            language_list.swap(language, neighbour)
        except IndexError:
            language_list.insert(0, language)


@csrf_protect
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
                lexemesTableForm = LexemeTableLanguageWordlistForm(
                    request.POST)
                lexemesTableForm.validate()

                for entry in lexemesTableForm.lexemes:
                    data = entry.data
                    # Updating the lexeme:
                    try:
                        with transaction.atomic():
                            lex = Lexeme.objects.get(id=data['id'])
                            if lex.isChanged(**data):
                                problem = lex.setDelta(request, **data)
                                if problem is None:
                                    lex.save()
                                else:
                                    messages.error(
                                        request, lex.deltaReport(**problem))
                    except Exception, e:
                        print('Exception for updating Lexeme:', e)
                        messages.error(request, 'Sorry, the server could '
                                       'not update lexeme %s.' % lex.gloss)
            except Exception, e:
                print('Problem updating lexemes:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'updating at least one lexeme.')
            return HttpResponseRedirect(
                reverse("view-language-wordlist",
                        args=[language.ascii_name, wordlist.name]))

    # collect data
    lexemes = Lexeme.objects.filter(
        language=language,
        meaning__in=wordlist.meanings.all()
        ).select_related(
        "meaning").order_by(
        "meaning__gloss").prefetch_related(
        "cognatejudgement_set",
        "cognatejudgement_set__cognatejudgementcitation_set",
        "cognate_class", "lexemecitation_set")

    # TODO: move this out of views
    # filter by 'language' or 'meaning'
    filt_form = LexemeTableFilterForm(request.GET)
    if filt_form.is_valid():
        if request.GET.get('meaning'):
            lexemes = lexemes.filter(meaning=int(request.GET.get('meaning')))
        if request.GET.get('cognate_class'):
            print 'cognate_class:', request.GET  # .get('cognate_class')
            lexemes = lexemes.filter(
                cognate_class=request.GET.get('cognate_class'))

    lexemes_editabletable_form = LexemeTableLanguageWordlistForm()
    for lex in lexemes:
        lex.rfcWebPath1 = language.rfcWebPath1
        lex.rfcWebPath2 = language.rfcWebPath2
        lexemes_editabletable_form.lexemes.append_entry(lex)

    otherMeaningLists = MeaningList.objects.exclude(id=wordlist.id).all()

    languageList = LanguageList.objects.prefetch_related('languages').get(
        name=getDefaultLanguagelist(request))
    typeahead = json.dumps({l.utf8_name: reverse(
        "view-language-wordlist", args=[l.ascii_name, wordlist.name])
        for l in languageList.languages.all()})

    prev_language, next_language = \
        get_prev_and_next_languages(request, language,
                                    language_list=languageList)
    return render_template(request, "language_wordlist.html",
                           {"language": language,
                            "lexemes": lexemes,
                            "prev_language": prev_language,
                            "next_language": next_language,
                            "wordlist": wordlist,
                            "otherMeaningLists": otherMeaningLists,
                            'lex_ed_form': lexemes_editabletable_form,
                            'filt_form': filt_form,
                            'typeahead': typeahead})


@login_required
def view_language_check(request, language=None, wordlist=None):
    '''
    Provides an html snipped that contains some sanity checks
    for a given language against a given wordlist.
    If language or wordlist are omitted they are inferred vie defaultModels.
    This function is a result of #159.
    @param language :: str | unicode | None
    @param wordlist :: str | unicode | None
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
            return HttpResponseRedirect(reverse("edit-language-list",
                                        args=[form.cleaned_data["name"]]))
    else:
        form = AddLanguageListForm()
    return render_template(request, "add_language_list.html",
                           {"form": form})


@login_required
def edit_language_list(request, language_list=None):
    language_list = get_canonical_language_list(
        language_list, request)  # a language list object
    language_list_all = get_canonical_language_list()  # a language list object
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
            else:  # changed name
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
def delete_language_list(request, language_list):
    language_list = LanguageList.objects.get(name=language_list)
    language_list.delete()
    return HttpResponseRedirect(reverse("view-all-languages"))


@login_required
def language_add_new(request, language_list):
    language_list = LanguageList.objects.get(name=language_list)
    if request.method == 'POST':
        form = EditLanguageForm(request.POST)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-language-list",
                                        args=[language_list.name]))
        if form.is_valid():
            form.save()
            language = Language.objects.get(
                    ascii_name=form.cleaned_data["ascii_name"])
            try:
                language_list.insert(0, language)
            except IntegrityError:
                pass  # automatically inserted into LanguageList.DEFAULT
            return HttpResponseRedirect(reverse("language-report",
                                        args=[language.ascii_name]))
    else:  # first visit
        form = EditLanguageForm()
    return render_template(request, "language_add_new.html",
                           {"form": form})


@login_required
def edit_language(request, language):
    try:
        language = Language.objects.get(ascii_name=language)
    except Language.DoesNotExist:
        language = get_canonical_language(language, request)
        return HttpResponseRedirect(reverse("language-edit",
                                    args=[language.ascii_name]))

    if request.method == 'POST':
        form = LanguageListRowForm(request.POST)
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
        except Exception, e:
            print('Problem updating single language:', e)
            messages.error(request, 'Sorry, the server could not update '
                           'the language.')
    language.idField = language.id
    form = LanguageListRowForm(obj=language)

    return render_template(request, "language_edit.html",
                           {"language": language,
                            "form": form})


@login_required
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


def view_wordlists(request):
    wordlists = MeaningList.objects.all()
    return render_template(request, "wordlists_list.html",
                           {"wordlists": wordlists})


@csrf_protect
def view_wordlist(request, wordlist=MeaningList.DEFAULT):
    try:
        wordlist = MeaningList.objects.get(name=wordlist)
    except MeaningList.DoesNotExist:
        raise Http404("MeaningList '%s' does not exist" % wordlist)
    setDefaultWordlist(request, wordlist.name)
    if request.method == 'POST':
        if 'wordlist' in request.POST:
            mltf = MeaningListTableForm(request.POST)
            ms = [m.data for m in mltf.meanings]
            for m in ms:
                try:
                    meaning = Meaning.objects.get(id=m['meaningId'])
                    if meaning.isChanged(**m):
                        try:
                            problem = meaning.setDelta(request, **m)
                            if problem is None:
                                meaning.save()
                            else:
                                messages.error(
                                    request, meaning.deltaReport(**problem))
                        except Exception, e:
                            print('Exception while saving POST: ', e)
                            messages.error(request, 'Sorry, the server had '
                                           'problems saving changes for '
                                           '"%s".' % meaning.gloss)
                except Exception, e:
                    print('Exception while accessing Meaning object: ',
                          e, '; POST items are: ', m)
                    messages.error(request, 'The server had problems saving '
                                   'at least one entry.')

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
            # TODO might be good to zap the session variable once finished
            # request.session["current_meaning_id"] = None
            return HttpResponseRedirect(reverse("view-wordlist",
                                        args=[wordlist.name]))
    else:  # first visit
        form = ReorderForm(initial={"meaning": meaning_id})
    return render_template(request, "reorder_wordlist.html",
                           {"wordlist": wordlist, "form": form})


def move_meaning(meaning, wordlist, direction):
    assert direction in (-1, 1)
    meanings = list(wordlist.meanings.all().order_by("meaninglistorder"))
    index = meanings.index(meaning)
    if index == 0 and direction == -1:
        wordlist.remove(meaning)
        wordlist.append(meaning)
    else:
        try:
            neighbour = meanings[index+direction]
            wordlist.swap(meaning, neighbour)
        except IndexError:
            wordlist.insert(0, meaning)


@login_required
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


@csrf_protect
def view_meaning(request, meaning, language_list, lexeme_id=None):
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

                for entry in lexemesTableForm.lexemes:
                    data = entry.data
                    # Updating the cognate classes:
                    try:
                        for cData in data['allCognateClasses']:
                            cc = CognateClass.objects.get(id=cData['idField'])
                            if cc.isChanged(**cData):
                                problem = cc.setDelta(request, **cData)
                                if problem is None:
                                    cc.save()
                                else:
                                    messages.error(
                                        request, cc.deltaReport(**problem))
                    except Exception, e:
                        print('Exception for updating CognateClass:', e)
                    # Updating the lexeme:
                    try:
                        lex = Lexeme.objects.get(id=data['id'])
                        if lex.isChanged(**data):
                            problem = lex.setDelta(request, **data)
                            if problem is None:
                                lex.save()
                            else:
                                messages.error(request,
                                               lex.deltaReport(**problem))
                    except Exception, e:
                        print('Exception for updating Lexeme:', e)
            except Exception, e:
                print('Problem updating lexemes:', e)

            return HttpResponseRedirect(
                reverse("view-meaning-languages",
                        args=[canonical_gloss, current_language_list.name]))
        elif 'createCognateClass' in request.POST:
            try:
                form = LexemeTableCreateCognateClassForm(request.POST)
                form.validate()
                lexemeIds = set([int(i) for i in
                                 form.data['lexemeIds'].split(',')])
                newC = CognateClass()
                newC.bump(request)
                newC.save()
                CognateJudgement.objects.bulk_create([
                    CognateJudgement(lexeme_id=lId, cognate_class_id=newC.id)
                    for lId in lexemeIds])
                newC.update_alias()
                messages.success(request, 'Create Cognate Class %s with id %i.'
                                 % (newC.alias, newC.id))
            except Exception, e:
                print('Exception when creating a cognate class:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'creating the new cognate class.')

            return HttpResponseRedirect(
                reverse("view-meaning-languages",
                        args=[canonical_gloss, current_language_list.name]))
        # Handling ChooseCognateClassForm:
        else:  # not ('meang_form' in request.POST)
            cognate_form = ChooseCognateClassForm(request.POST)
            if cognate_form.is_valid():
                cd = cognate_form.cleaned_data
                cognate_class = cd["cognate_class"]
                # if not cogjudge_id: # new cognate judgement
                lexeme = Lexeme.objects.get(id=lexeme_id)
                if cognate_class not in lexeme.cognate_class.all():
                    cj = CognateJudgement.objects.create(
                            lexeme=lexeme,
                            cognate_class=cognate_class)
                else:
                    cj = CognateJudgement.objects.get(
                            lexeme=lexeme,
                            cognate_class=cognate_class)

                # change this to a reverse() pattern
                return HttpResponseRedirect(anchored(
                        reverse("lexeme-add-cognate-citation",
                                args=[lexeme_id, cj.id])))

    # Gather lexemes:
    lexemes = Lexeme.objects.filter(
        meaning=meaning,
        language__in=current_language_list.languages.all(),
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

    cognate_form = ChooseCognateClassForm()
    cognate_form.fields[
        "cognate_class"].queryset = CognateClass.objects.filter(
            lexeme__in=lexemes).distinct()

    # TODO: move this out of views
    # filter by 'language' or 'meaning'
    filt_form = MeaningTableFilterForm(request.GET)
    if filt_form.is_valid():
        if request.GET.get('language'):
            lexemes = lexemes.filter(language=request.GET.get('language'))
    # TODO: suppress errorlist with error
    # "This field is required.", but only here:
    # Here this is not needed.
    filt_form.errors['language'] = ''
    # Fill lexemes_editabletable_form:
    lexemes_editabletable_form = LexemeTableViewMeaningsForm()
    for lex in lexemes:
        lexemes_editabletable_form.lexemes.append_entry(lex)
    # Fetch meaningList:
    meaningList = MeaningList.objects.prefetch_related("meanings").get(
        name=getDefaultWordlist(request))
    # Compute typeahead:
    typeahead = json.dumps({m.gloss: reverse(
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
         "add_cognate_judgement": lexeme_id,
         "lex_ed_form": lexemes_editabletable_form,
         "filt_form": filt_form,
         "typeahead": typeahead,
         "clades": Clade.objects.all()})


@csrf_protect
def view_cognateclasses(request, meaning):
    setDefaultMeaning(request, meaning)
    # Handle POST of AddCogClassTableForm:
    if request.method == 'POST':
        if 'cogclass_form' in request.POST:
            try:
                cogClassTableForm = AddCogClassTableForm(request.POST)
                cogClassTableForm.validate()
                # Iterate entries that may be changed:
                for entry in cogClassTableForm.cogclass:
                    data = entry.data
                    cogclass = CognateClass.objects.get(
                        id=int(data['idField']))
                    # Check if entry changed and try to update:
                    if cogclass.isChanged(**data):
                        try:
                            problem = cogclass.setDelta(request, **data)
                            if problem is None:
                                cogclass.save()
                            else:
                                messages.error(
                                    request, cogclass.deltaReport(**problem))
                        except Exception, e:
                            print('Exception while saving CognateClass:', e)
                            messages.error(
                                request,
                                'Problem while saving entry: %s' % data)
            except Exception, e:
                print('Problem updating cognateclasses:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'updating at least one entry.')
        elif 'mergeCognateClasses' in request.POST:
            try:
                # Parsing and validating data:
                mergeCCForm = MergeCognateClassesForm(request.POST)
                mergeCCForm.validate()
                # Extract ids from form:
                ids = set([int(i) for i in
                           mergeCCForm.data['mergeIds'].split(',')])
                # Fetching classes to merge:
                ccs = CognateClass.objects.filter(
                    id__in=ids).prefetch_related(
                    "cognatejudgement_set",
                    "cognateclasscitation_set").all()
                # Checking ccs length:
                if len(ccs) <= 1:
                    print('Not enough cognateclasses to merge.')
                    messages.error(request, 'Sorry, the server needs '
                                   '2 or more cognateclasses to merge.')
                else:
                    # Merging ccs:
                    with transaction.atomic():
                        # Creating new CC with merged field contents:
                        newC = CognateClass()
                        setDict = {'notes': set(),
                                   'root_form': set(),
                                   'root_language': set(),
                                   'gloss_in_root_lang': set(),
                                   'loan_source': set(),
                                   'loan_notes': set()}
                        for cc in ccs:
                            for k, v in cc.toDict().iteritems():
                                if k in setDict:
                                    setDict[k].add(v)
                        delta = {k: '{'+', '.join(v)+'}'
                                 for k, v in setDict.iteritems()}
                        for k, v in delta.iteritems():
                            setattr(newC, k, v)
                        newC.bump(request)
                        newC.save()
                        # Retargeting CJs:
                        cjIds = set()
                        for cc in ccs:
                            cjIds.update([cj.id for cj
                                          in cc.cognatejudgement_set.all()])
                        CognateJudgement.objects.filter(
                            id__in=cjIds).update(
                            cognate_class_id=newC.id)
                        # Retargeting CCCs:
                        cccIds = set()
                        for cc in ccs:
                            cccIds.update([ccc.id for ccc in
                                           cc.cognateclasscitation_set.all()])
                        CognateClassCitation.objects.filter(
                            id__in=cccIds).update(
                            cognate_class_id=newC.id)
                        # Deleting old ccs:
                        ccs.delete()
                        # Fixing alias:
                        newC.update_alias()
            except Exception, e:
                print('Problem merging cognateclasses:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'merging cognate classes.')
        else:
            print('Unexpected POST request in view_cognateclasses.')
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

    languageIds = languageList.languagelistorder_set.values_list(
        'language_id', flat=True)
    ccl_ordered = CognateClass.objects.filter(
        cognatejudgement__lexeme__meaning__gloss=meaning,
        cognatejudgement__lexeme__language_id__in=languageIds
            ).order_by('alias').distinct()

    def cmpLen(x, y):  # Fixing sort order for #98
        return len(x.alias) - len(y.alias)
    ccl_ordered = sorted(ccl_ordered, cmp=cmpLen)

    # Clades to use for #112:
    clades = Clade.objects.filter(
        id__in=LanguageClade.objects.filter(
            language__languagelistorder__language_list=languageList
            ).values_list('clade_id', flat=True)).exclude(
            hexColor='').exclude(shortName='').all()
    # Compute clade <-> cc connections:
    for c in clades:
        c.computeCognateClassConnections(ccl_ordered)
    # Filling cogclass_editabletable_form:
    cogclass_editabletable_form = AddCogClassTableForm()
    for cc in ccl_ordered:
        cc.computeCounts(languageList=languageList)
        cogclass_editabletable_form.cogclass.append_entry(cc)
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


def view_lexeme(request, lexeme_id):
    """For un-logged-in users, view only"""
    try:
        lexeme = Lexeme.objects.get(id=lexeme_id)
    except Lexeme.DoesNotExist:
        messages.add_message(request, messages.INFO,
                             "There is no lexeme with id=%s" % lexeme_id)
        raise Http404
    prev_lexeme, next_lexeme = get_prev_and_next_lexemes(request, lexeme)
    return render_template(request, "lexeme_report.html",
                           {"lexeme": lexeme,
                            "prev_lexeme": prev_lexeme,
                            "next_lexeme": next_lexeme})


@login_required
def lexeme_edit(request, lexeme_id, action="", citation_id=0, cogjudge_id=0):
    try:
        lexeme = Lexeme.objects.get(id=lexeme_id)
    except Lexeme.DoesNotExist:
        messages.add_message(request, messages.INFO,
                             "There is no lexeme with id=%s" % lexeme_id)
        raise Http404
    citation_id = int(citation_id)
    cogjudge_id = int(cogjudge_id)
    form = None

    def DELETE_CITATION_WARNING_MSG():
        messages.add_message(
            request,
            messages.WARNING,
            oneline("""Deletion of the final citation is not allowed. If
            you need to, add a new one before deleting the current
            one."""))

    def DELETE_COGJUDGE_WARNING_MSG(citation):
        msg = Template(oneline("""Deletion of final cognate citation is not
            allowed (Delete the cognate class {{ alias }} itself
            instead, if that's what you mean)"""))
        context = RequestContext(request)
        context["alias"] = citation.cognate_judgement.cognate_class.alias
        messages.add_message(
            request,
            messages.WARNING,
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
                messages.add_message(request, messages.WARNING,
                                     msg.render(context))

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
                        reliability=cd["reliability"],
                        comment=cd["comment"])
                    try:
                        citation.save()
                    except IntegrityError:
                        messages.add_message(
                            request,
                            messages.WARNING,
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
                return HttpResponseRedirect(redirect_url)
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
                    update_object_from_form(citation, form)  # XXX refactor
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
                # initial={"source_form":lexeme.source_form,
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
                    # "comment":citation.comment})
                except LexemeCitation.DoesNotExist:
                    form = AddCitationForm()
            # elif action == "add-new-citation":# XXX
            #     form = AddCitationForm()
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
                redirect_url = reverse("meaning-report",
                                       args=[lexeme.meaning.gloss])
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
def lexeme_duplicate(request, lexeme_id):
    """Useful for processing imported data; currently only available
    through direct url input, e.g. /lexeme/0000/duplicate/"""
    original_lexeme = Lexeme.objects.get(id=int(lexeme_id))
    SPLIT_RE = re.compile("[,;]")   # split on these characters
    done_split = False

    if SPLIT_RE.search(original_lexeme.source_form):
        original_source_form, new_source_form = [
            e.strip() for e in SPLIT_RE.split(original_lexeme.source_form, 1)]
        done_split = True
    else:
        original_source_form, new_source_form = original_lexeme.source_form, ""

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
            source_form=new_source_form,
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

        original_lexeme.source_form = original_source_form
        original_lexeme.phon_form = original_phon_form
        original_lexeme.save()
    redirect_to = "%s#lexeme_%s" % (
        reverse("meaning-report",
                args=[original_lexeme.meaning.gloss]),
        original_lexeme.id)
    return HttpResponseRedirect(redirect_to)


@login_required
def lexeme_add(request,
               meaning=None,
               language=None,
               return_to=None):
    initial_data = {}
    if language:
        initial_data["language"] = get_canonical_language(language, request)
    if meaning:
        initial_data["meaning"] = get_canonical_meaning(meaning)

    if request.method == "POST":
        form = AddLexemeForm(request.POST)
        if "cancel" in form.data:  # has to be tested before data is cleaned
            if "language" in initial_data:
                initial_data["language"] = initial_data["language"].ascii_name
            if "meaning" in initial_data:
                initial_data["meaning"] = initial_data["meaning"].gloss
            return HttpResponseRedirect(return_to % initial_data)
        if form.is_valid():
            lexeme = Lexeme.objects.create(**form.cleaned_data)
            previous_citation_id = request.session.get("previous_citation_id")
            try:
                previous_citation = \
                        LexemeCitation.objects.get(id=previous_citation_id)
                LexemeCitation.objects.create(
                        lexeme=lexeme,
                        source=previous_citation.source,
                        pages=previous_citation.pages,
                        reliability=previous_citation.reliability)
                return HttpResponseRedirect(reverse("view-lexeme",
                                            args=[lexeme.id]))
            except LexemeCitation.DoesNotExist:
                return HttpResponseRedirect(reverse("lexeme-add-citation",
                                            args=[lexeme.id]))
    else:
        form = AddLexemeForm()
        try:
            form.fields["language"].initial = initial_data["language"].id
        except KeyError:
            pass
        try:
            form.fields["meaning"].initial = initial_data["meaning"].id
        except KeyError:
            pass
    return render_template(request, "lexeme_add.html",
                           {"form": form})


def redirect_lexeme_citation(request, lexeme_id):
    """From a lexeme, redirect to the first citation"""
    lexeme = Lexeme.objects.get(id=lexeme_id)
    try:
        first_citation = lexeme.lexemecitation_set.all()[0]
        return HttpResponseRedirect(redirect("lexeme-citation-detail",
                                    args=[first_citation.id]))
    except IndexError:
        msg = "Operation failed: this lexeme has no citations"
        messages.add_message(request, messages.WARNING, msg)
        return HttpResponseRedirect(lexeme.get_absolute_url())


# -- /cognate/ ------------------------------------------------------------


def cognate_report(request, cognate_id=0, meaning=None, code=None,
                   cognate_name=None, action=""):

    form_dict = {
        "edit-name": EditCognateClassNameForm,
        "edit-notes": EditCognateClassNotesForm
        }
    if cognate_id:
        cognate_class = CognateClass.objects.get(id=int(cognate_id))
    elif cognate_name:
        cognate_class = CognateClass.objects.get(name=cognate_name)
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
            msg = oneline(msg)
            messages.add_message(request, messages.INFO, msg)
            return HttpResponseRedirect(reverse('meaning-report',
                                        args=[meaning]))

    # Handling of CognateJudgementSplitTable:
    if request.method == 'POST':
        if 'cognateJudgementSplitTable' in request.POST:
            form = CognateJudgementSplitTable(request.POST)
            try:
                form.validate()
                # Gathering data to operate on:
                idTMap = {j.data['idField']: j.data['lastTouched']
                          for j in form.judgements
                          if j.data['splitOff']}
                idCjMap = {cj.id: cj for cj in
                           CognateJudgement.objects.filter(
                               id__in=idTMap.keys()).all()}
                # Bumping judgements:
                bumped = True
                try:
                    for id, t in idTMap.iteritems():
                        idCjMap[id].bump(request, t)
                except Exception, e:
                    print('Problem splitting cognate judgements:', e)
                    messages.error(request, 'The server refused to split '
                                   'the cognate judgements, because someone '
                                   'changed one of them before your request.')
                    bumped = False
                # Create new CognateClass on successful bump:
                if bumped:
                    cc = CognateClass()
                    try:
                        cc.save()
                        for _, cj in idCjMap.iteritems():
                            cj.cognate_class = cc
                            cj.save()
                        cc.update_alias()
                        messages.success(
                            request,
                            'Created new Cognate Class at '
                            '[%s](/cognate/%s/) containing the judgements %s.'
                            % (cc.id, cc.id, idTMap.keys()))
                    except Exception, e:
                        print('Problem creating a new '
                              'cognate class on split:', e)
                        messages.error(request, 'Sorry the server could not '
                                       'create a new cognate class.')
            except Exception, e:
                print('Problem when splitting cognate classes:', e)
                messages.error(request, 'Sorry, the server had trouble '
                               'understanding the request.')
        elif 'deleteCognateClass' in request.POST:
            try:
                cognate_class.delete()
                messages.success(request, 'Deleted cognate class.')
                return HttpResponseRedirect('/cognateclasslist/')
            except Exception, e:
                print('Failed to delete cognate class %s.' % cognate_class.id)
                messages.error(request, 'Sorry, the server could not delete '
                               'the requested cognate class %s.'
                               % cognate_class.id)
        elif 'deleteCitation' in request.POST:
            try:
                citation = CognateClassCitation.objects.get(
                    id=int(request.POST['citationId']))
                citation.delete()
                messages.success(request, 'Deleted citation.')
            except Exception, e:
                print('Failed to delete citation.', e)
                messages.error(request, 'Sorry, the server could not delete '
                               'the citation.')

    if action in ["edit-notes", "edit-name"]:
        if request.method == 'POST':
            form = form_dict[action](request.POST, instance=cognate_class)
            if "cancel" in form.data:
                return HttpResponseRedirect(reverse('cognate-set',
                                            args=[cognate_class.id]))
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('cognate-set',
                                            args=[cognate_class.id]))
        else:
            form = form_dict[action](instance=cognate_class)
    else:
        form = None

    language_list = LanguageList.objects.get(
        name=getDefaultLanguagelist(request))
    splitTable = CognateJudgementSplitTable()
    # for language_id in language_list.language_id_list:
    ordLangs = language_list.languages.all().order_by("languagelistorder")
    for language in ordLangs:
        for cj in cognate_class.cognatejudgement_set.filter(
                 lexeme__language=language).all():
            cj.idField = cj.id
            splitTable.judgements.append_entry(cj)

    return render_template(request, "cognate_report.html",
                           {"cognate_class": cognate_class,
                            "splitTable": splitTable,
                            "action": action,
                            "form": form})

# -- /source/ -------------------------------------------------------------


def source_view(request, source_id):
    source = Source.objects.get(id=source_id)
    return render_template(request, 'source_edit.html', {
            "form": None,
            "source": source,
            "action": ""})


@login_required
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
                    return HttpResponseRedirect(reverse('lexeme-edit-citation',
                                                args=[lexeme.id, citation.id]))
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


def source_list(request):
    grouped_sources = []
    for type_code, type_name in TYPE_CHOICES:
        grouped_sources.append(
            (type_name, Source.objects.filter(type_code=type_code)))
    return render_template(request, "source_list.html",
                           {"grouped_sources": grouped_sources})


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
                        Q(source_form__regex=regex),
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


def viewDefaultLanguage(request):
    language = getDefaultLanguage(request)
    wordlist = getDefaultWordlist(request)
    return view_language_wordlist(request, language, wordlist)


def viewDefaultMeaning(request):
    meaning = getDefaultMeaning(request)
    languagelist = getDefaultLanguagelist(request)
    return view_meaning(request, meaning, languagelist)


def viewDefaultCognateClassList(request):
    meaning = getDefaultMeaning(request)
    return view_cognateclasses(request, meaning)


def viewAbout(request, page):
    """
    @param page :: str
    This function renders an about page.
    """
    if page == 'statistics':
        return viewStatistics(request)
    content = '\n'.join([
        '## Error', '',
        'Sorry, we could not deliver the requested content.',
        'Maybe you have more luck consulting the ' +
        '[wiki](https://github.com/lingdb/CoBL/wiki).'
        ])
    pageTitleMap = {
        'contact': 'Contact',
        'furtherInfo': 'Further Info',
        'home': 'Home'
        }
    baseUrl = 'https://raw.githubusercontent.com/wiki/lingdb/CoBL/'
    pageUrlMap = {
        'contact': baseUrl + 'About-Page:-Contact.md',
        'furtherInfo': baseUrl + 'About-Page:-Further-Info.md',
        'home': baseUrl + 'About-Page:-Home.md'
        }
    if page in pageUrlMap:
        try:
            r = requests.get(pageUrlMap[page])
            if r.status_code == requests.codes.ok:
                content = r.content
        except:
            pass
    return render_template(request, "about.html",
                           {'title': pageTitleMap.get(page, 'Error'),
                            'content': content})


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
            except Exception, e:
                print('Problem creating author:', e)
                messages.error(request, 'Sorry, the server could not '
                               'create new author as requested.')
        elif 'authors' in request.POST:
            authorData = AuthorTableForm(request.POST)
            try:
                authorData.validate()
                for entry in authorData.elements:
                    data = entry.data
                    try:
                        with transaction.atomic():
                            author = Author.objects.get(
                                id=int(data['idField']))
                            if author.isChanged(**data):
                                problem = author.setDelta(request, **data)
                                if problem is None:
                                    author.save()
                                else:
                                    messages.error(
                                        request, author.deltaReport(**problem))
                    except Exception, e:
                        print('Problem while saving author:', e)
                        messages.error(
                            request, 'Problem saving author data: %s' % data)
            except Exception, e:
                print('Problem updating authors:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'updating at least one author.')
        elif 'deleteAuthor' in request.POST:
            deleteAuthor = AuthorDeletionForm(request.POST)
            try:
                deleteAuthor.validate()
                with transaction.atomic():
                    # Making sure the author exists:
                    author = Author.objects.get(
                        initials=deleteAuthor.data['initials'])
                    # Make sure to update things referencing the author here!
                    # Deleting the author:
                    Author.objects.filter(id=author.id).delete()
            except Exception, e:
                print('Problem deleting author:', e)
                messages.error(request, 'Sorry, the server had problems '
                               'deleting the requested author.')
        else:
            print('Cannot handle POST request in viewAuthors():', request)
            messages.error(request, 'Sorry, the server did not '
                           'understand the request.')

    authors = Author.objects.all()
    form = AuthorTableForm()
    for author in authors:

        author.idField = author.id
        author.displayEmail = " [ AT ] ".join(author.email.split("@"))
        form.elements.append_entry(author)

    return render_template(
        request, "authors.html", {'authors': form})


def changeDefaults(request):
    # Functions to get defaults:
    getDefaults = {
        'language': getDefaultLanguage,
        'meaning': getDefaultMeaning,
        'wordlist': getDefaultWordlist,
        'languagelist': getDefaultLanguagelist}
    # Current defaults:
    defaults = {k: v(request) for (k, v) in getDefaults.iteritems()}
    # Defaults that can be changed:
    actions = {
        'language': setDefaultLanguage,
        'meaning': setDefaultMeaning,
        'wordlist': setDefaultWordlist,
        'languagelist': setDefaultLanguagelist}
    # Changing defaults for given parameters:
    for k, v in actions.iteritems():
        if k in request.GET:
            v(request, request.GET[k])
    # Find changed defaults to substitute in url:
    substitutes = {}
    for k, v in getDefaults.iteritems():
        default = v(request)
        if defaults[k] != default:
            substitutes[defaults[k]] = default
    # Url to redirect clients to:
    url = request.GET['url'] if 'url' in request.GET else '/'
    # Substitute defaults in url:
    for k, v in substitutes.iteritems():
        url = url.replace(k, v)
    # Redirect to target url:
    return redirect(url)


def view_frontpage(request):
    return viewAbout(request, 'home')
