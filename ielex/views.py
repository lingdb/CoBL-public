from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from ielex.lexicon.models import *
from ielex.forms import ChooseLanguageListForm
from ielex.utilities import next_alias

def view_frontpage(request):
    return render_to_response("frontpage.html",
            {"lexemes":Lexeme.objects.count(),
            "cognate_classes":CognateSet.objects.count(),
            "languages":Language.objects.count(),
            "meanings":Meaning.objects.count()})

def update_language_list_all():
    try:
        ll = LanguageList.objects.get(name="all")
    except:
        ll = LanguageList.objects.create(name="all")
    ll = LanguageList.objects.get(name="all")
    ll.language_ids = ",".join([str(l.id) for l in Language.objects.all()])
    ll.save()
    return

def view_languages(request):
    update_language_list_all()
    language_list_name = request.COOKIES.get("language_list_name","all")
    if request.method == 'POST':
        form = ChooseLanguageListForm(request.POST)
        if form.is_valid():
            current_list = form.cleaned_data["language_list"]
            language_list_name = current_list.name
    else:
        form = ChooseLanguageListForm()
    form.fields["language_list"].initial = LanguageList.objects.get(
            name=language_list_name).id

    languages = Language.objects.all().order_by("utf8_name")
    current_list = LanguageList.objects.get(name=language_list_name)
    response = render_to_response("language_list.html",
            {"languages":languages,
            "form":form,
            "current_list":current_list})
    response.set_cookie("language_list_name", language_list_name)
    return response

def view_words(request):
    meanings = Meaning.objects.all()
    return render_to_response("meaning_list.html", {"meanings":meanings})

def report_language(request, language):
    # languages = None
    if language.isdigit():
        language = Language.objects.get(id=language)
        return HttpResponseRedirect("/language/%s/" % language.ascii_name)
    else:
        try:
            language = Language.objects.get(ascii_name=language)
        except Language.DoesNotExist:
            try:
                language = Language.objects.get(
                        ascii_name__istartswith=language)
                return HttpResponseRedirect("/language/%s/" %
                        language.ascii_name)
            except Language.MultipleObjectsReturned:
                languages = Language.objects.filter(
                        ascii_name__icontains=language)
                return render_to_response("choose_language.html",
                        {"languages":languages})
    meanings = Meaning.objects.all()
    lexemes = Lexeme.objects.filter(language=language)
    return render_to_response("language_report.html", {"language":language,
        "lexemes":lexemes, "meanings":meanings})

def get_languages(request):
    """get languages, respecting language_list selection"""
    language_list_name = get_current_language_list(request)
    languages = Language.objects.filter(
            id__in=LanguageList.objects.get(
            name=language_list_name).language_id_list)
    return languages

def get_current_language_list(request):
    if "language_list_name" in request.COOKIES:
        language_list_name = request.COOKIES["language_list_name"]
    else:
        language_list_name = "all" # default
    return language_list_name

def report_word(request, word, action="", lexeme_id=None):
    debug = ""
    change_lexeme = None
    # normalize the url
    if action:
        action = action.strip("/")
    if word.isdigit():
        meaning = Meaning.objects.get(id=word)
        # if there are actions and lexeme_ids these should be preserved too
        return HttpResponseRedirect("/word/%s/" % meaning.gloss)
    else:
        meaning = Meaning.objects.get(gloss=word)

    # language list
    languages = get_languages(request)
    language_list_name = get_current_language_list(request)

    # basic view
    lexemes = Lexeme.objects.select_related().filter(meaning=meaning,
            language__in=languages).order_by("language")
            # select_related follows foreign keys
    judgements = CognateJudgement.objects.filter(lexeme__in=lexemes)
    all_cogsets = set([j.cognate_class for j in judgements])
    all_cogset_aliases = ["none"]+sorted([c.alias for c in all_cogsets])+["add"]
    cogset_dict = dict([(c.alias, c) for c in all_cogsets])
    special_codes = ["none","add"]

    if request.POST:
        debug = str(request.POST) ###
        if "add" in request.POST:
            if request.POST["add"] == "Add":
                language = Language.objects.get(
                        utf8_name=request.POST["language"])
                source_form = request.POST["source_form"]
                phon_form = request.POST["phon_form"]
                assert source_form and phon_form # handle error gracefully
                if not source_form:
                    source_form = phon_form
                cognate_class_alias = request.POST["cognate_class_alias"]
                try:
                    cognate_class = cogset_dict[cognate_class_alias]
                except KeyError:
                    if cognate_class_alias == "add":
                        new_alias = next_alias(cogset_dict.keys(),
                                    ignore=special_codes)
                        cognate_class = CognateSet.objects.create(
                                alias=new_alias)
                    else:
                        cognate_class = None
                lexeme = Lexeme.objects.create(language=language,
                        meaning=meaning,
                        source_form=source_form,
                        phon_form=phon_form)
                # lexeme.save()
                if cognate_class:
                    cj = CognateJudgement.objects.create(lexeme=lexeme,
                            cognate_class=cognate_class)

                debug = "|".join(debug)
            else:
                assert request.POST["add"] == "Cancel"
                debug = "CANCELLED"
        elif "change" in request.POST:
            try:
                debug = "CHANGE lexeme %s" % request.POST["lexeme_id"]
                change_lexeme = Lexeme.objects.get(id=lexeme_id)
                action="change"
            except KeyError:
                if request.POST["change"] != "Cancel":
                    # XXX do changes to database here XXX
                    debug = "CHANGE COMPLETE"
                else:
                    debug = "CANCELLED CHANGE"
        elif "delete" in request.POST:
            debug = "DELETE lexeme %s" % request.POST["lexeme_id"]
            Lexeme.objects.get(id=request.POST["lexeme_id"]).delete()
        else: # editing cognate sets
            assert len(request.POST) == 1
            name, target_cogset_alias = request.POST.items()[0]
            try:
                lexeme_id, cogset_id = name.split(",")
                lexeme_id, cogset_id = int(lexeme_id), int(cogset_id)
            except ValueError:
                lexeme_id, cogset_id = int(name), None
            debug = "change lexeme %s cogset %s to %s" % (lexeme_id, cogset_id,
                    target_cogset_alias)
            try:
                target_cogset = cogset_dict[target_cogset_alias]
                if cogset_id: # change one judgement to another
                    target_judgement = CognateJudgement.objects.get(
                            lexeme__id=lexeme_id, cognate_class__id=cogset_id)
                else: # change "none" to another
                    target_judgement = CognateJudgement.objects.create(
                            lexeme=Lexeme.objects.get(id=lexeme_id),
                            cognate_class=target_cogset)
                target_judgement.cognate_class = target_cogset
                target_judgement.save()
            except KeyError:
                if target_cogset_alias in special_codes:
                    if target_cogset_alias == "none": # delete coding
                        target_judgement = CognateJudgement.objects.get(
                                lexeme__id=lexeme_id,
                                cognate_class__id=cogset_id)
                        debug = "DELETED TJ-%s" % target_judgement.id
                        target_judgement.delete()
                    elif target_cogset_alias == "add": # make new cognate set
                        new_alias = next_alias(cogset_dict.keys(),
                                    ignore=special_codes)
                        target_cogset = CognateSet.objects.create(
                                alias=new_alias)
                        target_judgement = CognateJudgement.objects.create(
                                lexeme=Lexeme.objects.get(id=lexeme_id),
                                cognate_class=target_cogset)
                        debug = "NEW alias %s" % new_alias
                else:
                    assert not target_cogset_alias # just to make sure

            # redo basic view after edit
            lexemes = Lexeme.objects.filter(meaning=meaning).order_by(
                    "language", "source_form")
            judgements = CognateJudgement.objects.filter(lexeme__in=lexemes)
            all_cogsets = set([j.cognate_class for j in judgements])
            all_cogset_aliases = ["none"]+sorted([c.alias for c in
                all_cogsets])+["add"]

    return render_to_response("word_report.html",
            {"lexemes":lexemes,
            "meaning":meaning,
            "action":action,
            "change_lexeme":change_lexeme,
            "languages":languages,
            "language_list_name":language_list_name,
            "all_cogset_aliases":all_cogset_aliases,
            "debug":debug})

def word_source(request, lexeme_id):
    prev_page = request.META["HTTP_REFERER"]
    lexeme_id = int(lexeme_id)
    lexeme = Lexeme.objects.get(id=lexeme_id)
    citations = lexeme.lexemecitation_set.all()
    sources = Source.objects.filter(lexeme=lexeme)
    # l.lexemecitation_set.get(source=s).pages
    return render_to_response("word_source.html", {"lexeme":lexeme,
        "sources":sources,
        "citations":citations,
        "prev_page":prev_page})


# -- TESTING ---------------------------------------------------------

from ielex.forms import EnterNewSourceForm
def test_form_newsource(request):
    if request.method == 'POST':
        form = EnterNewSourceForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/test-success/')
    else:
        form = EnterNewSourceForm()
    return render_to_response('test_form.html', {'form': form})

from ielex.forms import ChooseSourceForm
def test_form_choosesource(request):
    if request.method == 'POST':
        form = ChooseSourceForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/test-success/')
    else:
        form = ChooseSourceForm()
    return render_to_response('test_form.html', {'form': form})

from ielex.forms import AddNewWordForm
# this works:
def test_form_newword(request):
    if request.method == 'POST':
        form = AddNewWordForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/test-success/')
    else:
        form = AddNewWordForm()
    form.fields["language"].queryset = get_languages(request)
    return render_to_response('test_form.html', {'form': form})

from ielex.forms import ChooseLanguageForm
def test_form_chooselanguage(request):
    no_submit_button = True
    if request.method == 'POST':
        form = ChooseLanguageForm(request.POST)
        if form.is_valid():
            return HttpResponse(form.cleaned_data["language"])
            #return HttpResponseRedirect('/test-success/')
    else:
        form = ChooseLanguageForm()
    # note that initial values have to be set using id rather than the object
    # itself
    form.fields["language"].initial = Language.objects.get(ascii_name='Bengali').id
    return render_to_response('test_form.html', {'form': form,
        "no_submit_button":no_submit_button})

def test_success(request):
    return HttpResponse("Success!")
