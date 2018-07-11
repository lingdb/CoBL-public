# -*- coding: utf-8 -*-
from __future__ import division
from cobl.lexicon.models import Language, LanguageList, \
                                 Meaning, MeaningList
"""
This module provides functions to track the default settings for a session.
Defaults are either set initially or overwritten by the clients session.
The implementation aims to solve the state tracking problem of #82
that requires us to know which language,.. a client last visited.
"""


def getDefaultLanguage(request):
    """
    @return defaultLanguage :: str
    """
    return request.session.get('defaultLanguage', Language.DEFAULT)


def setDefaultLanguage(request, language):
    """
    @param language :: Language | str
    @return success :: bool
    """
    if type(language) == Language:
        language = language.ascii_name
    if type(language) == str:
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
        'id', flat=True).filter(ascii_name=languageName).all()
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
            'ascii_name', flat=True).filter(id=language).all()
        if len(languageName) == 1:
            return setDefaultLanguage(request, languageName[0])
    return False


def getDefaultMeaning(request):
    """
    @return defaultMeaning :: str
    """
    return request.session.get('defaultMeaning', Meaning.DEFAULT)


def setDefaultMeaning(request, meaning):
    """
    @param meaning :: Meaning | str
    @return success :: bool
    """
    if type(meaning) == Meaning:
        meaning = meaning.gloss
    if type(meaning) == str:
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
    @return defaultWordlist :: str
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
    @param wordlist :: MeaningList | str
    @return success :: bool
    """
    if type(wordlist) == MeaningList:
        wordlist = wordlist.name
    if type(wordlist) == str:
        request.session['defaultWordlist'] = wordlist
        return True
    return False


def getDefaultLanguagelist(request):
    """
    @return defaultLanguagelist :: str
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
    @param languagelist :: LanguageList | str
    @return success :: bool
    """
    if type(languagelist) == LanguageList:
        languagelist = languagelist.name
    if type(languagelist) == str:
        request.session['defaultLanguagelist'] = languagelist
        return True
    return False


def getDefaultDict(request):
    """
    Produces a dictionary that carries the current defaults
    as well as the currently not choosen entries.
    """
    defaults = {
        'defaultLanguage': getDefaultLanguage(request),
        'defaultMeaning': getDefaultMeaning(request),
        'defaultWordlist': getDefaultWordlist(request),
        'defaultLanguagelist': getDefaultLanguagelist(request),
        }
    defaults['otherLanguages'] = \
        Language.objects.exclude(
            ascii_name=defaults['defaultLanguage']).values_list(
            'ascii_name', flat=True)
    defaults['otherMeanings'] = \
        Meaning.objects.exclude(
            gloss=defaults['defaultMeaning']).values_list(
            'gloss', flat=True)
    defaults['otherWordlists'] = \
        MeaningList.objects.exclude(
            name=defaults['defaultWordlist']).values_list(
            'name', flat=True)
    defaults['otherLanguagelists'] = \
        LanguageList.objects.exclude(
            name=defaults['defaultLanguagelist']).values_list(
            'name', flat=True)
    return defaults


def getDefaultSourceLanguage(request):
    return request.session.get('defaultSourceLanguage', None)


def setDefaultSourceLanguage(request, language):
    if type(language) == Language:
        language = language.ascii_name
    if type(language) == str:
        request.session['defaultSourceLanguage'] = language
        return True
    return False
