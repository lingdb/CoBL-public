# -*- coding: utf-8 -*-
from django import forms
from ielex.forms import clean_ascii_name
from ielex.extensional_semantics.models import *
from ielex.lexicon.models import RELIABILITY_CHOICES


class ChooseSemanticRelationsField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return obj.relation_code

class ChooseIncludedRelationsField(ChooseSemanticRelationsField):
    pass

class ChooseExcludedRelationsField(ChooseSemanticRelationsField):
    pass

class EditRelationForm(forms.ModelForm):

    def clean_relation_code(self):
        data = self.cleaned_data["relation_code"]
        clean_ascii_name(data)
        return data

    class Meta:
        model = SemanticRelation

class EditSemanticDomainForm(forms.ModelForm):

    def clean_name(self):
        data = self.cleaned_data["name"]
        clean_ascii_name(data)
        return data

    class Meta:
        model = SemanticDomain
        exclude = ["relation_ids"]

class AddSemanticExtensionForm(forms.Form):
    relations = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple(),
            choices=SemanticRelation.objects.values_list("id", "relation_code"),
            )

class SemanticExtensionCitationForm(forms.ModelForm):

    # overridden to ensure no "-----" choice
    reliability = forms.ChoiceField(choices=RELIABILITY_CHOICES,
            widget=forms.RadioSelect) 

    class Meta:
        #exclude = ["extension"]
        model = SemanticExtensionCitation

class MultipleSemanticExtensionCitationForm(forms.ModelForm):
    """Hides the extension value; will be applied to multiple objects"""

    # overridden to ensure no "-----" choice
    reliability = forms.ChoiceField(choices=RELIABILITY_CHOICES,
            widget=forms.RadioSelect) 

    class Meta:
        exclude = ["extension"]
        model = SemanticExtensionCitation
        widgets = {
                "comment":forms.Textarea(attrs={'cols': 78, 'rows': 20}),
                }

class ChooseSemanticRelationsForm(forms.Form):
    included_relations = ChooseIncludedRelationsField(
            required=False, empty_label=None,
            queryset=SemanticRelation.objects.none(),
            widget=forms.Select(attrs={"size":20, "onchange":"this.form.submit()"}))
    excluded_relations = ChooseExcludedRelationsField(
            required=False, empty_label=None,
            queryset=SemanticRelation.objects.all(),
            widget=forms.Select(attrs={"size":20, "onchange":"this.form.submit()"}))

