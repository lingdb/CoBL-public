# encoding: utf-8
from django import forms
from ielex.forms import ChooseLanguageListField, ChooseMeaningListField
from ielex.lexicon.models import LanguageList, MeaningList, RELIABILITY_CHOICES

class ChooseOutputBaseForm(forms.Form):
    language_list = ChooseLanguageListField(
            queryset=LanguageList.objects.all(),
            empty_label=None,
            widget=forms.Select())
    meaning_list = ChooseMeaningListField(
            queryset=MeaningList.objects.all(),
            empty_label=None,
            widget=forms.Select())

class ChooseNexusOutputForm(ChooseOutputBaseForm):
    DIALECT = (("BP", "BayesPhylogenies"),
            ("NN", "NeighborNet"),
            ("MB", "MrBayes"))
    dialect = forms.ChoiceField(choices=DIALECT,
            widget=forms.RadioSelect,
            label="NEXUS dialect",
            help_text=u"""BayesPhylogenies uses a ‘data’ block rather than ‘taxa’
            and ‘character’ blocks; NeighborNet and MrBayes require slightly
            different ‘format’ specification""")
    reliability = forms.MultipleChoiceField(choices=RELIABILITY_CHOICES,
            widget=forms.CheckboxSelectMultiple,
            required=False,
            label="Exclude ratings")
    ascertainment_marker = forms.BooleanField(required=False,
            label=u"Ascertainment bias correction marker",
            help_text="""Sets of cognates referring to the same meaning are
            marked by an initial all-zero column; column indexes  of character
            sets are listed in an ‘assumptions’ block""")

class DumpSnapshotForm(ChooseOutputBaseForm):
    pass
