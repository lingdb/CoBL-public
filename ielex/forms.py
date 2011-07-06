# -*- coding: utf-8 -*-
import re
from django import forms
from ielex.lexicon.models import *
from ielex.extensional_semantics.models import *

def clean_ascii_name(data):
    """Check that a string is suitable to be part of a url (ascii, no spaces)"""
    illegal_chars = re.findall(r"[^a-zA-Z0-9$\-_\.+!*'(),]", data)
    try:
        assert not illegal_chars
    except AssertionError:
        raise forms.ValidationError("Invalid character/s for an ascii label:"\
                " '%s'" % "', '".join(illegal_chars))
    return data

class ChooseLanguageField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.utf8_name or obj.ascii_name

class ChooseLanguagesField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.utf8_name or obj.ascii_name

class ChooseLanguageListField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name

class ChooseIncludedLanguagesField(ChooseLanguageField):
    pass

class ChooseExcludedLanguagesField(ChooseLanguageField):
    pass

class ChooseMeaningListField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name

class ChooseMeaningField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.gloss

class ChooseCognateClassField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.alias

class ChooseSourcesField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        def truncate(s, l):
            if len(s) < l:
                return s
            else:
                return s[:l-4]+" ..."
        return truncate(obj.citation_text, 124)

class ChooseOneSourceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        def truncate(s, l):
            if len(s) < l:
                return s
            else:
                return s[:l-4]+" ..."
        return truncate(obj.citation_text, 124)

class ChooseSemanticRelationsField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return obj.relation_code

class ChooseIncludedRelationsField(ChooseSemanticRelationsField):
    pass

class ChooseExcludedRelationsField(ChooseSemanticRelationsField):
    pass

class AddLexemeForm(forms.ModelForm):

    language = ChooseLanguageField(queryset=Language.objects.all())
    meaning = ChooseMeaningField(queryset=Meaning.objects.all(),
            help_text="e.g. Swadesh meaning", required=False)
    gloss = forms.CharField(required=False, help_text="""The actual gloss of
            this lexeme, may be different to 'meaning'""")

    class Meta:
        model = Lexeme
        exclude = ["cognate_class", "source"]

class EditLexemeForm(forms.ModelForm):

    meaning = ChooseMeaningField(queryset=Meaning.objects.all(),
            help_text="e.g. Swadesh meaning", required=False)
    gloss = forms.CharField(required=False, help_text="""The actual gloss of
            this lexeme, may be different to 'meaning'""")

    class Meta:
        model = Lexeme
        exclude = ["language", "cognate_class", "source"]


class EditSourceForm(forms.ModelForm):

    type_code = forms.ChoiceField(choices=TYPE_CHOICES,
            widget=forms.RadioSelect())

    class Meta:
        model = Source

class EditLanguageForm(forms.ModelForm):

    def clean_ascii_name(self):
        data = self.cleaned_data["ascii_name"]
        clean_ascii_name(data)
        return data

    class Meta:
        model = Language

class EditMeaningForm(forms.ModelForm):

    def clean_gloss(self):
        data = self.cleaned_data["gloss"]
        clean_ascii_name(data)
        return data

    class Meta:
        model = Meaning

class EditMeaningListForm(forms.ModelForm):

    def clean_gloss(self):
        data = self.cleaned_data["name"]
        clean_ascii_name(data)
        return data

    class Meta:
        model = MeaningList
        exclude = ["meaning_ids"]

class EditRelationForm(forms.ModelForm):

    def clean_relation_code(self):
        data = self.cleaned_data["relation_code"]
        clean_ascii_name(data)
        return data

    class Meta:
        model = SemanticRelation

class ChooseLanguageForm(forms.Form):
    # Need to think about the default sort order of the Language objects here
    # It might make sense to have it alphabetical
    language = ChooseLanguageField(queryset=Language.objects.all(),
            widget=forms.Select(attrs={"onchange":"this.form.submit()"}))

class ChooseLanguageListForm(forms.Form):
    language_list = ChooseLanguageListField(
            queryset=LanguageList.objects.all(),
            empty_label=None,
            widget=forms.Select(attrs={"onchange":"this.form.submit()"}))

class EditLanguageListForm(forms.ModelForm):

    def clean_name(self):
        data = self.cleaned_data["name"]
        clean_ascii_name(data)
        return data

    class Meta:
        model = LanguageList
        exclude = ["language_ids"]

class EditLanguageListMembersForm(forms.Form):
    included_languages = ChooseIncludedLanguagesField(
            required=False, empty_label=None,
            queryset=Language.objects.none(),
            widget=forms.Select(attrs={"size":20, "onchange":"this.form.submit()"}))
    excluded_languages = ChooseExcludedLanguagesField(
            required=False, empty_label=None,
            queryset=Language.objects.all(),
            widget=forms.Select(attrs={"size":20, "onchange":"this.form.submit()"}))


class ChooseMeaningListForm(forms.Form):
    meaning_list = ChooseMeaningListField(
            queryset=MeaningList.objects.all(),
            empty_label=None,
            widget=forms.Select(attrs={"onchange":"this.form.submit()"}))

class ChooseNexusOutputForm(forms.Form):
    DIALECT = (("BP", "BayesPhylogenies"),
            ("NN", "NeighborNet"),
            ("MB", "MrBayes"))
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
    unique = forms.BooleanField(label="Include unique states")
    dialect = forms.ChoiceField(choices=DIALECT,
            widget=forms.RadioSelect,
            label="NEXUS dialect")

class ChooseSourceForm(forms.Form):
    source = ChooseSourcesField(queryset=Source.objects.all())

class EditCitationForm(forms.Form):
    pages = forms.CharField(required=False)
    reliability = forms.ChoiceField(choices=RELIABILITY_CHOICES,
            widget=forms.RadioSelect)
    comment = forms.CharField(widget=forms.Textarea, required=False)

class EditCognateClassCitationForm(forms.ModelForm):

    def validate_unique(self):
        """Calls the instance's validate_unique() method and updates the
        form's validation errors if any were raised. See:
        http://neillyons.co/articles/IntegrityError-with-djangos-unique-together-constraint/
        """
        exclude = self._get_validation_exclusions()
        exclude.remove("cognate_class") # remove our previously excluded field from the list.
        try:
            self.instance.validate_unique(exclude=exclude)
        except ValidationError, e:
            self._update_errors(e.message_dict)

    class Meta:
        model = CognateClassCitation
        exclude = ["cognate_class"]

class AddCitationForm(forms.Form):
    source = ChooseOneSourceField(queryset=Source.objects.all(),
            help_text="")
    pages = forms.CharField(required=False)
    reliability = forms.ChoiceField(choices=RELIABILITY_CHOICES,
            widget=forms.RadioSelect)
    comment = forms.CharField(widget=forms.Textarea, required=False)

class ChooseCognateClassForm(forms.Form):
    cognate_class = ChooseCognateClassField(queryset=CognateClass.objects.all(),
            widget=forms.Select(attrs={"onchange":"this.form.submit()"}),
            empty_label="---", # make this into the "new" button?
            label="")

class EditCognateSetForm(forms.ModelForm):
    notes = forms.CharField(widget=forms.Textarea, required=False)

def make_reorder_languagelist_form(objlist):
    choices = [(e.id, e.ascii_name) for e in objlist]
    class ReorderLanguageListForm(forms.Form):
        language = forms.ChoiceField(
                choices=choices,
                widget=forms.Select(attrs={"size":20}))
    return ReorderLanguageListForm

def make_reorder_meaninglist_form(objlist):
    choices = [(e.id, e.gloss) for e in objlist]
    class ReorderMeaningListForm(forms.Form):
        meaning = forms.ChoiceField(
                choices=choices,
                widget=forms.Select(attrs={"size":20}))
    return ReorderMeaningListForm

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
                "comment":forms.Textarea(),
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

class SearchLexemeForm(forms.Form):
    SEARCH_FIELD_CHOICES = [("L", "Search phonological and source form"),
            ("E", "Search gloss, meaning and notes")]
    regex = forms.CharField()
    search_fields = forms.ChoiceField(widget=forms.RadioSelect(),
            choices=SEARCH_FIELD_CHOICES, initial="L")
    languages = ChooseLanguagesField(queryset=Language.objects.all(),
            required=False,
            widget=forms.SelectMultiple(attrs={"size":min(40,
                    Language.objects.count())}),
            help_text=u"no selection → all")
