from django import forms
# from ielex.views import get_languages
from ielex.lexicon.models import Language, Source, LanguageList, CognateSet

class ChooseLanguageField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.utf8_name or obj.ascii_name

class ChooseLanguageListField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name

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

class AddNewWordForm(forms.Form):
    # needs some custom validation: requires one of source_form and phon_form,
    # and will copy source_form to phon_form if empty
    language = ChooseLanguageField(queryset=Language.objects.all()) #
    source_form = forms.CharField(required=False)
    phon_form = forms.CharField(required=False)
    notes = forms.CharField(
            widget=forms.Textarea,
            label="Notes",
            required=False)

class EditLexemeForm(forms.Form):
    # needs some custom validation: requires one of source_form and phon_form,
    # and will copy source_form to phon_form if empty
    source_form = forms.CharField(required=False)
    phon_form = forms.CharField(required=False)
    notes = forms.CharField(
            widget=forms.Textarea,
            label="Notes",
            required=False)
    # sources = ChooseSourcesField(queryset=Source.objects.all())

class EditSourceForm(forms.ModelForm):
    type_code = forms.ChoiceField(choices=Source.TYPE_CHOICES,
            widget=forms.RadioSelect())
    class Meta:
        model = Source

class ChooseLanguageForm(forms.Form):
    language = ChooseLanguageField(queryset=Language.objects.all(),
            widget=forms.Select(attrs={"onchange":"this.form.submit()"}))

class ChooseLanguageListForm(forms.Form):
    language_list = ChooseLanguageListField(
            queryset=LanguageList.objects.all(),
            widget=forms.Select(attrs={"onchange":"this.form.submit()"}))

class ChooseSourceForm(forms.Form):
    source = ChooseSourcesField(queryset=Source.objects.all())

class EditCitationForm(forms.Form):
    pages = forms.CharField(required=False)
    reliability = forms.ChoiceField(choices=Source.RELIABILITY_CHOICES,
            widget=forms.RadioSelect)

class AddCitationForm(forms.Form):
    source = ChooseOneSourceField(queryset=Source.objects.all())
    pages = forms.CharField(required=False)
    reliability = forms.ChoiceField(choices=Source.RELIABILITY_CHOICES,
            widget=forms.RadioSelect)

class ChooseCognateClassForm(forms.Form):
    cognate_class = ChooseCognateClassField(queryset=CognateSet.objects.all(),
            widget=forms.Select(attrs={"onchange":"this.form.submit()"}),
            empty_label="---",
            label="")
