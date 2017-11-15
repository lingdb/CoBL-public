# encoding: utf-8
from django import forms
from ielex.forms import ChooseLanguageListField, ChooseMeaningListField
from ielex.lexicon.models import LanguageList, \
                                 MeaningList, \
                                 NEXUS_DIALECT_CHOICES


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
    dialect = forms.ChoiceField(
        choices=NEXUS_DIALECT_CHOICES,
        widget=forms.RadioSelect,
        label="NEXUS dialect",
        help_text=u"""BayesPhylogenies uses a ‘data’ block rather than ‘taxa’
        and ‘character’ blocks; NeighborNet and MrBayes require slightly
        different ‘format’ specification""")
    ascertainment_marker = forms.BooleanField(
        required=False,
        label=u"Ascertainment bias correction marker",
        help_text="""Sets of cognates referring to the same meaning are
        marked by an initial all-zero column; column indexes  of character
        sets are listed in an ‘assumptions’ block""")
    # Added for #146:
    excludeNotSwadesh = forms.BooleanField(
        required=False,
        label=u"Not Swh.:",
        help_text="Exclude lexemes marked as not Swadesh.")
    excludePllDerivation = forms.BooleanField(
        required=False,
        label=u"Pll. Derivation",
        help_text="Exclude cognate sets marked as parallel derivation.")
    excludeIdeophonic = forms.BooleanField(
        required=False,
        label=u"Ideophonic",
        help_text="Exclude cognate sets marked as ideophonic.")
    excludeDubious = forms.BooleanField(
        required=False,
        label=u"Dubious",
        help_text="Exclude cognate sets marked as dubious.")
    excludeLoanword = forms.BooleanField(
        required=False,
        label=u"Loanword",
        help_text="Exclude cognate sets marked as loan event.")
    excludePllLoan = forms.BooleanField(
        required=False,
        label=u"Exclude Pll. loan cognate sets"
    )
    includePllLoan = forms.BooleanField(
        required=False,
        label=u"Include Pll. loans as independent sets."
    )
    excludeMarkedMeanings = forms.BooleanField(
        required=False,
        label=u"Exclude meanings?",
        help_text="Exclude meanings marked [Not for Export]"
    )
    excludeMarkedLanguages = forms.BooleanField(
        required=False,
        label=u"Exclude languages?",
        help_text="Exclude languages marked [Not for Export]"
    )
    calculateMatrix = forms.BooleanField(
        required=False,
        label=u"Calculate Matrix?",
        help_text="""Calculate in addition the language distance matrix based on shared cognate classes. 
        (Depending on the number of languages and meanings the calculation will take a long time!)"""
    )
    calculateMatrix.widget.attrs["disabled"] = "disabled"
    calculateMatrix.widget.attrs["title"] = "not yet available - coming soon"
    description = forms.CharField(
        label="Export description",
        help_text="Please give a short description of the export.",
        max_length=256,
        required=True,
        widget=forms.Textarea)

    field_order = ["language_list",
                   "excludeMarkedLanguages",
                   "meaning_list",
                   "excludeMarkedMeanings",
                   "dialect",
                   "calculateMatrix",
                   "ascertainment_marker",
                   "excludeNotSwadesh",
                   "excludePllDerivation",
                   "excludeIdeophonic",
                   "excludeDubious",
                   "excludeLoanword",
                   "excludePllLoan",
                   "includePllLoan",
                   "description"]

    def clean(self):
        # Making sure excludePllLoan and includePllLoan are never both True:
        cleaned_data = super(ChooseNexusOutputForm, self).clean()
        if cleaned_data['excludePllLoan'] and cleaned_data['includePllLoan']:
            raise forms.ValidationError(
                "It's forbidden to set both excludePllLoan "
                "and includePllLoan to true.")
        return cleaned_data


class DumpSnapshotForm(ChooseOutputBaseForm):
    pass
