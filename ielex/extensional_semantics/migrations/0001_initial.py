# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SemanticRelation'
        db.create_table('extensional_semantics_semanticrelation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('relation_code', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('long_name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('extensional_semantics', ['SemanticRelation'])

        # Adding model 'SemanticExtension'
        db.create_table('extensional_semantics_semanticextension', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lexeme', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.Lexeme'])),
            ('relation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['extensional_semantics.SemanticRelation'])),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('extensional_semantics', ['SemanticExtension'])

        # Adding model 'SemanticExtensionCitation'
        db.create_table('extensional_semantics_semanticextensioncitation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pages', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('reliability', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=999)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('extension', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['extensional_semantics.SemanticExtension'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lexicon.Source'])),
        ))
        db.send_create_signal('extensional_semantics', ['SemanticExtensionCitation'])

        # Adding unique constraint on 'SemanticExtensionCitation', fields ['extension', 'source']
        db.create_unique('extensional_semantics_semanticextensioncitation', ['extension_id', 'source_id'])

        # Adding model 'SemanticDomain'
        db.create_table('extensional_semantics_semanticdomain', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=999)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('relation_ids', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=999, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('extensional_semantics', ['SemanticDomain'])

    def backwards(self, orm):
        
        # Removing unique constraint on 'SemanticExtensionCitation', fields ['extension', 'source']
        db.delete_unique('extensional_semantics_semanticextensioncitation', ['extension_id', 'source_id'])

        # Deleting model 'SemanticRelation'
        db.delete_table('extensional_semantics_semanticrelation')

        # Deleting model 'SemanticExtension'
        db.delete_table('extensional_semantics_semanticextension')

        # Deleting model 'SemanticExtensionCitation'
        db.delete_table('extensional_semantics_semanticextensioncitation')

        # Deleting model 'SemanticDomain'
        db.delete_table('extensional_semantics_semanticdomain')

    models = {
        'extensional_semantics.semanticdomain': {
            'Meta': {'ordering': "['name']", 'object_name': 'SemanticDomain'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '999'}),
            'relation_ids': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '999', 'blank': 'True'})
        },
        'extensional_semantics.semanticextension': {
            'Meta': {'object_name': 'SemanticExtension'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lexeme': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Lexeme']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'relation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['extensional_semantics.SemanticRelation']"}),
            'source': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lexicon.Source']", 'through': "orm['extensional_semantics.SemanticExtensionCitation']", 'symmetrical': 'False'})
        },
        'extensional_semantics.semanticextensioncitation': {
            'Meta': {'unique_together': "(('extension', 'source'),)", 'object_name': 'SemanticExtensionCitation'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '999'}),
            'extension': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['extensional_semantics.SemanticExtension']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pages': ('django.db.models.fields.CharField', [], {'max_length': '999'}),
            'reliability': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Source']"})
        },
        'extensional_semantics.semanticrelation': {
            'Meta': {'object_name': 'SemanticRelation'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'relation_code': ('django.db.models.fields.CharField', [], {'max_length': '64'})
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
        'lexicon.language': {
            'Meta': {'ordering': "['ascii_name']", 'object_name': 'Language'},
            'ascii_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '999'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iso_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'sort_key': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'utf8_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '999'})
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
        'lexicon.source': {
            'Meta': {'ordering': "['type_code', 'citation_text']", 'object_name': 'Source'},
            'citation_text': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'type_code': ('django.db.models.fields.CharField', [], {'default': "'P'", 'max_length': '1'})
        }
    }

    complete_apps = ['extensional_semantics']
