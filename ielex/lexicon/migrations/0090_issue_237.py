# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import Max

from datetime import datetime


def forwards_func(apps, schema_editor):
    '''
    I accidentially deleted a citation in production.
    This migration adds it again.
    '''
    offending = [44110, 46480, 46481, 46482, 46483, 46484, 46485, 46486,
                 46487, 46488, 46489, 46490, 46491, 46492, 46493, 46494,
                 46495, 46496, 46497, 46498, 46499, 46500, 46501, 46502,
                 46503, 46504, 46505, 46506, 46507, 46508, 46509, 46510,
                 46511, 46512, 46513, 46514, 46515, 46516, 46517, 46518,
                 46519, 46520, 46521, 46522, 46523, 46524, 46525, 46526,
                 46527, 46528, 46529, 46530, 46531, 46532, 46533, 46534,
                 46535, 46536, 46537, 46538, 46539, 46540, 46541, 46542,
                 46543, 46544, 46545, 46546, 46547, 46548, 46549, 46550,
                 46551, 46552, 46553, 46554, 46555, 46556, 46557, 46558,
                 46559, 46560, 46561, 46562, 46563, 46564, 46565, 46566,
                 46567, 46568, 46569, 46570, 46571, 46572, 46573, 46574,
                 46575, 46576, 46577, 46578, 46579, 46580, 46581, 46582,
                 46583, 46584, 46585, 46586, 46587, 46588, 46589, 46590,
                 46591, 46592, 46593]
    # Models to work with:
    CognateJudgementCitation = apps.get_model(
        'lexicon',
        'CognateJudgementCitation')
    print('go!')
    for c in CognateJudgementCitation.objects.filter(id__in=offending).all():
        print(c.id, c.reliability)
    print(1/0)


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0089_fix_citation')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
