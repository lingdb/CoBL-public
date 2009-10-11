from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from ielex.lexicon.models import *

def view_frontpage(request):
    return render_to_response("frontpage.html")

def view_languages(request):
    #debug = ["DEBUG"]
    set_cookie = False
    if "selection" in request.POST: #.get("selection",""):
        selection = request.POST.get("selection")
        set_cookie = True
        #debug.append("POST")
    elif "selection" in request.COOKIES:
        selection = request.COOKIES["selection"]
        #debug.append("COOKIE")
    else:
        selection = "GA2003"
        #debug.append("DEFAULT")
    #debug.append(selection)
    languages = Language.objects.all()
    language_lists = LanguageList.objects.all()
    current_list = LanguageList.objects.get(name=selection)
    response = render_to_response("language_list.html", {"languages":languages,
            "language_lists":language_lists, "current_list":current_list})
            #"debug":" : ".join(debug)})
    response.set_cookie("selection", selection)
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

def report_word(request, word):
    # debug = []
    if word.isdigit():
        meaning = Meaning.objects.get(id=word)
        return HttpResponseRedirect("/word/%s/" % meaning.gloss)
    else:
        meaning = Meaning.objects.get(gloss=word)
    lexemes = Lexeme.objects.filter(meaning=meaning)
    return render_to_response("word_report.html", {"lexemes":lexemes,
        "meaning":meaning})

def test_form(request):
    selection = request.POST.get("selection","")
    pets = request.POST.getlist("pets")
    return render_to_response('test_form.html',
            {"selection":selection, "pets":pets})

