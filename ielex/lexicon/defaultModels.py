# -*- coding: utf-8 -*-
from __future__ import division
from ielex.lexicon.models import *
"""
This module provides functions to track the default settings for a session.
Defaults are either set initially or overwritten by the clients session.
The implementation aims to solve the state tracking problem of #82
that requires us to know which language,… a client last visited.
"""


def getDefaultLanguage(request):
    """
    @return defaultLanguage :: str | unicode
    """
    return request.session.get('defaultLanguage', 'Proto-Indo-European')


def setDefaultLanguage(request, language):
    """
    @param language :: Language | str | unicode
    @return success :: bool
    """
    if type(language) == Language:
        language = language.utf8_name
    if type(language) == str or type(language) == unicode:
        request.session['defaultLanguage'] = language
        return True
    return False


def getDefaultLanguageId(request):
    """
    @return defaultLanguageId :: int | None
    This function is essentially a proxy for getDefaultLanguage.
    """
    languageName = getDefaultLanguage(request)
    id = Language.objects.values_list(
        'id', flat=True).filter(utf8_name=languageName).all()
    if len(id) == 1:
        return id[0]
    return None


def setDefaultLanguageId(request, language):
    """
    @param language :: Language | int
    @return success :: bool
    """
    if type(language) == Language:
        return setDefaultLanguage(request, language)
    if type(language) == int:
        languageName = Language.objects.values_list(
            'utf8_name', flat=True).filter(id=language).all()
        if len(languageName) == 1:
            return setDefaultLanguage(request, languageName[0])
    return False


def getDefaultMeaning(request):
    """
    @return defaultMeaning :: str | unicode
    """
    return request.session.get('defaultMeaning', 'ash')


def setDefaultMeaning(request, meaning):
    """
    @param meaning :: Meaning | str | unicode
    @return success :: bool
    """
    if type(meaning) == Meaning:
        meaning = meaning.gloss
    if type(meaning) == str or type(meaning) == unicode:
        request.session['defaultMeaning'] = meaning
        return True
    return False


def getDefaultMeaningId(request):
    """
    @return defaultMeaningId :: int | None
    """
    meaningName = getDefaultMeaning(request)
    id = Meaning.objects.values_list(
        'id', flat=True).filter(gloss=meaningName).all()
    if len(id) == 1:
        return id[0]
    return None


def setDefaultMeaningId(request, meaning):
    """
    @param meaning :: Meaning | int
    @return success :: bool
    """
    if type(meaning) == Meaning:
        return setDefaultMeaning(request, meaning)
    if type(meaning) == int:
        meaningName = Meaning.objects.values_list(
            'gloss', flat=True).filter(id=meaning).all()
        if len(meaningName) == 1:
            return setDefaultMeaning(request, meaningName[0])
    return False


def getDefaultWordlist(request):
    """
    @return defaultWordlist :: str | unicode
    """
    return request.session.get('defaultWordlist', MeaningList.DEFAULT)


def getDefaultWordlistId(request):
    """
    @return defaultWordlistId int
    """
    wl = getDefaultWordlist(request)
    try:
        ids = MeaningList.objects.values_list(
            'id', flat=True).filter(name=wl).all()
        if len(ids) == 1:
            return ids[0]
    except:
        pass
    return 1  # id of MeaningList `all`


def setDefaultWordlist(request, wordlist):
    """
    @param wordlist :: MeaningList | str | unicode
    @return success :: bool
    """
    if type(wordlist) == MeaningList:
        wordlist = wordlist.name
    if type(wordlist) == str or type(wordlist) == unicode:
        request.session['defaultWordlist'] = wordlist
        return True
    return False


def getDefaultLanguagelist(request):
    """
    @return defaultLanguagelist :: str | unicode
    """
    return request.session.get('defaultLanguagelist', LanguageList.DEFAULT)


def getDefaultLanguagelistId(request):
    """
    @return defaultLanguagelistId int
    """
    ll = getDefaultLanguagelist(request)
    try:
        ids = LanguageList.objects.values_list(
            'id', flat=True).filter(name=ll).all()
        if len(ids) == 1:
            return ids[0]
    except:
        pass
    return 1  # id of LanguageList `all`


def setDefaultLanguagelist(request, languagelist):
    """
    @param languagelist :: LanguageList | str | unicode
    @return success :: bool
    """
    if type(languagelist) == LanguageList:
        languagelist = languagelist.name
    if type(languagelist) == str or type(languagelist) == unicode:
        request.session['defaultLanguagelist'] = languagelist
        return True
    return False
