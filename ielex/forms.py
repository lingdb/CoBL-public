from django import forms
from ielex.views import get_languages
from ielex.lexicon.models import Language, Source


class ChooseLanguageField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.utf8_name or obj.ascii_name


class ChooseSourceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        def truncate(s, l):
            if len(s) < l:
                return s
            else:
                return s[:l-4]+" ..."
        return truncate(obj.citation_text, 164)


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


class EnterNewSourceForm(forms.ModelForm):
    class Meta:
        model = Source


class ChooseLanguageForm(forms.Form):
    language = ChooseLanguageField(queryset=Language.objects.all(),
            widget=forms.Select(attrs={"onchange":"this.form.submit()"}))


class ChooseSourceForm(forms.Form):
    source = ChooseSourceField(queryset=Source.objects.all())
