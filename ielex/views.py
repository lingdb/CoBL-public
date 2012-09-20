# -*- coding: utf-8 -*-
import datetime
import textwrap
import bisect
import re
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Q, Max, Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import RequestContext
from django.template.loader import get_template
from reversion.models import Version
from reversion import revision
from ielex.forms import *
from ielex.lexicon.models import *
# from ielex.citations.models import *
from ielex.extensional_semantics.views import *
from ielex.shortcuts import render_template
from ielex.utilities import next_alias, confirm_required

# Refactoring: 
# - rename the functions which render to response with the format
# view_TEMPLATE_NAME(request, ...). Put subsiduary functions under their main
# caller.

# -- Database input, output and maintenance functions ------------------------

@login_required
def make_backup(request):
    try:
        referer = request.META["HTTP_REFERER"]
    except KeyError:
        referer = "/"
    msg=backup()
    messages.add_message(request, messages.INFO, msg)
    return HttpResponseRedirect(referer)

def view_changes(request, username=None):
    """Recent changes"""
    # XXX the view fails when an object has been deleted
    if not username:
        recent_changes = Version.objects.all().order_by("-id")
    else:
        recent_changes = Version.objects.filter(
                revision__user__username=username).order_by("-id")
    paginator = Paginator(recent_changes, 50) # was 200

    try: # Make sure page request is an int. If not, deliver first page.
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try: # If page request is out of range, deliver last page of results.
        changes = paginator.page(page)
    except (EmptyPage, InvalidPage):
        changes = paginator.page(paginator.num_pages)

    # def object_exists(version):
    #     try:
    #         version.object_version.object
    #         return version
    #     except Version.DoesNotExist:
    #         return None

    # changes.object_list = [version for version in changes.object_list if object_exists(version)]

    contributors = sorted([(User.objects.get(id=user_id),
            Version.objects.filter(revision__user=user_id).count())
            for user_id in Version.objects.values_list("revision__user",
            flat=True).distinct() if user_id is not None],
            lambda x, y: -cmp(x[1], y[1])) # reverse sort by second element in tuple
            # TODO user_id should never be None

    return render_template(request, "view_changes.html",
            {"changes":changes,
            "contributors":contributors})

@login_required
def revert_version(request, version_id):
    """Roll back the object saved in a Version to the previous Version"""
    referer = request.META.get("HTTP_REFERER", "/")
    latest = Version.objects.get(pk=version_id)
    versions = Version.objects.get_for_object(
            latest.content_type.get_object_for_this_type(
            id=latest.object_id)).filter(id__lt=version_id).reverse()
    previous = versions[0]
    previous.revision.revert() # revert all associated objects too
    msg = "Rolled back version %s to version %s" % (latest.id, previous.id)
    messages.add_message(request, messages.INFO, msg)
    return HttpResponseRedirect(referer)

# login? # TODO
def view_object_history(request, version_id):
    version = Version.objects.get(pk=version_id)
    obj = version.content_type.get_object_for_this_type(id=version.object_id)
    # versions = Version.objects.get_for_object(
    #         latest.content_type.get_object_for_this_type(
    #         id=latest.object_id)).filter(id__lt=version_id).reverse()
    fields = [field.name for field in obj._meta.fields]
    versions = [[v.field_dict[f] for f in fields]+[v.id] for v in
            Version.objects.get_for_object(obj).order_by("revision__date_created")]
    return render_template(request, "view_object_history.html",
            {"object":obj,
            "versions":versions,
            "fields":fields})


# -- General purpose queries and functions -----------------------------------

def get_canonical_meaning(meaning):
    """Identify meaning from id number or partial name"""
    if meaning.isdigit():
        meaning = Meaning.objects.get(id=meaning)
    else:
        meaning = Meaning.objects.get(gloss=meaning)
    return meaning

def get_canonical_language(language):
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
                language = Language.objects.filter(
                    ascii_name__istartswith=language).order_by("ascii_name")[0]
            # except Language.DoesNotExist # still! XXX
            #   language = Language.objects.last_added()
    return language

def get_current_language_list_name(request):
    """Get the name of the current language list from session. This is
    only be be used by navigation functions (e.g.
    get_previous_and_next_languages) which don't take part in the RESTful url
    scheme"""
    return request.session.get("language_list_name", LanguageList.DEFAULT)

def get_prev_and_next_languages(request, current_language, language_list=None):
    # XXX language_list argument is not currently dispatched to this function
    # TODO this needs to be fixed
    if language_list:
        language_list = LanguageList.objects.get(name=language_list)
    else:
        language_list = LanguageList.objects.get(name=LanguageList.DEFAULT)

    ids = list(language_list.languages.values_list(
            "id", flat=True).order_by("languagelistorder"))
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

def get_ordered_meanings(wordlist):
    # TODO change this to the same ordering setup used by LanguageList (returns
    # a queryset), after which it will be possible to annotate the meanings
    # with e.g. Count()s
    def get_list_sorter(wordlist):
        def func(meaning):
            return wordlist.meaning_id_list.index(meaning.id)
        return func
    queryset = Meaning.objects.filter(id__in=wordlist.meaning_id_list)
    return sorted(queryset, key=get_list_sorter(wordlist))

def get_prev_and_next_meanings(request, current_meaning):
    # We'll let this one use the session variable (kind of cheating...)
    wordlist = request.session.get("current_wordlist_name", MeaningList.DEFAULT)
    wordlist = MeaningList.objects.get(name=wordlist)
    meanings = get_ordered_meanings(wordlist)

    ids = [m.id for m in meanings]
    current_idx = ids.index(current_meaning.id)
    prev_meaning = meanings[current_idx-1]
    # prev_meaning = Meaning.objects.get(id=ids[current_idx-1])
    try:
        next_meaning = meanings[current_idx+1]
        # next_meaning = Meaning.objects.get(id=ids[current_idx+1])
    except IndexError:
        next_meaning = meanings[0]
        # next_meaning = Meaning.objects.get(id=ids[0])
    return (prev_meaning, next_meaning)

def get_prev_and_next_lexemes(request, current_lexeme):
    """Get the previous and next lexeme from the same language, ordered
    by meaning and then alphabetically by form"""
    current_meaning = current_lexeme.meaning
    lexemes = list(Lexeme.objects.filter(language=current_lexeme.language).order_by(
            "meaning", "phon_form", "source_form", "id"))
    ids = [l.id for l in lexemes]
    current_idx = ids.index(current_lexeme.id)
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
    return

# -- /language(s)/ ----------------------------------------------------------

def get_canonical_language_list(language_list=None):
    """Returns a LanguageList object"""
    try:
        if language_list is None:
            language_list = LanguageList.objects.get(name=LanguageList.DEFAULT)
        elif language_list.isdigit():
            language_list = LanguageList.objects.get(id=language_list)
        else:
            language_list = LanguageList.objects.get(name=language_list)
    except LanguageList.DoesNotExist:
        language_list = LanguageList.objects.get(name=LanguageList.DEFAULT)
    return language_list

# def get_language_list_form(request):
#     language_list_name = get_current_language_list_name(request)
#     if request.method == 'POST':
#         form = ChooseLanguageListForm(request.POST)
#         if form.is_valid():
#             current_list = form.cleaned_data["language_list"]
#             language_list_name = current_list.name
#             msg = "Language list selection changed to '%s'" %\
#                     language_list_name
#             messages.add_message(request, messages.INFO, msg)
#     else:
#         form = ChooseLanguageListForm()
#     form.fields["language_list"].initial = LanguageList.objects.get(
#             name=language_list_name).id
#     return form


def view_language_list(request, language_list=None):
    if not language_list:
        return(redirect("view-language-list",
            language_list=LanguageList.DEFAULT))
    current_list = get_canonical_language_list(language_list)
    request.session["current_language_list_name"] = current_list.name
    languages = current_list.languages.all().order_by("languagelistorder")
    languages = languages.annotate(lexeme_count=Count("lexeme"))

    if request.method == 'POST':
        form = ChooseLanguageListForm(request.POST)
        if form.is_valid():
            current_list = form.cleaned_data["language_list"]
            request.session["current_language_list_name"] = current_list.name
            msg = "Language list selection changed to '%s'" %\
                    current_list.name
            messages.add_message(request, messages.INFO, msg)
            return HttpResponseRedirect(reverse("view-language-list",
                    args=[current_list.name]))
    else:
        form = ChooseLanguageListForm()
    form.fields["language_list"].initial = current_list.id

    return render_template(request, "language_list.html",
            {"languages":languages,
            "language_list_form":form,
            "current_list":current_list})

def reorder_language_list(request, language_list):
    language_id = request.session.get("current_language_id", None)
    language_list = LanguageList.objects.get(name=language_list)
    languages = language_list.languages.all().order_by("languagelistorder")
    ReorderForm = make_reorder_languagelist_form(languages)
    if request.method == "POST":
        form = ReorderForm(request.POST, initial={"language": language_id})
        if form.is_valid():
            language_id = int(form.cleaned_data["language"])
            request.session["current_language_id"] = language_id
            language = Language.objects.get(id=language_id)
            if form.data["submit"] == "Finish":
                language_list.sequentialize()
                return HttpResponseRedirect(reverse("view-language-list",
                    args=[language_list.name]))
            else:
                if form.data["submit"] == "Move up":
                    move_language(language, language_list, -1)
                elif form.data["submit"] == "Move down":
                    move_language(language, language_list, 1)
                else:
                    assert False, "This shouldn't be able to happen"
                return HttpResponseRedirect(reverse("reorder-language-list",
                    args=[language_list.name]))
        else: # pressed Finish without submitting changes
            # TODO might be good to zap the session variable once finished
            # request.session["current_meaning_id"] = None
            return HttpResponseRedirect(reverse("view-language-list",
                args=[language_list.name]))
    else: # first visit
        form = ReorderForm(initial={"language":language_id})
    return render_template(request, "reorder_language_list.html",
            {"language_list":language_list, "form":form})

def move_language(language, language_list, direction):
    assert direction in (-1, 1)
    languages = list(language_list.languages.order_by( "languagelistorder"))
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
    return

def view_language_wordlist(request, language, wordlist):
    wordlist = MeaningList.objects.get(name=wordlist)

    # clean language name
    try:
        language = Language.objects.get(ascii_name=language)
    except(Language.DoesNotExist):
        language = get_canonical_language(language)
        return HttpResponseRedirect(reverse("view-language-wordlist",
            args=[language.ascii_name, wordlist.name]))

    # change wordlist
    if request.method == 'POST':
        form = ChooseMeaningListForm(request.POST)
        if form.is_valid():
            wordlist = form.cleaned_data["meaning_list"]
            request.session["current_wordlist_name"] = wordlist.name
            msg = u"Wordlist selection changed to '%s'" % wordlist.name
            messages.add_message(request, messages.INFO, msg)
            return HttpResponseRedirect(reverse("view-language-wordlist",
                    args=[language.ascii_name, wordlist.name]))
    else:
        form = ChooseMeaningListForm()
    form.fields["meaning_list"].initial = wordlist.id

    # collect data
    lexemes = Lexeme.objects.filter(language=language,
            meaning__id__in=wordlist.meaning_id_list
            ).select_related("meaning__gloss").order_by("meaning__gloss")
    # decorate (with a temporary attribute)
    for lexeme in lexemes:
        lexeme.temporary_sort_order = wordlist.meaning_id_list.index(lexeme.meaning.id)
    lexemes = sorted(lexemes, key=lambda l:l.temporary_sort_order)

    prev_language, next_language = \
            get_prev_and_next_languages(request, language)
    return render_template(request, "language_wordlist.html",
            {"language":language,
            "lexemes":lexemes,
            "prev_language":prev_language,
            "next_language":next_language,
            "wordlist":wordlist,
            "form":form
            })

@login_required
def add_language_list(request):
    """Start a new language list by cloning an old one"""
    if request.method == "POST":
        form = AddLanguageListForm(request.POST)
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-all-languages"))
        if form.is_valid():
            form.save()
            new_list = LanguageList.objects.get(name=form.cleaned_data["name"])
            other_list = LanguageList.objects.get(name=form.cleaned_data["language_list"])
            for language in other_list.languages.all().order_by("languagelistorder"):
                new_list.append(language)
            #edit_language_list(request, language_list=form.cleaned_data["name"])
            return HttpResponseRedirect(reverse("edit-language-list",
                    args=[form.cleaned_data["name"]]))
    else:
        form = AddLanguageListForm()
    return render_template(request, "add_language_list.html",
            {"form":form})

@login_required
def edit_language_list(request, language_list=None):
    language_list = get_canonical_language_list(language_list) # a language list object
    language_list_all = get_canonical_language_list()  # a language list object
    included_languages = language_list.languages.all().order_by("languagelistorder")
    excluded_languages = language_list_all.languages.exclude(
                        id__in=language_list.languages.values_list("id", flat=True)
                        ).order_by("languagelistorder")
    if request.method == "POST":
        name_form = EditLanguageListForm(request.POST, instance=language_list)
        if "cancel" in name_form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse('view-language-list',
                args=[language_list.name]))
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
                return HttpResponseRedirect(reverse('edit-language-list',
                    args=[language_list.name]))
            else: # changed name
                name_form.save()
                return HttpResponseRedirect(reverse('view-language-list',
                    args=[name_form.cleaned_data["name"]]))
    else:
        name_form = EditLanguageListForm(instance=language_list)
        list_form = EditLanguageListMembersForm()
        list_form.fields["included_languages"].queryset = included_languages
        list_form.fields["excluded_languages"].queryset = excluded_languages
    return render_template(request, "edit_language_list.html",
            {"name_form":name_form,
            "list_form":list_form,
            "n_included":included_languages.count(),
            "n_excluded":excluded_languages.count(),
            })

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
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-language-list",
                    args=[language_list.name]))
        if form.is_valid():
            form.save()
            language = Language.objects.get(
                    ascii_name=form.cleaned_data["ascii_name"])
            try:
                language_list.insert(0, language)
            except IntegrityError:
                pass # automatically inserted into LanguageList.DEFAULT
            return HttpResponseRedirect(reverse("language-report",
                args=[language.ascii_name]))
    else: # first visit
        form = EditLanguageForm()
    return render_template(request, "language_add_new.html",
            {"form":form})

@login_required
def edit_language(request, language):
    try:
        language = Language.objects.get(ascii_name=language)
    except Language.DoesNotExist:
        language = get_canonical_language(language)
        return HttpResponseRedirect(reverse("language-edit",
                args=[language.ascii_name]))

    if request.method == 'POST':
        form = EditLanguageForm(request.POST, instance=language)
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-all-languages"))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("view-all-languages"))
    else:
        form = EditLanguageForm(instance=language)
    return render_template(request, "language_edit.html",
            {"language":language,
            "form":form})

@login_required
def delete_language(request, language):
    try:
        language = Language.objects.get(ascii_name=language)
    except Language.DoesNotExist:
        language = get_canonical_language(language)
        return HttpResponseRedirect(reverse("language-delete"),
                args=[language.ascii_name])

    language.delete()
    return HttpResponseRedirect(reverse("view-all-languages"))

# -- /meaning(s)/ and /wordlist/ ------------------------------------------

def view_wordlists(request):
    wordlists = MeaningList.objects.all()
    return render_template(request, "wordlists_list.html",
            {"wordlists":wordlists})

def view_wordlist(request, wordlist=MeaningList.DEFAULT):
    wordlist = MeaningList.objects.get(name=wordlist)
    request.session["current_wordlist_name"] = wordlist.name
    if request.method == 'POST':
        form = ChooseMeaningListForm(request.POST)
        if form.is_valid():
            wordlist = form.cleaned_data["meaning_list"]
            request.session["current_wordlist_name"] = wordlist.name
            msg = "Wordlist selection changed to '%s'" %\
                    wordlist.name
            messages.add_message(request, messages.INFO, msg)
            return HttpResponseRedirect(reverse("view-wordlist",
                    args=[wordlist.name]))
    else:
        form = ChooseMeaningListForm()
    form.fields["meaning_list"].initial = wordlist.id

    meanings = get_ordered_meanings(wordlist)
    current_language_list = request.session.get("current_language_list_name",
            LanguageList.DEFAULT)
    return render_template(request, "wordlist.html",
            {"meanings":meanings,
            "form":form,
            "current_language_list":current_language_list})

@login_required
def edit_wordlist(request, wordlist):
    wordlist = MeaningList.objects.get(name=wordlist)

    if request.method == 'POST':
        form = EditMeaningListForm(request.POST, instance=wordlist)
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-wordlist",
                    args=[wordlist.name]))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("view-wordlist",
                    args=[wordlist.name]))
    else:
        form = EditMeaningListForm(instance=wordlist)

    return render_template(request, "edit_wordlist.html",
            {"wordlist":wordlist,
            "form":form})

@login_required
def reorder_wordlist(request, wordlist):
    meaning_id = request.session.get("current_meaning_id", None)
    wordlist = MeaningList.objects.get(name=wordlist)
    meanings = get_ordered_meanings(wordlist)

    ReorderForm = make_reorder_meaninglist_form(meanings)
    if request.method == "POST":
        form = ReorderForm(request.POST, initial={"meaning":meaning_id})
        if form.is_valid():
            meaning_id = int(form.cleaned_data["meaning"])
            request.session["current_meaning_id"] = meaning_id
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
        else: # pressed Finish without submitting changes
            # TODO might be good to zap the session variable once finished
            # request.session["current_meaning_id"] = None
            return HttpResponseRedirect(reverse("view-wordlist",
                args=[wordlist.name]))
    else: # first visit
        form = ReorderForm(initial={"meaning":meaning_id})
    return render_template(request, "reorder_wordlist.html",
            {"wordlist":wordlist, "form":form})

def move_meaning(meaning, wordlist, direction):
    assert direction in (-1, 1)
    meaning_ids = wordlist.meaning_id_list[:] # copy
    target_idx = meaning_ids.index(meaning.id)
    target = meaning_ids.pop(target_idx)
    target_idx += direction
    if target_idx > len(meaning_ids):
        target_idx = 0
    elif target_idx < 0:
        target_idx = len(meaning_ids) + 1
    meaning_ids.insert(target_idx, target)
    wordlist.meaning_id_list = meaning_ids
    wordlist.save()
    return

@login_required
def meaning_add_new(request):
    if request.method == 'POST':
        form = EditMeaningForm(request.POST)
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-meanings"))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("meaning-report",
                args=[form.cleaned_data["gloss"]]))
    else: # first visit
        form = EditMeaningForm()
    return render_template(request, "meaning_add_new.html",
            {"form":form})

@login_required
def edit_meaning(request, meaning):
    try:
        meaning = Meaning.objects.get(gloss=meaning)
    except Meaning.DoesNotExist:
        meaning = get_canonical_meaning(meaning)
        return HttpResponseRedirect(reverse("edit-meaning",
                args=[meaning.gloss]))
    if request.method == 'POST':
        form = EditMeaningForm(request.POST, instance=meaning)
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect(meaning.get_absolute_url())
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(meaning.get_absolute_url())
    else:
        form = EditMeaningForm(instance=meaning)
    return render_template(request, "meaning_edit.html",
            {"meaning":meaning,
            "form":form})

def view_meaning(request, meaning, language_list, lexeme_id=None):
    # XXX a refactored version of report_meaning

    # Normalize calling parameters
    canonical_gloss = get_canonical_meaning(meaning).gloss
    current_language_list = get_canonical_language_list(language_list)
    request.session["current_language_list_name"] = current_language_list.name
    if meaning != canonical_gloss or language_list != current_language_list.name:
        return HttpResponseRedirect(reverse("view-meaning-languages", 
            args=[canonical_gloss, current_language_list.name]))
    else:
        meaning = Meaning.objects.get(gloss=meaning)

    # Change language list form
    if request.method == 'POST':
        language_form = ChooseLanguageListForm(request.POST)
        if language_form.is_valid():
            current_language_list = language_form.cleaned_data["language_list"]
            msg = "Language list selection changed to '%s'" %\
                    current_language_list.name
            messages.add_message(request, messages.INFO, msg)
            request.session["current_language_list_name"] = current_language_list.name
            return HttpResponseRedirect(reverse("view-meaning-languages",
                    args=[canonical_gloss, current_language_list.name]))
    else:
        language_form = ChooseLanguageListForm()
    language_form.fields["language_list"].initial = current_language_list.id

    # Cognate class judgement button
    if request.method == 'POST':
        cognate_form = ChooseCognateClassForm(request.POST)
        if cognate_form.is_valid():
            cd = cognate_form.cleaned_data
            cognate_class = cd["cognate_class"]
            #if not cogjudge_id: # new cognate judgement
            lexeme = Lexeme.objects.get(id=lexeme_id)
            if cognate_class not in lexeme.cognate_class.all():
                cj = CognateJudgement.objects.create(
                        lexeme=lexeme,
                        cognate_class=cognate_class)
            else:
                cj = CognateJudgement.objects.get(
                        lexeme=lexeme,
                        cognate_class=cognate_class)
                    # else:
                    #     cj = CognateJudgement.objects.get(id=cogjudge_id)
                    #     cj.cognate_class = cd["cognate_class"]
                    #     cj.save()

            # change this to a reverse() pattern
            return HttpResponseRedirect(reverse("lexeme-add-cognate-citation",
                    args=[lexeme_id, cj.id]))
    else:
        cognate_form = ChooseCognateClassForm()

    # Get lexemes, respecting 'languages'
    # lexemes = Lexeme.objects.filter(meaning=meaning,
    #         language__id__in=current_language_list.language_id_list)
    lexemes = get_ordered_lexemes(meaning, current_language_list,
            "language", "meaning", "cognatejudgement_set")
    cognate_form.fields["cognate_class"].queryset = CognateClass.objects.filter(
            lexeme__in=lexemes).distinct()

    prev_meaning, next_meaning = get_prev_and_next_meanings(request, meaning)
    return render_template(request, "view_meaning.html",
            {"meaning":meaning,
            "prev_meaning":prev_meaning,
            "next_meaning":next_meaning,
            "lexemes": lexemes,
            "language_form":language_form,
            "cognate_form":cognate_form,
            "add_cognate_judgement":lexeme_id,
            })



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

def get_ordered_lexemes(meaning, language_list, *select_related_fields):
    lexemes = Lexeme.objects.filter(
            meaning=meaning,
            language__in=language_list.languages.all(
            )).filter(language__languagelistorder__language_list=language_list
            ).select_related(*select_related_fields).order_by(
            "language__languagelistorder")
    return lexemes

def view_lexeme(request, lexeme_id):
    """For un-logged-in users, view only"""
    lexeme = Lexeme.objects.get(id=lexeme_id)
    prev_lexeme, next_lexeme = get_prev_and_next_lexemes(request, lexeme)
    return render_template(request, "lexeme_report.html",
            {"lexeme":lexeme,
            "prev_lexeme":prev_lexeme,
            "next_lexeme":next_lexeme})

@login_required
def lexeme_edit(request, lexeme_id, action="", citation_id=0, cogjudge_id=0):
    citation_id = int(citation_id)
    cogjudge_id = int(cogjudge_id)
    lexeme = Lexeme.objects.get(id=lexeme_id)
    form = None

    if action: # actions are: edit, edit-citation, add-citation
        def get_redirect_url(form):
            form_data = form.data["submit"].lower()
            if "new lexeme" in form_data:
                redirect_url = reverse("language-add-lexeme",
                        args=[lexeme.language.ascii_name])
            elif "back to language" in form_data:
                redirect_url = reverse('language-report',
                        args=[lexeme.language.ascii_name])
            elif "back to meaning" in form_data:
                redirect_url = '%s#lexeme_%s' % (reverse("meaning-report",
                    args=[lexeme.meaning.gloss]), lexeme.id)
            else:
                redirect_url = reverse('view-lexeme', args=[lexeme_id])
            return redirect_url

        # Handle POST data
        if request.method == 'POST':
            if action == "edit":
                form = EditLexemeForm(request.POST, instance=lexeme) ### 
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect(get_redirect_url(form))
                if form.is_valid():
                    form.save()
                    return HttpResponseRedirect(get_redirect_url(form))
            elif action == "edit-citation":
                form = EditCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect(get_redirect_url(form))
                if form.is_valid():
                    citation = LexemeCitation.objects.get(id=citation_id)
                    update_object_from_form(citation, form)
                    request.session["previous_citation_id"] = citation.id
                    return HttpResponseRedirect(get_redirect_url(form))
            elif action == "add-citation":
                form = AddCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect(get_redirect_url(form))
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
                    return HttpResponseRedirect(get_redirect_url(form))
            elif action == "add-new-citation": # TODO
                form = AddCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect(get_redirect_url(form))
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
                    return HttpResponseRedirect(get_redirect_url(form))
            elif action == "delink-citation":
                citation = LexemeCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect(redirect_url)
            elif action == "delink-cognate-citation":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect(get_redirect_url(form))
            elif action == "edit-cognate-citation":
                form = EditCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect(get_redirect_url(form))
                if form.is_valid():
                    citation = CognateJudgementCitation.objects.get(id=citation_id)
                    update_object_from_form(citation, form)
                    request.session["previous_cognate_citation_id"] = citation.id
                    return HttpResponseRedirect(get_redirect_url(form))
            elif action == "add-cognate-citation": #
                form = AddCitationForm(request.POST)
                if "cancel" in form.data:
                    return HttpResponseRedirect(get_redirect_url(form))
                if form.is_valid():
                    citation = CognateJudgementCitation.objects.create(
                            cognate_judgement=CognateJudgement.objects.get(
                            id=cogjudge_id), **form.cleaned_data)
                    request.session["previous_cognate_citation_id"] = citation.id
                    return HttpResponseRedirect(get_redirect_url(form))
            elif action == "add-cognate":
                languagelist = get_canonical_language_list(get_current_language_list_name(request))
                redirect_url = '%s#lexeme_%s' % (
                        reverse("view-meaning-languages-add-cognate",
                        args=[lexeme.meaning.gloss, languagelist, lexeme.id]), lexeme.id)
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
                            initial={"pages":citation.pages,
                            "reliability":citation.reliability,
                            "comment":citation.comment})
            elif action in ("add-citation", "add-new-citation"):
                previous_citation_id = request.session.get("previous_citation_id")
                try:
                    citation = LexemeCitation.objects.get(id=previous_citation_id)
                    form = AddCitationForm(
                                initial={"source":citation.source.id,
                                "pages":citation.pages,
                                "reliability":citation.reliability,
                                "comment":citation.comment})
                except LexemeCitation.DoesNotExist:
                    form = AddCitationForm()
            # elif action == "add-new-citation":# XXX
            #     form = AddCitationForm()
            elif action == "edit-cognate-citation":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                form = EditCitationForm(
                            initial={"pages":citation.pages,
                            "reliability":citation.reliability,
                            "comment":citation.comment})
            elif action == "delink-cognate":
                cj = CognateJudgement.objects.get(id=cogjudge_id)
                cj.delete()
            elif action == "add-cognate-citation":
                previous_citation_id = request.session.get("previous_cognate_citation_id")
                try:
                    citation = CognateJudgementCitation.objects.get(id=previous_citation_id)
                    form = AddCitationForm(
                                initial={"source":citation.source.id,
                                "pages":citation.pages,
                                "reliability":citation.reliability,
                                "comment":citation.comment})
                except CognateJudgementCitation.DoesNotExist:
                    form = AddCitationForm()
                # form = AddCitationForm()
            elif action == "add-cognate":
                languagelist = get_canonical_language_list(get_current_language_list_name(request))
                redirect_url = '%s#lexeme_%s' % (
                        reverse("view-meaning-languages-add-cognate",
                        args=[lexeme.meaning.gloss, languagelist, lexeme.id]), lexeme.id)
                return HttpResponseRedirect(redirect_url)
                # redirect_url = '%s#lexeme_%s' % (reverse("meaning-report",
                #        args=[lexeme.meaning.gloss]), lexeme.id)
                # return HttpResponseRedirect(redirect_url)
            elif action == "delink-citation":
                citation = LexemeCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect(redirect_url)
            elif action == "delink-cognate-citation":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect(redirect_url)
            elif action == "add-new-cognate":
                current_aliases = CognateClass.objects.filter(
                        lexeme__in=Lexeme.objects.filter(meaning=lexeme.meaning)
                        ).distinct().values_list("alias", flat=True)
                new_alias = next_alias(list(current_aliases))
                cognate_class = CognateClass.objects.create(
                        alias=new_alias)
                cj = CognateJudgement.objects.create(lexeme=lexeme,
                        cognate_class=cognate_class)
                return HttpResponseRedirect(reverse('lexeme-add-cognate-citation',
                        args=[lexeme_id, cj.id]))
            elif action == "delete":
                redirect_url = reverse("meaning-report",
                        args=[lexeme.meaning.gloss])
                lexeme.delete()
                return HttpResponseRedirect(redirect_url)
            else:
                assert not action

    prev_lexeme, next_lexeme = get_prev_and_next_lexemes(request, lexeme)
    return render_template(request, "lexeme_report.html",
            {"lexeme":lexeme,
            "prev_lexeme":prev_lexeme,
            "next_lexeme":next_lexeme,
            "action":action,
            "form":form,
            "active_citation_id":citation_id,
            "active_cogjudge_citation_id":cogjudge_id,
            })

@login_required
def lexeme_duplicate(request, lexeme_id):
    """Useful for processing imported data; currently only available
    through direct url input, e.g. /lexeme/0000/duplicate/"""
    original_lexeme = Lexeme.objects.get(id=int(lexeme_id))
    SPLIT_RE = re.compile("[,;]")   # split on these characters 
    done_split = False

    if SPLIT_RE.search(original_lexeme.source_form):
        original_source_form, new_source_form = [e.strip() for e in
                SPLIT_RE.split(original_lexeme.source_form, 1)]
        done_split= True
    else:
        original_source_form, new_source_form = original_lexeme.source_form, ""

    if SPLIT_RE.search(original_lexeme.phon_form):
        original_phon_form, new_phon_form = [e.strip() for e in
                SPLIT_RE.split(original_lexeme.phon_form, 1)]
        done_split= True
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
    redirect_to = "%s#lexeme_%s" % (reverse("meaning-report",
        args=[original_lexeme.meaning.gloss]), original_lexeme.id)
    return HttpResponseRedirect(redirect_to)

@login_required
def lexeme_add(request,
        meaning=None,
        language=None,
        lexeme_id=0, # non-zero -> duplicate
        return_to=None):
    # TODO break out the duplicate stuff to a different
    # (non-interactive) function, that splits and copies the lexemes, along
    # with cognate coding and everything (include a #current tag too)
    initial_data = {}
    if language:
        initial_data["language"] = get_canonical_language(language)
    if meaning:
        initial_data["meaning"] = get_canonical_meaning(meaning)
    # if lexeme_id:
    #     original_lexeme = Lexeme.objects.get(id=int(lexeme_id))
    #     original_source_form, new_source_form = [e.strip() for e in
    #             original_lexeme.source_form.split(",", 1)]
    #     initial_data["language"] = original_lexeme.language
    #     initial_data["meaning"] = original_lexeme.meaning

    if request.method == "POST":
        form = AddLexemeForm(request.POST)
        if "cancel" in form.data: # has to be tested before data is cleaned
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
            {"form":form})

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

#@login_required
def cognate_report(request, cognate_id=0, meaning=None, code=None,
        cognate_name=None, action=""):
    form_dict = {
            "edit-name":EditCognateClassNameForm,
            "edit-notes":EditCognateClassNotesForm
            }
    if cognate_id:
        cognate_class = CognateClass.objects.get(id=int(cognate_id))
    elif cognate_name:
        cognate_class = CognateClass.objects.get(name=cognate_name)
    else:
        assert meaning and code
        cognate_classes = CognateClass.objects.filter(alias=code, 
                cognatejudgement__lexeme__meaning__gloss=meaning).distinct()
        try:
            assert len(cognate_classes) == 1
            cognate_class = cognate_classes[0]
        except AssertionError:
            msg = """error: meaning='%s', cognate code='%s' identifies %s cognate
            sets""" % (meaning, code, len(cognate_classes))
            msg = textwrap.fill(msg, 9999)
            messages.add_message(request, messages.INFO, msg)
            return HttpResponseRedirect(reverse('meaning-report',
                args=[meaning]))
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
            # else: send form with errors back to render_template
        else:
            form = form_dict[action](instance=cognate_class)
    else:
        form = None

    # This is a clunky way of sorting; currently assumes LanguageList
    # 'all' (maybe make this configurable?)
    language_list = LanguageList.objects.get(name=LanguageList.DEFAULT)
    cj_ordered = []
    # for language_id in language_list.language_id_list:
    for language in language_list.languages.all().order_by("languagelistorder"):
        cj = cognate_class.cognatejudgement_set.filter(
                lexeme__language=language)
        cj_ordered.extend(list(cj))

    return render_template(request, "cognate_report.html",
            {"cognate_class":cognate_class,
            "cj_ordered":cj_ordered,
            "action":action,
            "form":form})

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
                if cogjudge_id: # send back to origin
                    judgement = CognateJudgement.objects.get(id=cogjudge_id)
                    citation = CognateJudgementCitation.objects.create(
                            cognate_judgement=judgement,
                            source=source)
                    return HttpResponseRedirect(reverse('lexeme-edit-cognate-citation',
                            args=[judgement.lexeme.id, citation.id]))
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
        grouped_sources.append((type_name,
                Source.objects.filter(type_code=type_code)))
    return render_template(request, "source_list.html",
            {"grouped_sources":grouped_sources})

# -- key value pairs ------------------------------------------------------

def set_key_value(request, key, value):
    msg = "set key '%s' to '%s'" % (key, value)
    messages.add_message(request, messages.INFO, msg)
    return HttpResponseRedirect(reverse("view-frontpage"))

# -- search ---------------------------------------------------------------

def lexeme_search(request):
    if request.method == 'POST':
        form = SearchLexemeForm(request.POST)
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-frontpage"))
        if form.is_valid():
            regex = form.cleaned_data["regex"]
            languages = form.cleaned_data["languages"]
            if not languages:
                languages = Language.objects.all()
            if form.cleaned_data["search_fields"] == "L": # Search language fields
                lexemes = Lexeme.objects.filter(
                        Q(phon_form__regex=regex) | Q(source_form__regex=regex),
                        language__in=languages)
            else:
                assert form.cleaned_data["search_fields"] == "E" # Search English fields
                lexemes = Lexeme.objects.filter(
                        Q(gloss__regex=regex) | Q(notes__regex=regex) | Q(meaning__gloss__regex=regex),
                        language__in=languages)
            return render_template(request, "lexeme_search_results.html", {
                    "regex": regex,
                    "language_names":[(l.utf8_name or l.ascii_name) for l in languages],
                    "lexemes": lexemes,
                    })
    else:
        form = SearchLexemeForm()
    return render_template(request, "lexeme_search.html",
            {"form":form})

