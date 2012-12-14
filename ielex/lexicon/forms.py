from django import forms
from ielex.forms import ChooseLanguageListField, ChooseMeaningListField
from ielex.lexicon.models import LanguageList, MeaningList, RELIABILITY_CHOICES

class ChooseOutputBaseForm(forms.Form):
    SINGLETON = (("all", "All singletons"),
            ("limited", "Maximum one singleton per language"),
            ("none", "No singletons"))
    language_list = ChooseLanguageListField(
            queryset=LanguageList.objects.all(),
            empty_label=None,
            widget=forms.Select())
    meaning_list = ChooseMeaningListField(
            queryset=MeaningList.objects.all(),
            empty_label=None,
            widget=forms.Select())
    reliability = forms.MultipleChoiceField(choices=RELIABILITY_CHOICES,
            widget=forms.CheckboxSelectMultiple,
            label="Exclude ratings")
    # unique = forms.BooleanField(label="Include unique states")
    exclude_invariant = forms.BooleanField(required=False,
            label="Exclude invariant states")
    singletons = forms.ChoiceField(choices=SINGLETON,
            widget=forms.RadioSelect,
            label="Singletons")

class ChooseNexusOutputForm(ChooseOutputBaseForm):
    DIALECT = (("BP", "BayesPhylogenies"),
            ("NN", "NeighborNet"),
            ("MB", "MrBayes"))
    dialect = forms.ChoiceField(choices=DIALECT,
            widget=forms.RadioSelect,
            label="NEXUS dialect")

class DumpSnapshotForm(ChooseOutputBaseForm):
    pass
