# -*- coding: utf-8 -*-
# import clldutils.dsv as dsv
# from ielex.lexicon.models import Language, Lexeme, Meaning
from ielex.shortcuts import render_template


def viewCsvImport(request):
    return render_template(request, "admin/viewCsvImport.html", {})
