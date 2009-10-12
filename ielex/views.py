from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from ielex.lexicon.models import *
from ielex.utilities import next_alias

def view_frontpage(request):
    return render_to_response("frontpage.html",
            {"lexemes":Lexeme.objects.count(),
            "cognate_classes":CognateSet.objects.count(),
            "languages":Language.objects.count(),
            "meanings":Meaning.objects.count()})

def view_languages(request):
    #debug = ["DEBUG"]
    set_cookie = False
    if "language_list_name" in request.POST: #.get("language_list_name",""):
        language_list_name = request.POST.get("language_list_name")
        set_cookie = True
        #debug.append("POST")
    elif "language_list_name" in request.COOKIES:
        language_list_name = request.COOKIES["language_list_name"]
        #debug.append("COOKIE")
    else:
        language_list_name = "GA2003"
        #debug.append("DEFAULT")
    #debug.append(language_list_name)
    languages = Language.objects.all()
    language_lists = LanguageList.objects.all()
    current_list = LanguageList.objects.get(name=language_list_name)
    response = render_to_response("language_list.html", {"languages":languages,
            "language_lists":language_lists, "current_list":current_list})
            #"debug":" : ".join(debug)})
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
            did_you_mean = None
        except Language.DoesNotExist:
            try:
                language = Language.objects.get(ascii_name__istartswith=language)
                return HttpResponseRedirect("/language/%s/" % language.ascii_name)
            except Language.MultipleObjectsReturned:
                languages = Language.objects.filter(ascii_name__icontains=language)
                return render_to_response("choose_language.html",
                        {"languages":languages})
    meanings = Meaning.objects.all()
    lexemes = Lexeme.objects.filter(language=language)
    return render_to_response("language_report.html", {"language":language,
        "lexemes":lexemes, "meanings":meanings})

def report_word(request, word, action=""):
    debug = ""
    # normalize the url
    if action:
        action = action.strip("/")
    if word.isdigit():
        meaning = Meaning.objects.get(id=word)
        return HttpResponseRedirect("/word/%s/" % meaning.gloss)
    else:
        meaning = Meaning.objects.get(gloss=word)

    # language list
    if "language_list_name" in request.COOKIES:
        language_list_name = request.COOKIES["language_list_name"]
    else:
        language_list_name = "GA2003"
    languages = Language.objects.filter(
            id__in=LanguageList.objects.get(name=language_list_name).language_id_list)

    # basic view
    lexemes = Lexeme.objects.select_related().filter( meaning=meaning,
            language__in=languages).order_by( "language") 
            # select_related follows foreign keys
    judgements = CognateJudgement.objects.filter(lexeme__in=lexemes)
    all_cogsets = set([j.cognate_class for j in judgements])
    all_cogset_aliases = ["none"]+sorted([c.alias for c in all_cogsets])+["add"]
    cogset_dict = dict([(c.alias, c) for c in all_cogsets])
    special_codes = ["none","add"]

    if request.POST:
        if "add" in request.POST:
            if request.POST["add"] == "Add":
                language = Language.objects.get(utf8_name=request.POST["language"])
                source_form = request.POST["source_form"]
                phon_form = request.POST["phon_form"]
                assert source_form or phon_form
                cognate_class_alias = request.POST["cognate_class_alias"]
                try:
                    cognate_class = cogset_dict[cognate_class_alias]
                except KeyError:
                    if cognate_class_alias == "add":
                        new_alias = next_alias(cogset_dict.keys(),
                                    ignore=special_codes)
                        cognate_class = CognateSet.objects.create(alias=new_alias)
                        cognate_class.save()
                    else:
                        cognate_class = None
                lexeme = Lexeme.objects.create(language=language,
                        meaning=meaning,
                        source_form=source_form,
                        phon_form=phon_form)
                lexeme.save()
                if cognate_class:
                    cj = CognateJudgement.objects.create(lexeme=lexeme,
                            cognate_class=cognate_class)
                    cj.save()

                debug = "|".join(debug)
            else:
                assert request.POST["add"] == "Cancel"
                debug = "CANCELLED"
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
                                lexeme__id=lexeme_id, cognate_class__id=cogset_id)
                        debug = "DELETED TJ-%s" % target_judgement.id
                        target_judgement.delete() # deletes the database row, not
                                                  # the python object
                        # target_judgement.save() # this _recreated_ the object !@#!
                    elif target_cogset_alias == "add": # make new cognate set
                        new_alias = next_alias(cogset_dict.keys(),
                                    ignore=special_codes)
                        target_cogset = CognateSet.objects.create(alias=new_alias)
                        target_cogset.save()
                        target_judgement = CognateJudgement.objects.create(
                                lexeme=Lexeme.objects.get(id=lexeme_id),
                                cognate_class=target_cogset)
                        debug = "NEW alias %s" % new_alias
                        target_judgement.save()
                else:
                    assert not target_cogset_alias # just to make sure

            # redo basic view after edit
            lexemes = Lexeme.objects.filter(meaning=meaning)
            judgements = CognateJudgement.objects.filter(lexeme__in=lexemes)
            all_cogsets = set([j.cognate_class for j in judgements])
            all_cogset_aliases = ["none"]+sorted([c.alias for c in
                all_cogsets])+["add"]

    return render_to_response("word_report.html", {"lexemes":lexemes,
            "meaning":meaning, "action":action, "languages":languages,
            "all_cogset_aliases":all_cogset_aliases,
            "debug":debug})

def test_form(request):
    selection = request.POST.get("selection","")
    pets = request.POST.getlist("pets")
    return render_to_response('test_form.html',
            {"selection":selection, "pets":pets})

