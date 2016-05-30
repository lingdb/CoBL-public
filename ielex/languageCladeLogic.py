# -*- coding: utf-8 -*-
from __future__ import division
from django.db import transaction
from ielex.lexicon.models import *


def updateLanguageCladeRelations(languages=None, clades=None):
    '''
    languages :: [Language] | None
    clades :: [Clade] | None
    This function updates the clades for all given languages.
    It will consider only the given clades.
    Iff clades or languages are None they will be fetched from the database.
    This function was added in an effort to solve #193
    '''
    # Sanitize languages:
    if languages is None:
        languages = Language.objects.all().prefetch_related(
            'languageclade_set')
    # Sanitize clades:
    if clades is None:
        clades = Clade.objects.all()

    def cladeSignature(**kwargs):
        # ',' delimeter is important because of multidigit lvs.
        return ','.join([str(kwargs['cladeLevel0']),
                         str(kwargs['cladeLevel1']),
                         str(kwargs['cladeLevel2']),
                         str(kwargs['cladeLevel3'])])
    # cSig -> Clade
    levelCladeMap = {cladeSignature(cladeLevel0=c.cladeLevel0,
                                    cladeLevel1=c.cladeLevel1,
                                    cladeLevel2=c.cladeLevel2,
                                    cladeLevel3=c.cladeLevel3): c
                     for c in clades}
    # LanguageClade to delete/create:
    toDeleteIds = []  # [LanguageClade.id]
    toCreate = []  # [LanguageClade]

    def flattenLC(lcs):
        # Helper to flatten [LanguageClade] -> String
        return ''.join([str(lc.clade_id) + str(lc.cladesOrder)
                        for lc in lcs])
    # zeroLevels will be merged with specific levels.
    zeroLevels = {'cladeLevel0': 0,
                  'cladeLevel1': 0,
                  'cladeLevel2': 0,
                  'cladeLevel3': 0}
    # Iterating languages to find their clades:
    for l in languages:
        # Data to select related clades by:
        wanted = [('cladeLevel0', l.level0),
                  ('cladeLevel1', l.level1),
                  ('cladeLevel2', l.level2),
                  ('cladeLevel3', l.level3)]
        # Gathering newRels to see if LanguageClade changed:
        newRels = []
        order = 0  # inc by for
        for i in xrange(len(wanted), 0, -1):
            sliceD = dict(wanted[:i])
            sig = cladeSignature(**dict(zeroLevels, **sliceD))
            if sig in levelCladeMap:
                newRels.append(LanguageClade(language=l,
                                             clade=levelCladeMap[sig],
                                             cladesOrder=order))
            order += 1
        # Did the clades for this language change?
        if flattenLC(l.languageclade_set.all()) != flattenLC(newRels):
            toDeleteIds += [lc.id for lc in l.languageclade_set.all()]
            toCreate += newRels
    with transaction.atomic():
        # Deleting unwanted LanguageClade:
        LanguageClade.objects.filter(id__in=toDeleteIds).delete()
        # Creating desired LanguageClade:
        LanguageClade.objects.bulk_create(toCreate)
