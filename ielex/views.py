# -*- coding: utf-8 -*-
import datetime
import textwrap
import re
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import get_template
from reversion.models import Version
from reversion import revision
from ielex.backup import backup
from ielex.forms import *
from ielex.lexicon.models import *
from ielex.extensional_semantics.views import *
from ielex.shortcuts import render_template
from ielex.utilities import next_alias, renumber_sort_keys, confirm_required



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

def view_frontpage(request):
    return render_template(request, "frontpage.html",
            {"lexemes":Lexeme.objects.count(),
            "cognate_classes":CognateSet.objects.count(),
            "languages":Language.objects.count(),
            "meanings":Meaning.objects.count(),
            "coded_characters":CognateJudgement.objects.count()})

def view_changes(request):
    """Recent changes"""
    # XXX the view fails when an object has been deleted
    recent_changes = Version.objects.all().order_by("id").reverse()
    paginator = Paginator(recent_changes, 100) # was 200

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

# login?
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

def get_sort_order(request):
    return request.session.get("language_sort_order", "sort_key")

def get_languages(request): # refactor this away XXX
    """Get all Language objects, respecting language_list selection; if no
    language list then all languages are selected"""
    language_list_name = get_current_language_list_name(request)
    sort_order = get_sort_order(request)
    try:
        languages = Language.objects.filter(
                id__in=LanguageList.objects.get(
                name=language_list_name).language_id_list).order_by(sort_order)
    except LanguageList.DoesNotExist:
        languages = Language.objects.all()
    return languages

def get_current_language_list_name(request): # refactor this away XXX
    """Get the name of the current language list from session."""
    return request.session.get("language_list_name", LanguageList.DEFAULT)

def get_prev_and_next_languages(request, current_language, language_list=None):
    # XXX language_list argument is not currently used
    if language_list:
        ids = LanguageList.objects.get(name=language_list).language_id_list
    else:
        ids = list(Language.objects.values_list("id", flat=True))
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

def get_prev_and_next_meanings(current_meaning):
    meanings = Meaning.objects.all().extra(select={'lower_gloss':
            'lower(gloss)'}).order_by('lower_gloss')
    ids = [m.id for m in meanings]
    current_idx = ids.index(current_meaning.id)
    prev_meaning = Meaning.objects.get(id=ids[current_idx-1])
    try:
        next_meaning = Meaning.objects.get(id=ids[current_idx+1])
    except IndexError:
        next_meaning = Meaning.objects.get(id=ids[0])
    return (prev_meaning, next_meaning)

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

def get_language_list_form(request):
    language_list_name = get_current_language_list_name(request)
    if request.method == 'POST':
        form = ChooseLanguageListForm(request.POST)
        if form.is_valid():
            current_list = form.cleaned_data["language_list"]
            language_list_name = current_list.name
            msg = "Language list selection changed to '%s'" %\
                    language_list_name
            messages.add_message(request, messages.INFO, msg)
    else:
        form = ChooseLanguageListForm()
    form.fields["language_list"].initial = LanguageList.objects.get(
            name=language_list_name).id
    return form


def view_language_list(request):
    language_list_name = get_current_language_list_name(request)
    languages = Language.objects.all().order_by(get_sort_order(request))
    current_list = LanguageList.objects.get(name=language_list_name)
    response = render_template(request, "language_list.html",
            {"languages":languages,
            "language_list_form":get_language_list_form(request),
            "current_list":current_list})
    request.session["language_list_name"] = language_list_name # XXX what's this for?
    return response

@login_required
def language_reorder(request):
    if request.method == "POST":
        form = ReorderLanguageSortKeyForm(request.POST)
        if form.is_valid():
            language = form.cleaned_data["language"]
            if form.data["submit"] == "Move up":
                move_language_up_list(language)
            elif form.data["submit"] == "Move down":
                move_language_down_list(language)
            else:
                assert form.data["submit"] == "Finish"
                # renumbering is slow, and doesn't need to be done every time
                # on the other hand, we hardly ever call this function ...
                renumber_sort_keys()
                return HttpResponseRedirect(reverse("view-languages"))
        else: # pressed Finish without submitting changes
            return HttpResponseRedirect(reverse("view-languages"))
    else: # first visit
        renumber_sort_keys() # if new languages have been added, number them
        form = ReorderLanguageSortKeyForm()
    return render_template(request, "language_reorder.html",
            {"form":form})

def move_language_up_list(language):
    """Called by reorder languages"""
    try: # get two languages in front of this one
        after = Language.objects.filter(
                sort_key__lt=language.sort_key).latest("sort_key")
        try:
            before = Language.objects.filter(
                    sort_key__lt=after.sort_key).latest("sort_key")
            # set the sort key to halfway between them
            language.sort_key = (after.sort_key+before.sort_key)/2
        except Language.DoesNotExist:
            # language is at index 1 => swap index 0 and index 1
            after.sort_key, language.sort_key = language.sort_key,\
                    after.sort_key
            after.save()
        language.save()
    except Language.DoesNotExist:
        pass # already first
    return

def move_language_down_list(language):
    """Called by reorder languages"""
    try: # get two languages after this one
        before = Language.objects.filter(
                sort_key__gt=language.sort_key)[0]
        try:
            after = Language.objects.filter(
                    sort_key__gt=before.sort_key)[0]
            # set the sort key to halfway between them
            language.sort_key = (after.sort_key+before.sort_key)/2
        except IndexError:
            before.sort_key, language.sort_key = language.sort_key,\
                    before.sort_key
            before.save()
        language.save()
    except IndexError:
        pass # already last
    return

def sort_languages(request, ordered_by):
    """Change the selected sort order via url"""
    referer = request.META.get("HTTP_REFERER", reverse("view-languages"))
    request.session["language_sort_order"] = ordered_by
    return HttpResponseRedirect(referer)

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
            msg = u"Wordlist selection changed to '%s'" %\
                    wordlist.name
            messages.add_message(request, messages.INFO, msg)
            return HttpResponseRedirect(reverse("view-language-wordlist",
                    args=[language.ascii_name, wordlist.name]))
    else:
        form = ChooseMeaningListForm()
    form.fields["meaning_list"].initial = wordlist.id

    # collect data
    lexemes = Lexeme.objects.filter(language=language,
            meaning__id__in=wordlist.meaning_id_list)
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
def language_add_new(request):
    if request.method == 'POST':
        form = EditLanguageForm(request.POST)
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-languages"))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("language-report",
                args=[form.cleaned_data["ascii_name"]]))
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
        return HttpResponseRedirect("/language/%s/edit/" %
                language.ascii_name)

    if request.method == 'POST':
        form = EditLanguageForm(request.POST, instance=language)
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect(reverse("view-languages"))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("view-languages"))
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
    return HttpResponseRedirect(reverse("view-languages"))

# -- /meaning(s)/ and /wordlist/ ------------------------------------------

def view_wordlist(request, wordlist="all"):
    wordlist = MeaningList.objects.get(name=wordlist)
    if request.method == 'POST':
        form = ChooseMeaningListForm(request.POST)
        if form.is_valid():
            current_list = form.cleaned_data["meaning_list"]
            wordlist_name = current_list.name
            msg = "Wordlist selection changed to '%s'" %\
                    wordlist_name
            messages.add_message(request, messages.INFO, msg)
            return HttpResponseRedirect(reverse("view-wordlist",
                    args=[wordlist_name]))
    else:
        form = ChooseMeaningListForm()
    form.fields["meaning_list"].initial = wordlist.id

    meanings = Meaning.objects.filter(id__in=wordlist.meaning_id_list)
    response = render_template(request, "wordlist.html",
            {"meanings":meanings,
            "form":form})
    return response

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
        return HttpResponseRedirect(reverse("meaning-edit",
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

def report_meaning(request, meaning, lexeme_id=0, cogjudge_id=0, action=None):
    lexeme_id = int(lexeme_id)
    cogjudge_id = int(cogjudge_id)

    if meaning.isdigit():
        meaning = Meaning.objects.get(id=int(meaning))
        # if there are actions and lexeme_ids these should be preserved too
        return HttpResponseRedirect("/meaning/%s/" % meaning.gloss)
    else:
        meaning = Meaning.objects.get(gloss=meaning)

    if request.method == 'POST':
        form = ChooseCognateClassForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if not cogjudge_id: # new cognate judgement
                lexeme = Lexeme.objects.get(id=lexeme_id)
                cognate_class = cd["cognate_class"]
                if cognate_class not in lexeme.cognate_class.all():
                    cj = CognateJudgement.objects.create(
                            lexeme=lexeme,
                            cognate_class=cognate_class)
                else:
                    cj = CognateJudgement.objects.get(
                            lexeme=lexeme,
                            cognate_class=cognate_class)
            else:
                cj = CognateJudgement.objects.get(id=cogjudge_id)
                cj.cognate_class = cd["cognate_class"]
                cj.save()

            return HttpResponseRedirect('/lexeme/%s/add-cognate-citation/%s/' %
                    (lexeme_id, cj.id))
    else:
        form = ChooseCognateClassForm()

    sort_order = "language__%s" % get_sort_order(request)
    lexemes = Lexeme.objects.select_related().filter(meaning=meaning,
            language__in=get_languages(request)).order_by(sort_order)
    form.fields["cognate_class"].queryset = CognateSet.objects.filter(
            lexeme__in=lexemes).distinct()
    add_cognate_judgement = 0 # to lexeme
    current_lexeme = 0
    if action == "add":
        if cogjudge_id:
            # note that initial values have to be set using id 
            # rather than the object itself
            form.fields["cognate_class"].initial = CognateJudgement.objects.get(
                  id=cogjudge_id).cognate_class.id
        else:
            add_cognate_judgement = lexeme_id
    elif action == "goto":
        current_lexeme = lexeme_id
    prev_meaning, next_meaning = get_prev_and_next_meanings(meaning)
    return render_template(request, "meaning_report.html",
            {"meaning":meaning,
            "prev_meaning":prev_meaning,
            "next_meaning":next_meaning,
            "lexemes": lexemes,
            "add_cognate_judgement":add_cognate_judgement,
            "edit_cognate_judgement":cogjudge_id,
            "current_lexeme":current_lexeme,
            "language_list_name":get_current_language_list_name(request),
            #"language_list_form":get_language_list_form(request),
            "form":form})

# -- /lexeme/ -------------------------------------------------------------

def view_lexeme(request, lexeme_id):
    """For un-logged-in users, view only"""
    lexeme = Lexeme.objects.get(id=lexeme_id)
    return render_template(request, "lexeme_report.html",
            {"lexeme":lexeme})

@login_required
def lexeme_edit(request, lexeme_id, action="", citation_id=0, cogjudge_id=0):
    citation_id = int(citation_id)
    cogjudge_id = int(cogjudge_id)
    lexeme = Lexeme.objects.get(id=lexeme_id)
    lexeme_citations = lexeme.lexemecitation_set.all() # XXX not used?
    sources = Source.objects.filter(lexeme=lexeme)  # XXX not used
    form = None

    if action: # actions are: edit, edit-citation, add-citation
        redirect_url = '/lexeme/%s/' % lexeme_id

        # Handle POST data
        if request.method == 'POST':
            if action == "edit":
                form = EditLexemeForm(request.POST, instance=lexeme) ### 
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect(redirect_url)
                if form.data["submit"] != "Submit":
                    if "new lexeme" in form.data["submit"].lower():
                        redirect_url = "/language/%s/add-lexeme/" % lexeme.language.ascii_name
                    else:
                        redirect_url = '/meaning/%s/%s/#current' % (lexeme.meaning.gloss, lexeme.id)
                if form.is_valid():
                    form.save()
                    ## update_object_from_form(lexeme, form)
                    return HttpResponseRedirect(redirect_url)
            elif action == "edit-citation":
                form = EditCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect(redirect_url)
                if form.data["submit"] != "Submit":
                    if "new lexeme" in form.data["submit"].lower():
                        redirect_url = "/language/%s/add-lexeme/" % lexeme.language.ascii_name
                    else:
                        # redirect_url = '/meaning/%s/' % lexeme.meaning.gloss
                        redirect_url = '/meaning/%s/%s/#current' % (lexeme.meaning.gloss, lexeme.id)
                if form.is_valid():
                    citation = LexemeCitation.objects.get(id=citation_id)
                    update_object_from_form(citation, form)
                    request.session["previous_citation_id"] = citation.id
                    return HttpResponseRedirect(redirect_url)
            elif action == "add-citation":
                form = AddCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect(redirect_url)
                if form.data["submit"] != "Submit":
                    if "new lexeme" in form.data["submit"].lower():
                        redirect_url = "/language/%s/add-lexeme/" % lexeme.language.ascii_name
                    else:
                        # redirect_url = '/meaning/%s/' % lexeme.meaning.gloss
                        redirect_url = '/meaning/%s/%s/#current' % (lexeme.meaning.gloss, lexeme.id)
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
                    return HttpResponseRedirect(redirect_url)
            elif action == "add-new-citation": # TODO
                form = AddCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect(redirect_url)
                if form.data["submit"] != "Submit":
                    if "new lexeme" in form.data["submit"].lower():
                        redirect_url = "/language/%s/add-lexeme/" % lexeme.language.ascii_name
                    else:
                        # redirect_url = '/meaning/%s/' % lexeme.meaning.gloss
                        redirect_url = '/meaning/%s/%s/#current' % (lexeme.meaning.gloss, lexeme.id)
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
                    return HttpResponseRedirect(redirect_url)
            elif action == "delink-citation":
                citation = LexemeCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect(redirect_url)
            elif action == "delink-cognate-citation":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect(redirect_url)
            elif action == "edit-cognate-citation":
                form = EditCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect(redirect_url)
                if form.data["submit"] != "Submit":
                    if "new lexeme" in form.data["submit"].lower():
                        redirect_url = "/language/%s/add-lexeme/" % lexeme.language.ascii_name
                    else:
                        # redirect_url = '/meaning/%s/' % lexeme.meaning.gloss
                        redirect_url = '/meaning/%s/%s/#current' % (lexeme.meaning.gloss, lexeme.id)
                if form.is_valid():
                    citation = CognateJudgementCitation.objects.get(id=citation_id)
                    update_object_from_form(citation, form)
                    request.session["previous_cognate_citation_id"] = citation.id
                    return HttpResponseRedirect(redirect_url)
            elif action == "add-cognate-citation": #
                form = AddCitationForm(request.POST)
                if "cancel" in form.data:
                    return HttpResponseRedirect(redirect_url)
                if form.data["submit"] != "Submit":
                    if "new lexeme" in form.data["submit"].lower():
                        redirect_url = "/language/%s/add-lexeme/" % lexeme.language.ascii_name
                    else:
                        # redirect_url = '/meaning/%s/' % lexeme.meaning.gloss
                        redirect_url = '/meaning/%s/%s/#current' % (lexeme.meaning.gloss, lexeme.id)
                if form.is_valid():
                    citation = CognateJudgementCitation.objects.create(
                            cognate_judgement=CognateJudgement.objects.get(
                            id=cogjudge_id), **form.cleaned_data)
                    request.session["previous_cognate_citation_id"] = citation.id
                    return HttpResponseRedirect(redirect_url)
            elif action == "add-cognate":
                return HttpResponseRedirect("/meaning/%s/%s/#current" %
                        (lexeme.meaning.gloss, lexeme_id))
            else:
                assert not action

        # first visit, preload form with previous answer
        else:
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
                return HttpResponseRedirect("/meaning/%s/%s/#current" %
                        (lexeme.meaning.gloss, lexeme_id))
            elif action == "delink-citation":
                citation = LexemeCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect(redirect_url)
            elif action == "delink-cognate-citation":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect(redirect_url)
            elif action == "add-new-cognate":
                current_aliases = CognateSet.objects.filter(
                        lexeme__in=Lexeme.objects.filter(
                        meaning=lexeme.meaning).values_list(
                        "id", flat=True)).distinct().values_list("alias", flat=True)
                new_alias = next_alias(list(current_aliases))
                cognate_class = CognateSet.objects.create(
                        alias=new_alias)
                cj = CognateJudgement.objects.create(lexeme=lexeme,
                        cognate_class=cognate_class)
                return HttpResponseRedirect('/lexeme/%s/add-cognate-citation/%s' %
                        (lexeme_id, cj.id))
            elif action == "delete":
                redirect_url = '/meaning/%s' % lexeme.meaning.gloss
                lexeme.delete()
                return HttpResponseRedirect(redirect_url)
            else:
                assert not action

    return render_template(request, "lexeme_report.html",
            {"lexeme":lexeme,
            "action":action,
            "form":form,
            "active_citation_id":citation_id,
            "active_cogjudge_citation_id":cogjudge_id,
            })

@login_required
def lexeme_duplicate(request, lexeme_id):
    original_lexeme = Lexeme.objects.get(id=int(lexeme_id))
    SPLIT_RE = re.compile("[,;]")   # split on these characters 
                                    # XXX get this from settings.SPLIT_CHARS ?
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
    return HttpResponseRedirect("/meaning/%s/%s/#current" %
            (original_lexeme.meaning.gloss, original_lexeme.id))

@login_required
def lexeme_add(request,
        meaning=None,
        language=None,
        lexeme_id=0, # non-zero -> duplicate
        return_to=None):
    # TODO break out the duplicate stuff to a different a different
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
                return HttpResponseRedirect("/lexeme/%s/" % lexeme.id)
            except LexemeCitation.DoesNotExist:
                return HttpResponseRedirect("/lexeme/%s/add-citation/" % lexeme.id)
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

# -- /cognate/ ------------------------------------------------------------

#@login_required
def cognate_report(request, cognate_id=0, meaning=None, code=None, action=""):
    if cognate_id:
        cognate_id = int(cognate_id)
        cognate_class = CognateSet.objects.get(id=cognate_id)
    else:
        assert meaning and code
        cognate_classes = CognateSet.objects.filter(alias=code, 
                cognatejudgement__lexeme__meaning__gloss=meaning).distinct()
        try:
            assert len(cognate_classes) == 1
            cognate_class = cognate_classes[0]
        except AssertionError:
            msg = """error: meaning='%s', cognate code='%s' identifies %s cognate
            sets""" % (meaning, code, len(cognate_classes))
            msg = textwrap.fill(msg, 9999)
            messages.add_message(request, messages.INFO, msg)
            return HttpResponseRedirect('/meaning/%s/' % meaning)
    if action == "edit":
        if request.method == 'POST':
            form = EditCognateSetForm(request.POST, instance=cognate_class)
            if "cancel" not in form.data and form.is_valid():
                update_object_from_form(cognate_class, form)
            return HttpResponseRedirect('/cognate/%s/' % cognate_class.id)
        else:
            form = EditCognateSetForm(instance=cognate_class)
    else:
        form = None
    sort_order = "lexeme__language__%s" % get_sort_order(request)
    cj_ordered = cognate_class.cognatejudgement_set.filter(
            lexeme__language__in=get_languages(request)).order_by(sort_order)
    return render_template(request, "cognate_report.html",
            {"cognate_class":cognate_class,
            "cj_ordered":cj_ordered,
             "form":form})

# -- /source/ -------------------------------------------------------------

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
            return HttpResponseRedirect('/sources/')
        if form.is_valid():
            if action == "add":
                source = Source.objects.create(**form.cleaned_data)
                if cogjudge_id: # send back to origin
                    judgement = CognateJudgement.objects.get(id=cogjudge_id)
                    citation = CognateJudgementCitation.objects.create(
                            cognate_judgement=judgement,
                            source=source)
                    return HttpResponseRedirect('/lexeme/%s/edit-cognate-citation/%s/' %\
                            (judgement.lexeme.id, citation.id))
                if lexeme_id:
                    lexeme = Lexeme.objects.get(id=lexeme_id)
                    citation = LexemeCitation.objects.create(
                            lexeme=lexeme,
                            source=source)
                    return HttpResponseRedirect('/lexeme/%s/edit-citation/%s/' %\
                            (lexeme.id, citation.id))
            elif action == "edit":
                form.save()
            return HttpResponseRedirect('/source/%s/' % source.id)
    else:
        if action == "add":
            form = EditSourceForm()
        elif action == "edit":
            #form = EditSourceForm(source.__dict__)
            form = EditSourceForm(instance=source)
        elif action == "delete":
            source.delete()
            return HttpResponseRedirect('/sources/')
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

# -- search ---------------------------------------------------------------

def lexeme_search(request):
    if request.method == 'POST':
        form = SearchLexemeForm(request.POST)
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect('/')
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

