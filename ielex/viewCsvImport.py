# -*- coding: utf-8 -*-
import dateutil.parser
from datetime import datetime
from collections import defaultdict

from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone

import clldutils.dsv as dsv

from ielex.lexicon.models import Lexeme
from ielex.shortcuts import render_template
from ielex.utilities import logExceptions


@user_passes_test(lambda u: u.is_superuser)
@csrf_protect
@logExceptions
def viewCsvImport(request):
    '''
    report stores how the import went.
    Its structure must be iterable containing dicts
    with str data for keys 'heading', 'body'.
    '''
    report = []
    if request.method == 'POST' and 'CsvImportForm' in request.POST:
        importMethod = request.POST['tableType']
        fileDicts = list(dsv.reader(request.FILES['csvFile'], dicts=True))
        handlerFunctions = {'ms*l': handleMeaningsLanguageImport}
        if importMethod in handlerFunctions:
            report = handlerFunctions[importMethod](fileDicts, request)

    return render_template(
        request,
        "admin/viewCsvImport.html",
        {'report': report})


def handleMeaningsLanguageImport(fileDicts, request):
    '''
    :: [{..}] -> [str]
    This function handles the import of data for the
    `all meanings single language` table.
    '''
    fieldConversions = {
        'id': intOrNone,
        'language_id': int,
        'meaning_id': int,
        'source_form': strOrEmpty,
        'phon_form': strOrEmpty,
        'gloss': strOrEmpty,
        'notes': strOrEmpty,
        '_order': intOrZero,
        'dubious': boolOrNone,
        'not_swadesh_term': boolOrNone,
        'phoneMic': strOrEmpty,
        'rfcWebLookup1': strOrEmpty,
        'rfcWebLookup2': strOrEmpty,
        'transliteration': strOrEmpty,
        'lastEditedBy': strNonEmpty,
        'lastTouched': strToDatetime
    }

    # Structures to generate report from:
    problematicEntries = []  # :: [(reason, {..}))]
    newEntries = []  # :: [{..}]
    updatedEntries = []  # :: [{..}]

    newLexemes = []  # :: [Lexeme]

    lexemes = Lexeme.objects.filter(
        meaning_id__in=set([e['meaning_id'] for e in fileDicts]),
        language_id__in=set([e['language_id'] for e in fileDicts])
    ).all()

    for entry in fileDicts:
        entry, problem = sanitizeEntry(entry, fieldConversions)
        if problem is not None:
            problematicEntries.append(problem)
            continue

        status = saveEntry(
            entry=entry,
            model=Lexeme,
            request=request,
            ignoreMergeFields=set([
                'id', 'language_id', 'meaning_id', '_order', 'lastTouched']),
            instanceFinder=mkLexemeInstanceFinder(lexemes)
        )
        if type(status) == Lexeme:
            newLexemes.append(status)
            newEntries.append(entry)
        elif type(status) == tuple:
            problematicEntries.append(status)
        else:
            updatedEntries.append(status)

    # Executing required bulk creation:
    Lexeme.objects.bulk_create(newLexemes)

    def listToUl(xs):
        return '<ul>' + ''.join(['<li>%s</li>' % str(dict(x))
                                 for x in xs]) + '</ul>'

    def listToDl(xs):
        return '<dl>' + ''.join([
            '<dt>%s</dt><dd>%s</dd>' % (str(x[0]), str(dict(x[1])))
            for x in xs]) + '</dl>'

    # Returning report:
    return [
        {'heading': 'Problematic entries (%s):' % len(problematicEntries),
         'body': listToDl(problematicEntries)},
        {'heading': 'Newly created entries (%s):' % len(newEntries),
         'body': listToUl(newEntries)},
        {'heading': 'Updated entries (%s):' % len(updatedEntries),
         'body': listToUl(updatedEntries)}
    ]


def sanitizeEntry(entry, fieldConversions):
    # sanitizeEntry :: {} -> {} -> ({}, None) | (None, (str, {}))
    # Entry is problematic, when a field is missing:
    if set(fieldConversions.keys()) != set(entry.keys()):
        return (None, ('Incorrect fields', entry))
    # Sanitizing fields:
    for k, f in fieldConversions.items():
        try:
            entry[k] = f(entry[k])
        except:
            return (None, ('Failed to sanitize field "%s"' % k, entry))
    return (entry, None)


def saveEntry(entry,
              model,
              request,
              ignoreMergeFields=set(),
              instanceFinder=None):
    '''
    Returns:
    * in case of problem: (str, entry)
    * in case of update: entry
    * in case of creation: model

    Uses instanceFinder if given to find instance to update,
    iff entry has no 'id' field.
    instanceFinder :: entry -> model | None
    '''
    instance = None
    if instanceFinder is not None:
        instance = instanceFinder(entry)

    if instance is None:  # Create new model
        return model(**entry)
    else:  # Merge with existing model
        delta = {k: v for k, v in entry.items()
                 if k not in ignoreMergeFields}
        delta['lastTouched'] = datetime.now()
        delta['lastEditedBy'] = ' '.join([request.user.first_name,
                                          request.user.last_name])
        model.objects.filter(id=instance.id).update(**delta)
        return entry


def mkLexemeInstanceFinder(lexemes):

    def lexemeToKey(lexeme):
        return '%s:%s' % (lexeme.language_id, lexeme.meaning_id)
    langMeanToLexemeDict = defaultdict(list)
    for lexeme in lexemes:
        langMeanToLexemeDict[lexemeToKey(lexeme)].append(lexeme)
    idToLexemeMap = {l.id: l for l in lexemes}

    def lexemeInstanceFinder(entry):
        # Returns Lexeme | None
        if entry['id'] in idToLexemeMap:
            return idToLexemeMap[entry['id']]

        ls = langMeanToLexemeDict[
            '%s:%s' % (entry['language_id'], entry['meaning_id'])]
        for l in ls:
            if l.checkTime(t=entry['lastTouched']):
                if l.lastEditedBy == entry['lastEditedBy']:
                    return l
            for k in l.timestampedFields():
                lData = getattr(l, k)
                if bool(lData):
                    if lData != entry[k]:
                        break
            else:
                return l
        return None

    return lexemeInstanceFinder


def intOrNone(s):
    try:
        return int(s)
    except:
        return None


def intOrZero(s):
    try:
        return int(s)
    except:
        return 0


def boolOrNone(s):
    if s == 't':
        return True
    if s == 'f':
        return False
    return None


def strNonEmpty(s):
    if s == '':
        raise Exception('Empty string given to strNonEmpty', s)
    return s


def strOrEmpty(s):
    try:
        return unicode(s)
    except:
        return u''


def strToDatetime(s):
    date = dateutil.parser.parse(s, fuzzy=True)
    if date.tzinfo is None:
        date = timezone.make_aware(date, timezone.get_current_timezone())
    return date
