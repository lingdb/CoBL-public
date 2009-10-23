import itertools
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from ielex.lexicon.models import *
from ielex.forms import *
from ielex.utilities import next_alias

def view_frontpage(request):
    return render_to_response("frontpage.html",
            {"lexemes":Lexeme.objects.count(),
            "cognate_classes":CognateSet.objects.count(),
            "languages":Language.objects.count(),
            "meanings":Meaning.objects.count(),
            "coded_characters":CognateJudgement.objects.count()})

# def update_language_list_all():
#     try:
#         ll = LanguageList.objects.get(name="all")
#     except:
#         ll = LanguageList.objects.create(name="all")
#     ll.language_ids = ",".join([str(l.id) for l in Language.objects.all()])
#     ll.save()
#     return

def view_languages(request):
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

    languages = Language.objects.all()
    #languages = get_languages(request)
    current_list = LanguageList.objects.get(name=language_list_name)
    response = render_to_response("language_list.html",
            {"languages":languages,
            "form":form,
            "current_list":current_list})
    response.set_cookie("language_list_name", language_list_name)
    return response

def reorder_languages(request):
    # XXX
    if request.method == "POST":
        form = ReorderLanguageSortKeyForm(request.POST)
        if form.is_valid():
            language = form.cleaned_data["language"]
            # Moving up
            # get two languages in front of this one
            try:
                after = Language.objects.filter(
                        sort_key__lt=language.sort_key).latest("sort_key")
                try: 
                    before = Language.objects.filter(
                            sort_key__lt=after.sort_key).latest("sort_key")
                    # set the sort key to halfway between them
                    language.sort_key = (after.sort_key + before.sort_key) / 2
                except Language.DoesNotExist:
                    # language is at index 1 => swap index 0 and index 1
                    after.sort_key, language.sort_key = language.sort_key, after_sort_key
                    after.save()
                language.save()
            except Language.DoesNotExist:
                # language is at index 0
                pass
            # handle min and max sort key values
            # renumber all the sort keys on
            # moving down the same way
    else:
        form = ReorderLanguageSortKeyForm()
    return render_to_response("language_reorder.html",
            {"form":form})

def cognate_report(request, cognate_id):
    cognate_class = CognateSet.objects.get(id=int(cognate_id))
    return render_to_response("cognate_report.html",
            {"cognate_class":cognate_class})

def view_meanings(request):
    meanings = Meaning.objects.all()
    return render_to_response("meaning_list.html", {"meanings":meanings})

def get_canonical_language(language):
    """Identify language from id number or partial name"""
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

def report_language(request, language):
    try:
        language = Language.objects.get(ascii_name=language)
    except Language.DoesNotExist:
        language = get_canonical_language(language)
        return HttpResponseRedirect("/language/%s/" %
                language.ascii_name)
    lexemes = Lexeme.objects.filter(language=language).order_by("meaning")
    return render_to_response("language_report.html",
            {"language":language,
            "lexemes":lexemes})

def edit_language(request, language):
    try:
        language = Language.objects.get(ascii_name=language)
    except Language.DoesNotExist:
        assert False
        language = get_canonical_language(language)
        return HttpResponseRedirect("/language/%s/edit/" %
                language.ascii_name)
    if request.method == 'POST':
        form = EditLanguageForm(request.POST)
        if "cancel" in form.data: # has to be tested before data is cleaned
            return HttpResponseRedirect('/language/%s/' % language.ascii_name)
        if form.is_valid():
            cd = form.cleaned_data
            language.iso_code = cd["iso_code"]
            language.ascii_name = cd["ascii_name"]
            language.utf8_name = cd["utf8_name"]
            language.save()
            return HttpResponseRedirect('/language/%s/' % language.ascii_name)
        else:
            assert False
    else:
        form = EditLanguageForm(language.__dict__)
    return render_to_response("language_edit.html",
            {"language":language,
            "form":form})

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

def lexeme_report(request, lexeme_id, action="", citation_id=0,
        cognate_class_id=0, cogjudge_id=0):
    lexeme = Lexeme.objects.get(id=lexeme_id)
    lexeme_citations = lexeme.lexemecitation_set.all()
    sources = Source.objects.filter(lexeme=lexeme)
    form = None
    citation_id = int(citation_id)
    cognate_class_id = int(cognate_class_id)
    cogjudge_id = int(cogjudge_id)

    if action: # actions are: edit, edit-lexeme, edit-citation, add-citation

        # Handle POST data
        if request.method == 'POST':
            if action == "edit-lexeme":
                form = EditLexemeForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
                if form.is_valid():
                    cd = form.cleaned_data
                    lexeme.source_form = cd["source_form"]
                    lexeme.phon_form = cd["phon_form"]
                    lexeme.notes = cd["notes"]
                    lexeme.save()
                    return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
            elif action == "edit-citation":
                form = EditCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
                if form.is_valid():
                    cd = form.cleaned_data
                    citation = LexemeCitation.objects.get(id=citation_id)
                    citation.pages = cd["pages"]
                    citation.reliability = cd["reliability"]
                    citation.save()
                    return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
            elif action == "add-citation":
                form = AddCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
                if form.is_valid():
                    cd = form.cleaned_data
                    citation = LexemeCitation(
                            lexeme=lexeme,
                            source=cd["source"],
                            pages=cd["pages"],
                            reliability=cd["reliability"])
                    citation.save()
                    return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
            elif action == "delink-citation":
                citation = LexemeCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
            elif action == "delink-cognate-citation":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
            elif action == "edit-cognate":
                form = EditCitationForm(request.POST)
                if "cancel" in form.data: # has to be tested before data is cleaned
                    return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
                if form.is_valid():
                    cd = form.cleaned_data
                    citation = CognateJudgementCitation.objects.get(id=citation_id)
                    citation.pages = cd["pages"]
                    citation.reliability = cd["reliability"]
                    citation.save()
                    return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
            elif action == "add-cognate-citation": #
                form = AddCitationForm(request.POST)
                if "cancel" in form.data:
                    return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
                if form.is_valid():
                    cd = form.cleaned_data
                    citation = CognateJudgementCitation.objects.create(
                            cognate_judgement=CognateJudgement.objects.get(
                                id=cogjudge_id),
                            source=cd["source"],
                            pages=cd["pages"],
                            reliability=cd["reliability"])
                    return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
            elif action == "add-cognate": # XXX
                return HttpResponseRedirect("/meaning/%s/%s" %
                        (lexeme.meaning.gloss, lexeme_id))
            else:
                assert not action

        # first visit
        else:
            if action == "edit-lexeme":
                form = EditLexemeForm(
                        initial={"source_form":lexeme.source_form,
                        "phon_form":lexeme.phon_form,
                        "notes":lexeme.notes})
            elif action == "edit-citation":
                citation = LexemeCitation.objects.get(id=citation_id)
                form = EditCitationForm(
                            initial={"pages":citation.pages,
                            "reliability":citation.reliability})
            elif action == "add-citation":
                form = AddCitationForm()
            elif action == "edit-cognate":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                form = EditCitationForm(
                            initial={"pages":citation.pages,
                            "reliability":citation.reliability})
            elif action == "delink-cognate":
                cj = CognateJudgement.objects.get(id=cogjudge_id)
                cj.delete()
            elif action == "add-cognate-citation":
                form = AddCitationForm()
            elif action == "add-cognate":
                return HttpResponseRedirect("/meaning/%s/%s" %
                        (lexeme.meaning.gloss, lexeme_id))
            elif action == "delink-citation":
                citation = LexemeCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
            elif action == "delink-cognate-citation":
                citation = CognateJudgementCitation.objects.get(id=citation_id)
                citation.delete()
                return HttpResponseRedirect('/lexeme/%s/' % lexeme_id)
            elif action == "add-new-cognate":
                current_aliases = CognateSet.objects.filter(   #
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
            else:
                assert not action

    return render_to_response("lexeme_report.html",
            {"lexeme":lexeme,
            "action":action,
            "form":form,
            "active_citation_id":citation_id,
            "active_cogjudge_citation_id":cogjudge_id,
            })

def report_meaning(request, meaning, lexeme_id=0, cogjudge_id=0):
    lexeme_id = int(lexeme_id)
    cogjudge_id = int(cogjudge_id)
    if meaning.isdigit():
        meaning = Meaning.objects.get(id=meaning)
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

    lexemes = Lexeme.objects.select_related().filter(meaning=meaning,
            language__in=get_languages(request)).order_by("language")
    form.fields["cognate_class"].queryset = CognateSet.objects.filter(
            lexeme__in=lexemes).distinct()
    # note that initial values have to be set using id 
    # rather than the object itself
    if cogjudge_id:
        form.fields["cognate_class"].initial = CognateJudgement.objects.get(
              id=cogjudge_id).cognate_class.id
        add_cognate_judgement=0 # to lexeme
    else:
        add_cognate_judgement=lexeme_id

    return render_to_response("meaning_report.html",
            {"meaning":meaning,
            "lexemes": lexemes,
            "add_cognate_judgement":add_cognate_judgement,
            "edit_cognate_judgement":cogjudge_id,
            "form":form})

def source_edit(request, source_id=0, action=""):
    source_id = int(source_id)
    if source_id:
        source = Source.objects.get(id=source_id)
    else:
        source = None
    if request.method == 'POST':
        form = EditSourceForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if action == "add":
                source = Source.objects.create(
                        citation_text=cd["citation_text"],
                        type_code=cd["type_code"],
                        description=cd["description"])
            elif action == "edit":
                # source = Source.objects.get(id=source_id)
                source.citation_text=cd["citation_text"]
                source.type_code=cd["type_code"]
                source.description=cd["description"]
                source.save()
            return HttpResponseRedirect('/source/%s/' % source.id)
    else:
        if action == "add":
            form = EditSourceForm()
        elif action == "edit":
            form = EditSourceForm(source.__dict__)
        elif action == "delete":
            source.delete()
            return HttpResponseRedirect('/sources/')
        else:
            form = None
    return render_to_response('source_edit.html', {
            "form": form,
            "source":source,
            "action":action})

def source_list(request):
    grouped_sources = []
    for type_code, type_name in Source.TYPE_CHOICES:
        grouped_sources.append((type_name,
                Source.objects.filter(type_code=type_code)))
    return render_to_response("source_list.html", {"grouped_sources":grouped_sources})



