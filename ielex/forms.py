# -*- coding: utf-8 -*-
import re
from django import forms
from django.forms import ValidationError
from ielex.lexicon.models import *
from ielex.lexicon.validators import suitable_for_url
# from ielex.extensional_semantics.models import *

from wtforms import StringField, IntegerField, \
    FieldList, FormField, \
    TextField, BooleanField, \
    DateTimeField, DecimalField, \
    TextAreaField
from wtforms.validators import DataRequired
from wtforms_components import read_only
from wtforms.form import Form as WTForm
from wtforms.ext.django.orm import model_form
from lexicon.models import Lexeme

LexemeForm = model_form(Lexeme)


def clean_value_for_url(instance, field_label):
    """Check that a string in a form field is suitable to be part of a url"""
    # TODO compare the suitable_for_url validator
    data = instance.cleaned_data[field_label]
    data = data.strip()
    suitable_for_url(data)
    # illegal_chars = re.findall(r"[^a-zA-Z0-9$\-_\.+!*'(),]", data)
    # try:
    #     assert not illegal_chars
    # except AssertionError:
    #     raise ValidationError("Invalid character/s for an ascii label:"\
    #             " '%s'" % "', '".join(illegal_chars))
    return data


def strip_whitespace(instance, field_label):
    """Strip the whitespace from around a form field before validation"""
    data = instance.cleaned_data[field_label]
    return data.strip()


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


class AddLexemeForm(forms.ModelForm):

    language = ChooseLanguageField(queryset=Language.objects.all())
    meaning = ChooseMeaningField(
        queryset=Meaning.objects.all(),
        help_text="e.g. Swadesh meaning", required=False)
    gloss = forms.CharField(required=False, help_text="""The actual gloss of
            this lexeme, may be different to 'meaning'""")

    def clean_source_form(self):
        return strip_whitespace(self, "source_form")

    def clean_phon_form(self):
        return strip_whitespace(self, "phon_form")

    class Meta:
        model = Lexeme
        exclude = ["cognate_class", "source"]


class EditLexemeForm(forms.ModelForm):

    meaning = ChooseMeaningField(
        queryset=Meaning.objects.all(),
        help_text="e.g. Swadesh meaning", required=False)
    gloss = forms.CharField(required=False, help_text="""The actual gloss of
            this lexeme, may be different to 'meaning'""")

    class Meta:
        model = Lexeme
        exclude = ["language", "cognate_class", "source"]


class EditSourceForm(forms.ModelForm):

    type_code = forms.ChoiceField(
        choices=TYPE_CHOICES, widget=forms.RadioSelect())

    class Meta:
        model = Source
        fields = "__all__"


class EditLanguageForm(forms.ModelForm):

    def clean_ascii_name(self):
        return clean_value_for_url(self, "ascii_name")

    def clean_utf8_name(self):
        return strip_whitespace(self, "utf8_name")

    class Meta:
        model = Language
        fields = "__all__"


class EditMeaningForm(forms.ModelForm):

    def clean_gloss(self):
        return clean_value_for_url(self, "gloss")

    class Meta:
        model = Meaning
        fields = ["gloss", "description", "notes"]


class EditMeaningListForm(forms.ModelForm):

    def clean_gloss(self):
        return clean_value_for_url(self, "name")

    class Meta:
        model = MeaningList
        exclude = ["meaning_ids"]


class ChooseLanguageForm(forms.Form):
    # Need to think about the default sort order of the Language objects here
    # It might make sense to have it alphabetical
    language = ChooseLanguageField(
        queryset=Language.objects.all(),
        widget=forms.Select(attrs={"onchange": "this.form.submit()"}))


class AddLanguageListForm(forms.ModelForm):
    help_text = "The new language list will start as a clone of this one"
    language_list = ChooseLanguageListField(
            queryset=LanguageList.objects.all(),
            empty_label=None,
            widget=forms.Select(),
            help_text=help_text)

    class Meta:
        model = LanguageList
        exclude = ["languages"]


class EditLanguageListForm(forms.ModelForm):

    def clean_name(self):
        return clean_value_for_url(self, "name")

    class Meta:
        model = LanguageList
        exclude = ["languages"]


class EditLanguageListMembersForm(forms.Form):
    included_languages = ChooseIncludedLanguagesField(
            required=False, empty_label=None,
            queryset=Language.objects.none(),
            widget=forms.Select(
                attrs={"size": 20, "onchange": "this.form.submit()"}))
    excluded_languages = ChooseExcludedLanguagesField(
            required=False, empty_label=None,
            queryset=Language.objects.all(),
            widget=forms.Select(
                attrs={"size": 20, "onchange": "this.form.submit()"}))


class LanguageListRowForm(WTForm):
    iso_code = StringField('Language ISO Code', validators=[DataRequired()])
    utf8_name = StringField('Language Utf8 Name', validators=[DataRequired()])
    ascii_name = StringField('Language ASCII Name',
                             validators=[DataRequired()])
    glottocode = StringField('Glottocode', validators=[DataRequired()])
    variety = StringField('Language Variety', validators=[DataRequired()])
    foss_stat = BooleanField('Fossile Status', validators=[DataRequired()])
    low_stat = BooleanField('Low Status', validators=[DataRequired()])
    soundcompcode = StringField('Sound Comparisons Code',
                                validators=[DataRequired()])
    level0 = StringField('Level 0 Branch', validators=[DataRequired()])
    level1 = StringField('Level 1 Branch', validators=[DataRequired()])
    level2 = StringField('Level 2 Branch', validators=[DataRequired()])
    representative = BooleanField('Representative',
                                  validators=[DataRequired()])
    mgs_count = IntegerField('Meaning Count', validators=[DataRequired()])
    lex_count = IntegerField('Lexeme Count', validators=[DataRequired()])
    entd_count = IntegerField('Entry Count', validators=[DataRequired()])
    excess_count = IntegerField('Excess Count', validators=[DataRequired()])
    mean_timedepth_BP_years = IntegerField('Mean of Time Depth BP (years)',
                                           validators=[DataRequired()])
    std_deviation_timedepth_BP_years = IntegerField(
        'Standard Deviation of Time Depth BP (years)',
        validators=[DataRequired()])
    rfcWebPath1 = StringField('This Lg lex rfc web path 1',
                              validators=[DataRequired()])
    rfcWebPath2 = StringField('This Lg lex rfc web path 2',
                              validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    reviewer = StringField('Reviewer', validators=[DataRequired()])


class AddLanguageListTableForm(WTForm):
    langlist = FieldList(FormField(LanguageListRowForm))


class LanguageBranchesRowForm(WTForm):
    idField = IntegerField('Id')
    family_ix = IntegerField('Family Ix', validators=[DataRequired()])
    level1_branch_ix = IntegerField('Level1 Branch Ix',
                                    validators=[DataRequired()])
    level1_branch_name = StringField('Level 1 Branch Name',
                                     validators=[DataRequired()])
    shortName = StringField('Short name', validators=[DataRequired()])
    hexColor = StringField('hexColor', validators=[DataRequired()])


class LanguageBranchesTableForm(WTForm):
    elements = FieldList(FormField(LanguageBranchesRowForm))


class LexemeRowForm(WTForm):
    id = IntegerField('Lexeme Id', validators=[DataRequired()])
    language_id = StringField('Language Id', validators=[DataRequired()])
    language = StringField('Language', validators=[DataRequired()])
    language_asciiname = StringField('Language Ascii Name',
                                     validators=[DataRequired()])
    language_utf8name = StringField('Language Utf8 Name',
                                    validators=[DataRequired()])
    cognate_class_links = StringField('Cognate Class',
                                      validators=[DataRequired()])
    meaning_id = IntegerField('Meaning Id', validators=[DataRequired()])
    meaning = IntegerField('Meaning', validators=[DataRequired()])
    source_form = StringField('Source Form', validators=[DataRequired()])
    phon_form = StringField('PhoNetic Form', validators=[DataRequired()])
    phoneMic = StringField('PhoneMic Form', validators=[DataRequired()])
    transliteration = StringField('Transliteration',
                                  validators=[DataRequired()])
    not_swadesh_term = BooleanField('Not Swadesh Term',
                                    validators=[DataRequired()])
    gloss = StringField('Gloss', validators=[DataRequired()])
    number_cognate_coded = IntegerField('Count Coded Cognates',
                                        validators=[DataRequired()])
    notes = TextField('Notes', validators=[DataRequired()])
    cogclass_link = TextField('CogClass Links', validators=[DataRequired()])
    rfcWebLookup1 = StringField('This Lg lex rfc web path 1',
                                validators=[DataRequired()])
    rfcWebLookup2 = StringField('This Lg lex rfc web path 2',
                                validators=[DataRequired()])
    dubious = BooleanField('Dubious', validators=[DataRequired()])

    # Components for copying buttons
    source_form_2_transliteration = BooleanField(
        'Source Form to Transliteration', validators=[DataRequired()])
    transliteration_2_source_form = BooleanField(
        'Transliteration to Source Form', validators=[DataRequired()])
    phon_form_2_phoneMic = BooleanField('PhoneTic to PhoneMic',
                                        validators=[DataRequired()])
    phoneMic_2_phon_form = BooleanField('PhoneMic to PhoneTic',
                                        validators=[DataRequired()])

    cog_class_ids = StringField('Root Form', validators=[DataRequired()])
    root_form = StringField('Root Form', validators=[DataRequired()])
    rootFormCompare = StringField('Root Form Compare')
    root_language = StringField('Root Language', validators=[DataRequired()])
    rootLanguageCompare = StringField('Root Language Compare')

    # Exclusion booleans:
    is_excluded = BooleanField('Is Excluded', validators=[DataRequired()])
    is_loan = BooleanField('Is Loan', validators=[DataRequired()])

    # LoanEvent for #29:
    loan_event = BooleanField('Loan Event', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(LexemeRowForm, self).__init__(*args, **kwargs)
        read_only(self.meaning_id)
        read_only(self.meaning)
        read_only(self.language_utf8name)


class AddLexemesTableForm(WTForm):
    # Default of at least 5 blank fields
    lexemes = FieldList(FormField(LexemeRowForm))


# TODO: return to this if/when moving to Python 3
@python_2_unicode_compatible
class CogClassRowForm(WTForm):
    cogclass_id = IntegerField('Cog Class Id', validators=[DataRequired()])
    alias = StringField('Cog Class Alias', validators=[DataRequired()])
    modified = DateTimeField('Date Modified', validators=[DataRequired()])
    cogclass_name = StringField('Cog Class Name', validators=[DataRequired()])
    root_form = StringField('Cog Class Root', validators=[DataRequired()])
    root_language = StringField('Root Language', validators=[DataRequired()])
    gloss_in_root_lang = StringField('Gloss in Root Language',
                                     validators=[DataRequired()])
    loanword = BooleanField('Loanword', validators=[DataRequired()])
    notes = TextField('Notes', validators=[DataRequired()])
    loan_source = TextField('Loan Source', validators=[DataRequired()])
    loan_notes = TextField('Loan Notes', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(CogClassRowForm, self).__init__(*args, **kwargs)
        read_only(self.cogclass_id)
        read_only(self.alias)

    def __str__(self):
        cogclass_form_vals = (
                              str(self.cogclass_id),
                              self.alias,
                              self.root_form,  # .encode('ascii', 'replace'),
                              self.root_language,
                              self.gloss_in_root_lang,
                              str(self.loanword),
                              self.notes
                              )
        tmpl = '( id=%s, root=%s, language=%s, gloss=%s, '\
               'alias=%s, loanword=%s, notes=%s )'
        return tmpl % cogclass_form_vals


class AddCogClassTableForm(WTForm):
    # Default of at least 5 blank fields
    cogclass = FieldList(FormField(CogClassRowForm))


class LexemeTableFilterForm(forms.ModelForm):

    class Meta:
        model = Lexeme
        fields = ['meaning']  # , 'cognate_class']


class MeaningTableFilterForm(forms.ModelForm):

    class Meta:
        model = Lexeme
        fields = ['language']


class MeaningListRowForm(WTForm):
    meaningId = IntegerField('Meaning Id', validators=[DataRequired()])
    gloss = StringField('Gloss', validators=[DataRequired()])
    desc = StringField('Description', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[DataRequired()])
    percent_coded = DecimalField('Percentage coded',
                                 validators=[DataRequired()])
    lex_count = IntegerField('Lexeme Count', validators=[DataRequired()])
    cog_count = IntegerField('Cognate Class Count',
                             validators=[DataRequired()])


class MeaningListTableForm(WTForm):
    meanings = FieldList(FormField(MeaningListRowForm))


class ChooseSourceForm(forms.Form):
    source = ChooseSourcesField(queryset=Source.objects.all())


class EditCitationForm(forms.Form):
    pages = forms.CharField(required=False)
    reliability = forms.ChoiceField(
        choices=RELIABILITY_CHOICES, widget=forms.RadioSelect)
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 78, 'rows': 20}), required=False)


class EditCognateClassCitationForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 78, 'rows': 20}), required=False)

    def validate_unique(self):
        """Calls the instance's validate_unique() method and updates the
        form's validation errors if any were raised. See:
        http://neillyons.co/articles/IntegrityError-with-djangos-unique-together-constraint/
        """
        exclude = self._get_validation_exclusions()
        # remove our previously excluded field from the list.
        exclude.remove("cognate_class")
        try:
            self.instance.validate_unique(exclude=exclude)
        except ValidationError, e:
            self._update_errors(e.message_dict)

    class Meta:
        model = CognateClassCitation
        fields = ["source", "pages", "reliability", "comment"]


class AddCitationForm(forms.Form):
    source = ChooseOneSourceField(
        queryset=Source.objects.all(), help_text="")
    pages = forms.CharField(required=False)
    reliability = forms.ChoiceField(
        choices=RELIABILITY_CHOICES, widget=forms.RadioSelect)
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 78, 'rows': 20}), required=False)


class ChooseCognateClassForm(forms.Form):
    cognate_class = ChooseCognateClassField(
        queryset=CognateClass.objects.all(),
        widget=forms.Select(attrs={"onchange": "this.form.submit()"}),
        empty_label="---",  # make this into the "new" button?
        label="")


class EditCognateClassNameForm(forms.ModelForm):
    name = forms.CharField(required=False)

    class Meta:
        model = CognateClass
        fields = ["name"]


class EditCognateClassNotesForm(forms.ModelForm):
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 78, 'rows': 20}), required=False)

    class Meta:
        model = CognateClass
        fields = ["notes"]


def make_reorder_languagelist_form(objlist):
    choices = [(e.id, e.ascii_name) for e in objlist]

    class ReorderLanguageListForm(forms.Form):
        language = forms.ChoiceField(
            choices=choices,
            widget=forms.Select(attrs={"size": 20}))
    return ReorderLanguageListForm


def make_reorder_meaninglist_form(objlist):
    choices = [(e.id, e.gloss) for e in objlist]

    class ReorderMeaningListForm(forms.Form):
        meaning = forms.ChoiceField(
            choices=choices,
            widget=forms.Select(attrs={"size": 20}))
    return ReorderMeaningListForm


class SearchLexemeForm(forms.Form):
    SEARCH_FIELD_CHOICES = [
        ("L", "Search phonological and source form"),
        ("E", "Search gloss, meaning and notes")]
    regex = forms.CharField()
    search_fields = forms.ChoiceField(
        widget=forms.RadioSelect(), choices=SEARCH_FIELD_CHOICES, initial="L")
    languages = ChooseLanguagesField(
        queryset=Language.objects.all(),
        required=False, widget=forms.SelectMultiple(
            attrs={"size": min(40, Language.objects.count())}),
        help_text=u"no selection → all")


class AuthorRowForm(WTForm):
    idField = IntegerField('Id')
    surname = StringField('Author Surname', validators=[DataRequired()])
    firstNames = StringField('Author First names', validators=[DataRequired()])
    email = StringField('Email address', validators=[DataRequired()])
    website = StringField('Personal website URL', validators=[DataRequired()])
    initials = StringField('Initials', validators=[DataRequired()])


class AuthorTableForm(WTForm):
    elements = FieldList(FormField(AuthorRowForm))
