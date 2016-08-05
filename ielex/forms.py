# -*- coding: utf-8 -*-
import json
from django import forms
from django.forms import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from ielex.lexicon.models import CognateClass, \
                                 CognateClassCitation, \
                                 DISTRIBUTION_CHOICES, \
                                 Language, \
                                 LanguageList, \
                                 Meaning, \
                                 MeaningList, \
                                 Source, \
                                 TYPE_CHOICES
from ielex.lexicon.validators import suitable_for_url, suitable_for_url_wtforms
# from ielex.extensional_semantics.models import *

from wtforms import StringField, \
                    IntegerField, \
                    FieldList, \
                    FormField, \
                    TextField, \
                    BooleanField, \
                    DateTimeField, \
                    TextAreaField, \
                    SelectField
from wtforms.validators import Email, InputRequired
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
        fields = ["language", "meaning", "gloss", "source_form", "phon_form"]


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
        fields = ['ascii_name', 'utf8_name']


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


class AbstractTimestampedForm(WTForm):
    lastTouched = DateTimeField('Last changed', validators=[InputRequired()])
    lastEditedBy = StringField('Last edited')


class LanguageListRowForm(AbstractTimestampedForm):
    idField = IntegerField('Language id', validators=[InputRequired()])
    iso_code = StringField('ISO code', validators=[InputRequired()])
    utf8_name = StringField('Display name', validators=[InputRequired()])
    ascii_name = StringField(
        'URL name', validators=[InputRequired(), suitable_for_url_wtforms])
    glottocode = StringField('Glottocode', validators=[InputRequired()])
    variety = StringField('Language Variety', validators=[InputRequired()])
    foss_stat = BooleanField('Fossilised Status', validators=[InputRequired()])
    low_stat = BooleanField('Low Status', validators=[InputRequired()])
    soundcompcode = StringField('Sound Comparisons Code',
                                validators=[InputRequired()])
    level0 = IntegerField('Clade level 0', validators=[InputRequired()])
    level1 = IntegerField('Clade level 1', validators=[InputRequired()])
    level2 = IntegerField('Clade level 2', validators=[InputRequired()])
    level3 = IntegerField('Clade level 3', validators=[InputRequired()])
    representative = BooleanField('Representative',
                                  validators=[InputRequired()])
    mean_timedepth_BP_years = IntegerField('Mean of Time Depth BP (years)',
                                           validators=[InputRequired()])
    std_deviation_timedepth_BP_years = IntegerField(
        'Standard Deviation of Time Depth BP (years)',
        validators=[InputRequired()])
    rfcWebPath1 = StringField('This Lg lex rfc web path 1',
                              validators=[InputRequired()])
    rfcWebPath2 = StringField('This Lg lex rfc web path 2',
                              validators=[InputRequired()])
    author = StringField('Author', validators=[InputRequired()])
    reviewer = StringField('Reviewer', validators=[InputRequired()])
    earliestTimeDepthBound = IntegerField('Earliest Time-Depth Bound',
                                          validators=[InputRequired()])
    latestTimeDepthBound = IntegerField('Latest Time-Depth Bound',
                                        validators=[InputRequired()])
    progress = IntegerField('Progress on this language',
                            validators=[InputRequired()])
    sortRankInClade = IntegerField(
        'Sort rank in clade', validators=[InputRequired()])
    entryTimeframe = StringField('Entry timeframe',
                                 validators=[InputRequired()])
    historical = BooleanField('Historical', validators=[InputRequired()])

    def validate_historical(form, field):
        # Assumes that field.data :: True | False
        if field.data:
            mean_timedepth_BP_years = form.data['mean_timedepth_BP_years']
            if mean_timedepth_BP_years is None:
                raise ValidationError('mean_timedepth_BP_years is None '
                                      'but historical is True.')
            if mean_timedepth_BP_years <= 0:
                raise ValidationError('mean_timedepth_BP_years must be > 0, '
                                      'but is %i.' % mean_timedepth_BP_years)
        else:
            for k in ['mean_timedepth_BP_years',
                      'std_deviation_timedepth_BP_years',
                      'earliestTimeDepthBound',
                      'latestTimeDepthBound']:
                value = form.data[k]
                if value is not None and value != 0:
                    raise ValidationError('Field %s should be None or 0, '
                                          'but is: "%s"' % (k, value))


class AddLanguageListTableForm(WTForm):
    langlist = FieldList(FormField(LanguageListRowForm))


class CladeRowForm(AbstractTimestampedForm):
    idField = IntegerField('Id', validators=[InputRequired()])
    cladeName = StringField('Clade Name', validators=[InputRequired()])
    shortName = StringField('Short name', validators=[InputRequired()])
    hexColor = StringField('hexColor', validators=[InputRequired()])
    export = BooleanField('Export?', validators=[InputRequired()])
    exportDate = BooleanField('Export Date?', validators=[InputRequired()])
    taxonsetName = StringField('Texonset name', validators=[InputRequired()])
    atMost = IntegerField('At most?', validators=[InputRequired()])
    atLeast = IntegerField('At least?', validators=[InputRequired()])
    distribution = SelectField('Distribution type',
                               choices=DISTRIBUTION_CHOICES,
                               validators=[InputRequired()])
    logNormalOffset = IntegerField('[Offset]', validators=[InputRequired()])
    logNormalMean = IntegerField('Mean', validators=[InputRequired()])
    logNormalStDev = IntegerField('StDev', validators=[InputRequired()])
    normalMean = IntegerField('Mean', validators=[InputRequired()])
    normalStDev = IntegerField('StDev', validators=[InputRequired()])
    uniformUpper = IntegerField('Upper', validators=[InputRequired()])
    uniformLower = IntegerField('Lower', validators=[InputRequired()])
    cladeLevel0 = IntegerField('Clade Level 0',
                               validators=[InputRequired()])
    cladeLevel1 = IntegerField('Clade Level 1',
                               validators=[InputRequired()])
    cladeLevel2 = IntegerField('Clade Level 2',
                               validators=[InputRequired()])
    cladeLevel3 = IntegerField('Clade Level 3',
                               validators=[InputRequired()])
    level0Name = StringField('Level 0 name', validators=[InputRequired()])
    level1Name = StringField('Level 1 name', validators=[InputRequired()])
    level2Name = StringField('Level 2 name', validators=[InputRequired()])
    level3Name = StringField('Level 3 name', validators=[InputRequired()])


class CladeTableForm(WTForm):
    elements = FieldList(FormField(CladeRowForm))


class CladeCreationForm(WTForm):
    cladeName = StringField('Clade name', validators=[InputRequired()])
    cladeLevel0 = IntegerField('Clade level 0', validators=[InputRequired()])
    cladeLevel1 = IntegerField('Clade level 1', validators=[InputRequired()])
    cladeLevel2 = IntegerField('Clade level 2', validators=[InputRequired()])
    cladeLevel3 = IntegerField('Clade level 3', validators=[InputRequired()])


class CladeDeletionForm(WTForm):
    cladeName = StringField('Clade name', validators=[InputRequired()])


class SndCompRowForm(AbstractTimestampedForm):
    idField = IntegerField('Id', validators=[InputRequired()])
    lgSetName = StringField('Language set name', validators=[InputRequired()])
    lv0 = IntegerField('SndComp branch level 0', validators=[InputRequired()])
    lv1 = IntegerField('SndComp branch level 1', validators=[InputRequired()])
    lv2 = IntegerField('SndComp branch level 2', validators=[InputRequired()])
    lv3 = IntegerField('SndComp branch level 3', validators=[InputRequired()])
    cladeLevel0 = IntegerField('Clade level 0', validators=[InputRequired()])
    cladeLevel1 = IntegerField('Clade level 1', validators=[InputRequired()])
    cladeLevel2 = IntegerField('Clade level 2', validators=[InputRequired()])
    cladeLevel3 = IntegerField('Clade level 3', validators=[InputRequired()])


class SndCompTableForm(WTForm):
    elements = FieldList(FormField(SndCompRowForm))


class SndCompCreationForm(WTForm):
    lgSetName = StringField('Language set name', validators=[InputRequired()])
    lv0 = IntegerField('SndComp branch level 0', validators=[InputRequired()])
    lv1 = IntegerField('SndComp branch level 1', validators=[InputRequired()])
    lv2 = IntegerField('SndComp branch level 2', validators=[InputRequired()])
    lv3 = IntegerField('SndComp branch level 3', validators=[InputRequired()])
    # Clade levels are not required:
    cladeLevel1 = IntegerField('Clade level 0')
    cladeLevel1 = IntegerField('Clade level 1')
    cladeLevel2 = IntegerField('Clade level 2')
    cladeLevel3 = IntegerField('Clade level 3')


class SndCompDeletionForm(WTForm):
    lgSetName = StringField('Language set name', validators=[InputRequired()])


# TODO: return to this if/when moving to Python 3
@python_2_unicode_compatible
class CogClassRowForm(AbstractTimestampedForm):
    idField = IntegerField('Id', validators=[InputRequired()])
    alias = StringField('Cog Class Alias', validators=[InputRequired()])
    cogclass_name = StringField('Cog Class Name', validators=[InputRequired()])
    root_form = StringField('Cog Class Root', validators=[InputRequired()])
    root_language = StringField('Root Language', validators=[InputRequired()])
    gloss_in_root_lang = StringField('Gloss in Root Language',
                                     validators=[InputRequired()])
    loanword = BooleanField('Loanword', validators=[InputRequired()])
    notes = TextField('Notes', validators=[InputRequired()])
    loan_source = TextField('Loan Source', validators=[InputRequired()])
    loan_notes = TextField('Loan Notes', validators=[InputRequired()])
    loanSourceId = IntegerField(
        'Id of related cc', validators=[InputRequired()])
    loanEventTimeDepthBP = StringField(
        'Time depth of loan event', validators=[InputRequired()])
    sourceFormInLoanLanguage = TextField(
        'Source form in loan language', validators=[InputRequired()])
    parallelLoanEvent = BooleanField(
        'Parallel Loan Event', validators=[InputRequired()])
    notProtoIndoEuropean = BooleanField(
        'Not Proto-Indo-European?', validators=[InputRequired()])
    # Added when mobbing 2016-08-04:
    idiophonic = BooleanField('Idiophonic', validators=[InputRequired()])
    parallelDerivation = BooleanField('Parallel Derivation',
                                      validators=[InputRequired()])
    dubiousSet = BooleanField('Dubious set', validators=[InputRequired()])

    def __str__(self):
        cogclass_form_vals = (
                              str(self.idField),
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
    cogclass = FieldList(FormField(CogClassRowForm))


class MergeCognateClassesForm(WTForm):
    mergeIds = StringField('merge ids', validators=[InputRequired()])


class CognateJudgementSplitRow(AbstractTimestampedForm):
    idField = IntegerField('Id', validators=[InputRequired()])
    splitOff = BooleanField('Checked implies split off',
                            validators=[InputRequired()],
                            default=False)


class CognateJudgementSplitTable(WTForm):
    judgements = FieldList(FormField(CognateJudgementSplitRow))


class LexemeRowViewMeaningsForm(AbstractTimestampedForm):
    '''
    Since WTForms always fills fields with their default values
    we need different forms for cases where different fields are presented.
    This form aims to be used by the `view_meaning` function.
    '''
    id = IntegerField('Lexeme Id', validators=[InputRequired()])
    language_asciiname = StringField('Language Ascii Name',
                                     validators=[InputRequired()])
    language_utf8name = StringField('Language Utf8 Name',
                                    validators=[InputRequired()])
    source_form = StringField('Source Form', validators=[InputRequired()])
    phon_form = StringField('PhoNetic Form', validators=[InputRequired()])
    phoneMic = StringField('PhoneMic Form', validators=[InputRequired()])
    transliteration = StringField('Transliteration',
                                  validators=[InputRequired()])
    not_swadesh_term = BooleanField('Not Swadesh Term',
                                    validators=[InputRequired()])
    gloss = StringField('Gloss', validators=[InputRequired()])
    notes = TextField('Notes', validators=[InputRequired()])
    cogclass_link = TextField('CogClass Links', validators=[InputRequired()])


class LexemeTableViewMeaningsForm(WTForm):
    lexemes = FieldList(FormField(LexemeRowViewMeaningsForm))


class LexemeTableEditCognateClassesForm(WTForm):
    lexemeIds = StringField('Lexeme ids', validators=[InputRequired()])
    cognateClassAssignments = StringField('Cognate class assignments ids',
                                          validators=[InputRequired()])

    _validated = dict()

    def getValidated(self):
        return self._validated

    def validate_lexemeIds(form, field):
        # Parse ids:
        ids = [int(x) for x in field.data.split(',')]
        # Check ids belonging to lexemes with common meaning:
        mIds = set(Lexeme.objects.filter(id__in=ids).values_list(
            'meaning__id', flat=True))
        if len(mIds) != 1:
            raise ValidationError('Given lexemes belong to %s meanings '
                                  'rather than a single one.' % len(mIds))
        # Write validated data to form.data:
        form._validated['lexemeIds'] = ids

    def validate_cognateClassAssignments(form, field):
        # Make sure field.data is a json dict:
        data = json.loads(field.data)
        if type(data) != dict:
            raise ValidationError('Data for cognateClassAssignments '
                                  'is not a JSON object.')
        # Dict to put into _validated:
        retData = dict()  # :: int | 'new' -> int | 'new' | 'delete'
        # Validating data:
        cIdSet = set()
        # Gathering IDs allowing other keywords:
        for k, v in data.iteritems():
            if k != 'new':
                cIdSet.add(int(k))
                k = int(k)
            if v != 'new' and v != 'delete':
                cIdSet.add(int(v))
                v = int(v)
            retData[k] = v
        # Make sure cIdSet consists of valid cognate class IDs:
        cCount = CognateClass.objects.filter(id__in=cIdSet).count()
        if cCount != len(cIdSet):
            raise ValidationError('At least one of the given '
                                  'cognate class IDs could not be '
                                  'found in the database.')
        # Write validated data to form.data:
        form._validated['cognateClassAssignments'] = retData


class LexemeRowLanguageWordlistForm(AbstractTimestampedForm):
    id = IntegerField('Lexeme Id', validators=[InputRequired()])
    language_id = StringField('Language Id', validators=[InputRequired()])
    language = StringField('Language', validators=[InputRequired()])
    language_asciiname = StringField('Language Ascii Name',
                                     validators=[InputRequired()])
    language_utf8name = StringField('Language Utf8 Name',
                                    validators=[InputRequired()])
    cognate_class_links = StringField('Cognate Class',
                                      validators=[InputRequired()])
    meaning_id = IntegerField('Meaning Id', validators=[InputRequired()])
    meaning = IntegerField('Meaning', validators=[InputRequired()])
    source_form = StringField('Source Form', validators=[InputRequired()])
    phon_form = StringField('PhoNetic Form', validators=[InputRequired()])
    phoneMic = StringField('PhoneMic Form', validators=[InputRequired()])
    transliteration = StringField('Transliteration',
                                  validators=[InputRequired()])
    not_swadesh_term = BooleanField('Not Swadesh Term',
                                    validators=[InputRequired()])
    gloss = StringField('Gloss', validators=[InputRequired()])
    notes = TextField('Notes', validators=[InputRequired()])
    cogclass_link = TextField('CogClass Links', validators=[InputRequired()])
    rfcWebLookup1 = StringField('This Lg lex rfc web path 1',
                                validators=[InputRequired()])
    rfcWebLookup2 = StringField('This Lg lex rfc web path 2',
                                validators=[InputRequired()])
    dubious = BooleanField('Dubious', validators=[InputRequired()])


class LexemeTableLanguageWordlistForm(WTForm):
    lexemes = FieldList(FormField(LexemeRowLanguageWordlistForm))


class CloneLanguageForm(WTForm):
    sourceLanguageName = StringField(
        'Name of source language',
        validators=[InputRequired(),
                    suitable_for_url_wtforms])
    languageName = StringField(
        'Name of new language',
        validators=[InputRequired(),
                    suitable_for_url_wtforms])
    languageId = IntegerField(
        'Id of the language to clone',
        validators=[InputRequired()])
    emptyLexemes = BooleanField('Should lexemes be emptied?')


class LexemeTableFilterForm(forms.ModelForm):

    class Meta:
        model = Lexeme
        fields = ['meaning']  # , 'cognate_class']


class MeaningTableFilterForm(forms.ModelForm):

    class Meta:
        model = Lexeme
        fields = ['language']


class MeaningListRowForm(AbstractTimestampedForm):
    meaningId = IntegerField('Meaning Id', validators=[InputRequired()])
    gloss = StringField('Gloss', validators=[InputRequired()])
    description = StringField('Description', validators=[InputRequired()])
    notes = TextAreaField('Notes', validators=[InputRequired()])
    doubleCheck = BooleanField('Double check', validators=[InputRequired()])
    exclude = BooleanField('Exclude?', validators=[InputRequired()])


class MeaningListTableForm(WTForm):
    meanings = FieldList(FormField(MeaningListRowForm))


class ChooseSourceForm(forms.Form):
    source = ChooseSourcesField(queryset=Source.objects.all())


class EditCitationForm(forms.Form):
    pages = forms.CharField(required=False)
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
        except ValidationError as e:
            self._update_errors(e.message_dict)

    class Meta:
        model = CognateClassCitation
        fields = ["source", "pages", "reliability", "comment"]


class AddCitationForm(forms.Form):
    source = ChooseOneSourceField(
        queryset=Source.objects.all(), help_text="")
    pages = forms.CharField(required=False)
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 78, 'rows': 20}),
        required=False)


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


class AuthorRowForm(AbstractTimestampedForm):
    idField = IntegerField('Id', validators=[InputRequired()])
    initials = StringField('Initials', validators=[InputRequired()])
    surname = StringField('Author Surname', validators=[InputRequired()])
    firstNames = StringField('Author First names',
                             validators=[InputRequired()])
    email = StringField('Email address', validators=[InputRequired(), Email()])
    website = StringField('Personal website URL', validators=[InputRequired()])


class AuthorTableForm(WTForm):
    elements = FieldList(FormField(AuthorRowForm))


class AuthorCreationForm(WTForm):
    initials = StringField('Initials', validators=[InputRequired()])
    surname = StringField('Author Surname', validators=[InputRequired()])
    firstNames = StringField('Author First names',
                             validators=[InputRequired()])
    email = StringField('Email address', validators=[InputRequired(), Email()])
    website = StringField('Personal website URL', validators=[InputRequired()])


class AuthorDeletionForm(WTForm):
    initials = StringField('Initials', validators=[InputRequired()])
