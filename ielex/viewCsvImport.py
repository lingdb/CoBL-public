# -*- coding: utf-8 -*-
import dateutil.parser

from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import user_passes_test
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
        fileDicts = dsv.reader(request.FILES['csvFile'], dicts=True)
        handlerFunctions = {'ms*l': handleMeaningsLanguageImport}
        if importMethod in handlerFunctions:
            report = handlerFunctions[importMethod](fileDicts, request)

    return render_template(
        request,
        "admin/viewCsvImport.html",
        {'report': report})


def handleMeaningsLanguageImport(fileDicts, request):
    '''
    :: [{…}] -> [str]
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
        'lastTouched': dateutil.parser.parse
    }

    # Structures to generate report from:
    problematicEntries = []  # :: [(reason, {…}))]
    newEntries = []  # :: [{…}]
    updatedEntries = []  # :: [{…}]

    newLexemes = []  # :: [Lexeme]

    for entry in fileDicts:
        entry, problem = sanitizeEntry(entry, fieldConversions)
        if problem is not None:
            problematicEntries.append(problem)
            continue

        status = saveEntry(
            entry=entry,
            model=Lexeme,
            ignoreMergeFields=set([
                'id', 'language_id', 'meaning_id', '_order', 'lastTouched']),
            instanceFinder=lexemeInstanceFinder
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
        {'heading': 'Newly created entries (%s):' % len(newEntries),
         'body': listToUl(newEntries)},
        {'heading': 'Updated entries (%s):' % len(updatedEntries),
         'body': listToUl(updatedEntries)},
        {'heading': 'Problematic entries (%s):' % len(problematicEntries),
         'body': listToDl(problematicEntries)}
    ]


def sanitizeEntry(entry, fieldConversions):
    # sanitizeEntry :: {} -> {} -> ({}, None) | (None, (str, {}))
    # Entry is problematic, when a field is missing:
    if set(fieldConversions.keys()) != set(entry.keys()):
        return (None, ('Incorrect fields', entry))
    # Sanitizing fields:
    for k, f in fieldConversions.iteritems():
        try:
            entry[k] = f(entry[k])
        except:
            return (None, ('Failed to sanitize field "%s"' % k, entry))
    return (entry, None)


def saveEntry(entry,
              model,
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
    if 'id' in entry and entry['id'] is not None:
        instance = model.objects.get(id=entry['id'])
        if not instance.checkTime(t=entry['lastTouched']):
            return ('Refusing to update entry:', entry)
    elif instanceFinder is not None:
        instance = instanceFinder(entry)

    if instance is None:  # Create new model
        return model(**entry)
    else:  # Merge with existing model
        for k, v in entry.iteritems():
            if k in ignoreMergeFields:
                continue
            instance[k] = v
        instance.save()
        return entry


def lexemeInstanceFinder(entry):
    # Returns Lexeme | None
    try:
        lexemes = Lexeme.objects.filter(
            meaning_id=entry['meaning_id'],
            language_id=entry['language_id']).all()
        for lexeme in lexemes:
            if lexeme.checkTime(t=entry['lastTouched']) and \
               lexeme.lastEditedBy == entry['lastEditedBy']:
                return lexeme
            for k, v in lexeme.toDict().iteritems():
                if bool(v):
                    print('DEBUG', 'Truthy entry: (%s,%s)' % (k, v))
                    break
            else:
                return lexeme
    except:
        pass
    return None


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
        return str(s)
    except:
        return ''
