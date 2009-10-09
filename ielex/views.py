from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse

def view_frontpage(request):
    return HttpResponse("Indo European LEXicon")

def view_languages(request):
    return HttpResponse("Language list")

def view_words(request):
    return HttpResponse("Word list")

def report_language(request, language):
    t = get_template("language_report.html")
    html = t.render(Context({"language":language}))
    return HttpResponse(html)

def report_word(request, word):
    t = get_template("word_report.html")
    html = t.render(Context({"word":word}))
    return HttpResponse(html)
