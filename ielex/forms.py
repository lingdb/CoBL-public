# -*- coding: utf-8 -*-
import json
import logging
import re
from collections import defaultdict
from django import forms
from django.contrib import messages
from django.db import transaction
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
                                 TYPE_CHOICES, \
                                 CognateJudgement, \
                                 Clade
from ielex.lexicon.validators import suitable_for_url, suitable_for_url_wtforms
from wtforms import StringField, \
                    IntegerField, \
                    FieldList, \
                    FormField, \
                    TextField, \
                    BooleanField, \
                    DateTimeField, \
                    TextAreaField, \
                    SelectField, \
                    DecimalField
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


class AddLexemeForm(WTForm):
    language_id = IntegerField('Language:', validators=[InputRequired()])
    meaning_id = IntegerField('Meaning:', validators=[InputRequired()])
    source_form = StringField('Orthographic:', validators=[InputRequired()])
    transliteration = StringField('Transliteration:',
                                  validators=[InputRequired()])
    phon_form = StringField('PhoneTic:', validators=[InputRequired()])
    phoneMic = StringField('phoneMic:', validators=[InputRequired()])

    def validate_language_id(form, field):
        exists = Language.objects.filter(id=field.data).exists()
        if not exists:
            raise ValueError('language_id %s does not exist.' % field.data)

    def validate_meaning_id(form, field):
        exists = Meaning.objects.filter(id=field.data).exists()
        if not exists:
            raise ValueError('meaning_id %s does not exist.' % field.data)


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


class AbstractDistributionForm(WTForm):
    distribution = SelectField('Distribution type',
                               default='_',
                               choices=DISTRIBUTION_CHOICES,
                               validators=[InputRequired()])
    logNormalOffset = IntegerField('[Offset]', validators=[InputRequired()])
    logNormalMean = IntegerField('Mean', validators=[InputRequired()])
    logNormalStDev = DecimalField('StDev', validators=[InputRequired()])
    normalMean = IntegerField('Mean', validators=[InputRequired()])
    normalStDev = IntegerField('StDev', validators=[InputRequired()])
    uniformLower = IntegerField('Lower', validators=[InputRequired()])
    uniformUpper = IntegerField('Upper', validators=[InputRequired()])

    def validate_distribution(form, field):
        wantedFields = {
            'O': ['logNormalOffset', 'logNormalMean', 'logNormalStDev'],
            'L': ['logNormalMean', 'logNormalStDev'],
            'N': ['normalMean', 'normalStDev'],
            'U': ['uniformLower', 'uniformUpper']}
        if field.data in wantedFields:
            for f in wantedFields[field.data]:
                if form[f] is None:
                    raise ValidationError(
                        'Distribution is %s, but field %s is None.' %
                        (field.data, f))


class LanguageListRowForm(AbstractTimestampedForm, AbstractDistributionForm):
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
    notInExport = BooleanField('Not in Export', validators=[InputRequired()])

    def validate_historical(form, field):
        # Assumes that field.data :: True | False
        if field.data:
            distribution = form.data['distribution']
            if distribution is None or distribution == '_':
                raise ValidationError('distribution is None '
                                      'but historical is True.')


class AddLanguageListTableForm(WTForm):
    langlist = FieldList(FormField(LanguageListRowForm))


class CladeRowForm(AbstractTimestampedForm, AbstractDistributionForm):
    idField = IntegerField('Id', validators=[InputRequired()])
    cladeName = StringField('Clade Name', validators=[InputRequired()])
    shortName = StringField('Short name', validators=[InputRequired()])
    hexColor = StringField('hexColor', validators=[InputRequired()])
    export = BooleanField('Export?', validators=[InputRequired()])
    exportDate = BooleanField('Export Date?', validators=[InputRequired()])
    taxonsetName = StringField('Texonset name', validators=[InputRequired()])
    atMost = IntegerField('At most?', validators=[InputRequired()])
    atLeast = IntegerField('At least?', validators=[InputRequired()])
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

    def handle(self, request):
        cladeChanged = False
        idCladeMap = {c.id: c for c in Clade.objects.all()}
        for entry in self.elements:
            data = entry.data
            try:
                clade = idCladeMap[data['idField']]
                if clade.isChanged(**data):
                    problem = clade.setDelta(request, **data)
                    if problem is None:
                        with transaction.atomic():
                            clade.save()
                            cladeChanged = True
                    else:
                        messages.error(
                            request, clade.deltaReport(**problem))
            except Exception:
                logging.exception('Problem saving clade '
                                  'in view_clades.')
                messages.error(request,
                               'Problem saving clade data: %s' % data)
        return cladeChanged


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
    ideophonic = BooleanField('Idiophonic', validators=[InputRequired()])
    parallelDerivation = BooleanField('Parallel Derivation',
                                      validators=[InputRequired()])
    dubiousSet = BooleanField('Dubious set', validators=[InputRequired()])
    # Added for #263:
    revisedYet = BooleanField('Revised Yet?', validators=[InputRequired()])
    revisedBy = TextField('Revised by', validators=[InputRequired()])

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

    def handle(self, request):
        # Extract ids from form:
        ids = set([int(i) for i in
                   self.data['mergeIds'].split(',')])
        # Fetching classes to merge:
        ccs = CognateClass.objects.filter(
            id__in=ids).prefetch_related(
            "cognatejudgement_set",
            "cognateclasscitation_set").all()
        # Checking ccs length:
        if len(ccs) <= 1:
            logging.warning('Not enough cognateclasses to merge.',
                            extra=ccs)
            messages.error(request, 'Sorry, the server needs '
                           '2 or more cognateclasses to merge.')
        else:
            # Merging ccs:
            with transaction.atomic():
                # Creating new CC with merged field contents:
                newC = CognateClass()
                setDict = {'notes': set(),
                           'root_form': set(),
                           'root_language': set(),
                           'gloss_in_root_lang': set(),
                           'loan_source': set(),
                           'loan_notes': set()}
                for cc in ccs:
                    for k, v in cc.toDict().iteritems():
                        if k in setDict:
                            setDict[k].add(v)
                delta = {k: '{'+', '.join(v)+'}'
                         for k, v in setDict.iteritems()}
                for k, v in delta.iteritems():
                    setattr(newC, k, v)
                newC.bump(request)
                newC.save()
                # Retargeting CJs:
                cjIds = set()
                for cc in ccs:
                    cjIds.update([cj.id for cj
                                  in cc.cognatejudgement_set.all()])
                CognateJudgement.objects.filter(
                    id__in=cjIds).update(
                    cognate_class_id=newC.id)
                '''
                Retargeting CCCs:
                This needs a bit of extra handling
                in case a source is mentioned twice.
                Compare #294.
                '''
                sourceCCCMap = defaultdict(list)
                for cc in ccs:
                    for ccc in cc.cognateclasscitation_set.all():
                        sourceCCCMap[ccc.source_id].append(ccc)
                simpleCCCs = set()
                newCCCs = []
                oldCCCs = set()
                for k, v in sourceCCCMap.iteritems():
                    if len(v) == 1:
                        simpleCCCs.add(v[0].id)
                    else:
                        newCCCs.append(CognateClassCitation(
                            cognate_class_id=newC.id,
                            source_id=k,
                            pages='{' +
                                  ', '.join([x.pages for x in v]) +
                                  '}',
                            reliability='A',
                            comment='{' +
                                    ', '.join([x.comment for x in v]) +
                                    '}'))
                        oldCCCs.update([x.id for x in v])
                # Retargeting simple cases:
                CognateClassCitation.objects.filter(
                    id__in=simpleCCCs).update(
                    cognate_class_id=newC.id)
                # Creating new CCCs:
                CognateClassCitation.objects.bulk_create(newCCCs)
                # Removing old CCCs:
                CognateClassCitation.objects.filter(
                    id__in=oldCCCs).delete()
                # Deleting old ccs:
                ccs.delete()
                # Fixing alias:
                newC.update_alias()


class CognateJudgementSplitRow(AbstractTimestampedForm):
    idField = IntegerField('Id', validators=[InputRequired()])
    splitOff = BooleanField('Checked implies split off',
                            validators=[InputRequired()],
                            default=False)


class CognateJudgementSplitTable(WTForm):
    judgements = FieldList(FormField(CognateJudgementSplitRow))


class LexemeCognateClassRow(AbstractTimestampedForm):
    id = IntegerField('Cognate Class id', validators=[InputRequired()])
    root_form = StringField('Root form', validators=[InputRequired()])
    root_language = StringField('Root language', validators=[InputRequired()])


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
    # Re-added for #278:
    allCognateClasses = FieldList(FormField(LexemeCognateClassRow))


class LexemeTableViewMeaningsForm(WTForm):
    lexemes = FieldList(FormField(LexemeRowViewMeaningsForm))

    def handle(self, request):
        # Assumes validation has already passed
        changedCogIdSet = set()  # Not changing a cognate class twice
        for entry in self.lexemes:
            data = entry.data
            try:
                # Updating the lexeme:
                lex = Lexeme.objects.get(id=data['id'])
                if lex.isChanged(**data):
                    problem = lex.setDelta(request, **data)
                    if problem is None:
                        lex.save()
                    else:
                        messages.error(request,
                                       lex.deltaReport(**problem))
                # Updating cognate class if requested:
                for cData in data['allCognateClasses']:
                    if cData['id'] in changedCogIdSet:
                        continue
                    c = CognateClass.objects.get(id=cData['id'])
                    if c.isChanged(**cData):
                        problem = c.setDelta(request, **cData)
                        if problem is None:
                            c.save()
                            changedCogIdSet.add(c.id)
                        else:
                            messages.error(
                                request, c.deltaReport(**problem))
            except Exception:
                logging.exception('Problem updating Lexeme '
                                  'in view_meaning.')
                messages.error(request, "The server had problems "
                                        "updating lexeme %s." % lex.id)


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

    def handle(self, request):
        '''
        Handles the data given for an instance of this form.
        This method assumes that validation already took place.
        Method introduced for #219.
        '''
        data = self.getValidated()
        with transaction.atomic():
            for k, v in data['cognateClassAssignments'].iteritems():
                # Ignoring don't care cases:
                if k == 'new':
                    if v == 'delete':
                        continue
                elif k == v:  # new, new is permitted
                    continue
                # Creating new CC or moving from an old one?
                if k == 'new':
                    # Add to new class:
                    if v == 'new':
                        # Class to add to:
                        newC = CognateClass()
                        newC.bump(request)
                        newC.save()
                        # Adding to new class:
                        CognateJudgement.objects.bulk_create([
                            CognateJudgement(lexeme_id=lId,
                                             cognate_class_id=newC.id)
                            for lId in data['lexemeIds']])
                        # Fixing alias for new class:
                        newC.update_alias()
                    # Add to existing class:
                    else:
                        CognateJudgement.objects.bulk_create([
                            CognateJudgement(lexeme_id=lId,
                                             cognate_class_id=v)
                            for lId in data['lexemeIds']])
                else:
                    judgements = CognateJudgement.objects.filter(
                        lexeme_id__in=data['lexemeIds'],
                        cognate_class_id=k)
                    # Move to new class:
                    if v == 'new':
                        # Class to add to:
                        newC = CognateClass()
                        newC.bump(request)
                        newC.save()
                        # Adding to new class:
                        judgements.update(cognate_class_id=newC.id)
                        # Fixing alias for new class:
                        newC.update_alias()
                    # Deletion from current class:
                    elif v == 'delete':
                        judgements.delete()
                    # Move to existing class:
                    else:
                        judgements.update(cognate_class_id=v)
                    # Check for remaining entries:
                    remaining = CognateJudgement.objects.filter(
                        cognate_class_id=k).count()
                    if remaining == 0:
                        logging.info('Removed last lexemes '
                                     'from cognate class %s.' % k)
                        messages.warning(
                            request,
                            'Cognate class %s has no lexemes '
                            'left in it.' % k)


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
    # Added for #219
    combinedCognateClassAssignment = StringField(
        'Assignment string for cognate classes',
        validators=[InputRequired()])

    def validate_combinedCognateClassAssignment(form, field):
        tokens = [t.strip() for t in field.data.split(',')]
        for t in tokens:
            if t == 'new':
                '''
                This case is subsumed by the alias regex,
                but listed here for clarity and in case
                we want to enhance alias validation.
                '''
                continue
            elif re.match('^([a-zA-Z]+|\d+)$', t) is not None:
                continue  # Token is number or alias
            else:
                raise ValidationError("Unacceptable token: %s" % t)


class LexemeTableLanguageWordlistForm(WTForm):
    lexemes = FieldList(FormField(LexemeRowLanguageWordlistForm))

    def handle(self, request):
        # Assumes validation has already passed.
        for entry in self.lexemes:
            data = entry.data
            # Fetching lexeme:
            try:
                lex = Lexeme.objects.get(id=data['id'])
            except Lexeme.DoesNotExist:
                messages.error(request, "Sorry, lexeme %s does not "
                                        "exist in the database." % data['id'])
                continue  # Skip this entry
            # Updating the lexeme:
            try:
                with transaction.atomic():
                    if lex.isChanged(**data):
                        problem = lex.setDelta(request, **data)
                        if problem is None:
                            lex.save()
                        else:
                            messages.error(
                                request, lex.deltaReport(**problem))
            except Exception:
                logging.exception('Problem updating Lexeme '
                                  'in LexemeTableLanguageWordlistForm.')
                messages.error(request, 'Sorry, the server could '
                               'not update lexeme %s.' % lex.gloss)
            # Handling combineCognateClassAssignment:
            if data['combinedCognateClassAssignment'] != \
                    lex.combinedCognateClassAssignment:
                # Current cognate classes:
                currentCCs = {}  # :: id | alias -> CognateClass
                for c in lex.cognate_class.all():
                    currentCCs[str(c.id)] = c
                    currentCCs[c.alias] = c
                # cognate classes to keep:
                keepCCs = {}  # :: id -> CognateClass
                # We expect non staff to not increase the count of currentCCs:
                toAdd = len(currentCCs)
                # Tokens to handle:
                tokens = [
                    t.strip() for t
                    in data['combinedCognateClassAssignment'].split(',')]
                for t in tokens:
                    toAdd -= 1  # Decrement toAdd:
                    if toAdd <= 0 and len(currentCCs) > 0 \
                            and not request.user.is_staff:
                        messages.error(
                            request,
                            "Sorry - only staff is allowed "
                            "to add additional cognate set assignments. "
                            "Please contact a staff member if you feel "
                            "that a second cognate set is necessary. "
                            "Refused to add '%s' to lexeme %s." % (t, lex.id))
                        break
                    if t == 'new':  # Add lexeme to a new class:
                        with transaction.atomic():
                            # Class to add to:
                            newC = CognateClass()
                            newC.bump(request)
                            newC.save()
                            # Adding to new class:
                            CognateJudgement.objects.create(
                                lexeme_id=lex.id,
                                cognate_class_id=newC.id)
                            # Fixing alias for new class:
                            newC.update_alias()
                    elif t in currentCCs:  # Is this one satisfied?
                        keep = currentCCs[t]
                        keepCCs[keep.id] = keep
                    else:  # Add lexeme to existing class if this is a new one.
                        cc = None
                        try:
                            if re.match('^\d+$', t) is not None:
                                cc = CognateClass.objects.get(id=int(t))
                            else:
                                cc = CognateClass.objects.filter(
                                    lexeme__meaning__id=lex.meaning_id
                                    ).distinct().get(alias=t)
                        except Exception:
                            logging.exception("Problem handling token %s" % t)
                            messages.error(
                                request,
                                "Sorry, the server didn't understand "
                                "the cognate set assignment token %s." % t)
                            continue  # Next iteration
                        # Adding to found cognate class:
                        CognateJudgement.objects.create(
                            lexeme_id=lex.id,
                            cognate_class_id=cc.id)
                # Remove lexeme from unwanted cognate classes:
                removeCCs = set()  # :: set(id)
                for cc in currentCCs.values():
                    if cc.id not in keepCCs:
                        removeCCs.add(cc.id)
                CognateJudgement.objects.filter(
                    lexeme_id=lex.id,
                    cognate_class_id__in=removeCCs).delete()


class AddMissingLexemsForLanguageForm(WTForm):
    '''
    Added for #304, this form adds lexeme entries for each meaning that
    doesn't already have at least one entry linking to the given language.
    '''
    language = StringField('Ascii name of the language',
                           validators=[InputRequired()])

    def handle(self, request):
        language = Language.objects.get(ascii_name=self.data['language'])
        meanings = Meaning.objects.exclude(
            id__in=set(Lexeme.objects.filter(
                       language=language).values_list(
                       'meaning_id', flat=True))).all()
        if len(meanings) > 0:
            with transaction.atomic():
                for m in meanings:
                    Lexeme.objects.create(language=language, meaning=m)
            messages.info(
                request,
                "Added lexemes for meanings: " +
                ", ".join([m.gloss for m in meanings]))
        else:
            messages.info(
                request,
                'There is at least one lexeme '
                'for every meaning in the database.')


class RemoveEmptyLexemsForLanguageForm(WTForm):
    '''
    Added for #304, this form removes lexeme entries for a given language
    that have empty data for 'Orthographic'.
    '''
    language = StringField('Ascii name of the language',
                           validators=[InputRequired()])

    def handle(self, request):
        language = Language.objects.get(ascii_name=self.data['language'])
        with transaction.atomic():
            wanted = Lexeme.objects.filter(source_form='', language=language)
            meanings = wanted.values_list('meaning__gloss', flat=True)
            if len(meanings) > 0:
                wanted.delete()
                messages.info(
                    request,
                    'Removed entries for meanings: '+', '.join(meanings))
            else:
                messages.info(
                    request,
                    'All meanings have Orthographic data entered, '
                    'nothing to remove.')


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

    def handle(self, request):
        ms = [m.data for m in self.meanings]
        for m in ms:
            try:
                meaning = Meaning.objects.get(id=m['meaningId'])
                if meaning.isChanged(**m):
                    try:
                        problem = meaning.setDelta(request, **m)
                        if problem is None:
                            meaning.save()
                        else:
                            messages.error(
                                request, meaning.deltaReport(**problem))
                    except Exception:
                        logging.exception('Exception while saving POST '
                                          'in view_wordlist.')
                        messages.error(request, 'Sorry, the server had '
                                       'problems saving changes for '
                                       '"%s".' % meaning.gloss)
            except Exception:
                logging.exception('Problem accessing Meaning object '
                                  'in view_wordlist.',
                                  extra=m)
                messages.error(request, 'The server had problems saving '
                               'at least one entry.')


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
        fields = ["source", "pages", "comment"]


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
