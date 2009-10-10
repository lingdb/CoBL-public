from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from ielex.lexicon.models import *

def view_frontpage(request):
    return HttpResponse("Indo European LEXicon")

def view_languages(request):
    languages = Language.objects.all()
    return render_to_response("language_list.html", {"languages":languages})
    # t = get_template("language_list.html")
    # html = t.render(Context({"language":language}))
    # return HttpResponse(html)

def view_words(request):
    return HttpResponse("Word list")

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
    return render_to_response("word_report.html", {"word":word})
