# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Source'
        db.create_table('lexicon_source', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('citation_text', self.gf('django.db.models.fields.TextField')(unique=True)),
            ('type_code', self.gf('django.db.models.fields.CharField')(default='P', max_length=1)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('lexicon', ['Source'])

        # Adding model 'Language'
        db.create_table('lexicon_language', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('iso_code', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
            ('ascii_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=999)),
            ('utf8_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=999)),
            ('sort_key', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('lexicon', ['Language'])

        # Adding model 'DyenName'
        db.create_table('lexicon_dyenname', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.Language'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=999)),
        ))
        db.send_create_signal('lexicon', ['DyenName'])

        # Adding model 'Meaning'
        db.create_table('lexicon_meaning', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gloss', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('lexicon', ['Meaning'])

        # Adding model 'CognateSet'
        db.create_table('lexicon_cognateset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('alias', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('notes', self.gf('django.db.models.fields.TextField')()),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('lexicon', ['CognateSet'])

        # Adding model 'DyenCognateSet'
        db.create_table('lexicon_dyencognateset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cognate_class', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.CognateSet'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('doubtful', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('lexicon', ['DyenCognateSet'])

        # Adding model 'Lexeme'
        db.create_table('lexicon_lexeme', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.Language'])),
            ('meaning', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.Meaning'], null=True, blank=True)),
            ('source_form', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('phon_form', self.gf('django.db.models.fields.CharField')(max_length=999, blank=True)),
            ('gloss', self.gf('django.db.models.fields.CharField')(max_length=999, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('lexicon', ['Lexeme'])

        # Adding model 'CognateJudgement'
        db.create_table('lexicon_cognatejudgement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lexeme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.Lexeme'])),
            ('cognate_class', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.CognateSet'])),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('lexicon', ['CognateJudgement'])

        # Adding model 'LanguageList'
        db.create_table('lexicon_languagelist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('language_ids', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=999)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('lexicon', ['LanguageList'])

        # Adding model 'MeaningList'
        db.create_table('lexicon_meaninglist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('meaning_ids', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=999)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('lexicon', ['MeaningList'])

        # Adding model 'GenericCitation'
        db.create_table('lexicon_genericcitation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.Source'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('pages', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('reliability', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('lexicon', ['GenericCitation'])

        # Adding unique constraint on 'GenericCitation', fields ['content_type', 'object_id', 'source']
        db.create_unique('lexicon_genericcitation', ['content_type_id', 'object_id', 'source_id'])

        # Adding model 'CognateJudgementCitation'
        db.create_table('lexicon_cognatejudgementcitation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pages', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('reliability', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('cognate_judgement', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.CognateJudgement'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.Source'])),
        ))
        db.send_create_signal('lexicon', ['CognateJudgementCitation'])

        # Adding unique constraint on 'CognateJudgementCitation', fields ['cognate_judgement', 'source']
        db.create_unique('lexicon_cognatejudgementcitation', ['cognate_judgement_id', 'source_id'])

        # Adding model 'LexemeCitation'
        db.create_table('lexicon_lexemecitation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pages', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('reliability', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('lexeme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.Lexeme'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.Source'])),
        ))
        db.send_create_signal('lexicon', ['LexemeCitation'])

        # Adding unique constraint on 'LexemeCitation', fields ['lexeme', 'source']
        db.create_unique('lexicon_lexemecitation', ['lexeme_id', 'source_id'])

    def backwards(self, orm):
        
        # Removing unique constraint on 'LexemeCitation', fields ['lexeme', 'source']
        db.delete_unique('lexicon_lexemecitation', ['lexeme_id', 'source_id'])

        # Removing unique constraint on 'CognateJudgementCitation', fields ['cognate_judgement', 'source']
        db.delete_unique('lexicon_cognatejudgementcitation', ['cognate_judgement_id', 'source_id'])

        # Removing unique constraint on 'GenericCitation', fields ['content_type', 'object_id', 'source']
        db.delete_unique('lexicon_genericcitation', ['content_type_id', 'object_id', 'source_id'])

        # Deleting model 'Source'
        db.delete_table('lexicon_source')

        # Deleting model 'Language'
        db.delete_table('lexicon_language')

        # Deleting model 'DyenName'
        db.delete_table('lexicon_dyenname')

        # Deleting model 'Meaning'
        db.delete_table('lexicon_meaning')

        # Deleting model 'CognateSet'
        db.delete_table('lexicon_cognateset')

        # Deleting model 'DyenCognateSet'
        db.delete_table('lexicon_dyencognateset')

        # Deleting model 'Lexeme'
        db.delete_table('lexicon_lexeme')

        # Deleting model 'CognateJudgement'
        db.delete_table('lexicon_cognatejudgement')

        # Deleting model 'LanguageList'
        db.delete_table('lexicon_languagelist')

        # Deleting model 'MeaningList'
        db.delete_table('lexicon_meaninglist')

        # Deleting model 'GenericCitation'
        db.delete_table('lexicon_genericcitation')

        # Deleting model 'CognateJudgementCitation'
        db.delete_table('lexicon_cognatejudgementcitation')

        # Deleting model 'LexemeCitation'
        db.delete_table('lexicon_lexemecitation')

    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'lexicon.cognatejudgement': {
            'Meta': {'object_name': 'CognateJudgement'},
            'cognate_class': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.CognateSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lexeme': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Lexeme']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lexicon.Source']", 'through': "orm['lexicon.CognateJudgementCitation']", 'symmetrical': 'False'})
        },
        'lexicon.cognatejudgementcitation': {
            'Meta': {'unique_together': "(('cognate_judgement', 'source'),)", 'object_name': 'CognateJudgementCitation'},
            'cognate_judgement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.CognateJudgement']"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '999'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pages': ('django.db.models.fields.CharField', [], {'max_length': '999'}),
            'reliability': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Source']"})
        },
        'lexicon.cognateset': {
            'Meta': {'ordering': "['alias']", 'object_name': 'CognateSet'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {})
        },
        'lexicon.dyencognateset': {
            'Meta': {'object_name': 'DyenCognateSet'},
            'cognate_class': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.CognateSet']"}),
            'doubtful': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '8'})
        },
        'lexicon.dyenname': {
            'Meta': {'ordering': "['name']", 'object_name': 'DyenName'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Language']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '999'})
        },
        'lexicon.genericcitation': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'source'),)", 'object_name': 'GenericCitation'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '999'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'pages': ('django.db.models.fields.CharField', [], {'max_length': '999'}),
            'reliability': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Source']"})
        },
        'lexicon.language': {
            'Meta': {'ordering': "['ascii_name']", 'object_name': 'Language'},
            'ascii_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '999'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iso_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'sort_key': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'utf8_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '999'})
        },
        'lexicon.languagelist': {
            'Meta': {'ordering': "['name']", 'object_name': 'LanguageList'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_ids': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '999'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '999'})
        },
        'lexicon.lexeme': {
            'Meta': {'ordering': "('_order',)", 'object_name': 'Lexeme'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cognate_class': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lexicon.CognateSet']", 'symmetrical': 'False', 'through': "orm['lexicon.CognateJudgement']", 'blank': 'True'}),
            'gloss': ('django.db.models.fields.CharField', [], {'max_length': '999', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Language']"}),
            'meaning': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Meaning']", 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'phon_form': ('django.db.models.fields.CharField', [], {'max_length': '999', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lexicon.Source']", 'symmetrical': 'False', 'through': "orm['lexicon.LexemeCitation']", 'blank': 'True'}),
            'source_form': ('django.db.models.fields.CharField', [], {'max_length': '999'})
        },
        'lexicon.lexemecitation': {
            'Meta': {'unique_together': "(('lexeme', 'source'),)", 'object_name': 'LexemeCitation'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '999'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lexeme': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Lexeme']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pages': ('django.db.models.fields.CharField', [], {'max_length': '999'}),
            'reliability': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Source']"})
        },
        'lexicon.meaning': {
            'Meta': {'ordering': "['gloss']", 'object_name': 'Meaning'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'gloss': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'lexicon.meaninglist': {
            'Meta': {'ordering': "['name']", 'object_name': 'MeaningList'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meaning_ids': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '999'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '999'})
        },
        'lexicon.source': {
            'Meta': {'ordering': "['type_code', 'citation_text']", 'object_name': 'Source'},
            'citation_text': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'type_code': ('django.db.models.fields.CharField', [], {'default': "'P'", 'max_length': '1'})
        }
    }

    complete_apps = ['lexicon']
