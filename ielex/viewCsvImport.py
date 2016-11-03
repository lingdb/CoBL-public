# -*- coding: utf-8 -*-
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import user_passes_test
# import clldutils.dsv as dsv
# from ielex.lexicon.models import Language, Lexeme, Meaning
from ielex.shortcuts import render_template
from ielex.utilities import logExceptions


@user_passes_test(lambda u: u.is_superuser)
@csrf_protect
@logExceptions
def viewCsvImport(request):
    return render_template(request, "admin/viewCsvImport.html", {})
