# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):

        def set_percent_coded(meaning):
            """Can't use the method in models.py, http://stackoverflow.com/a/3315547/188595"""
            uncoded = meaning.lexeme_set.filter(cognate_class=None).count()
            total = meaning.lexeme_set.filter().count()
            try:
                meaning.percent_coded = 100.0 * (total - uncoded) / total
            except ZeroDivisionError:
                meaning.percent_coded = 0
            meaning.save()
            return

        for meaning in orm.Meaning.objects.all():
            set_percent_coded(meaning)
        return

    def backwards(self, orm):
        "no need for backwards migration of data denormalization"
        return


    models = {
        'lexicon.cognateclass': {
            'Meta': {'ordering': "['alias']", 'object_name': 'CognateClass'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('ielex.lexicon.models.CharNullField', [], {'max_length': '128', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'lexicon.cognateclasscitation': {
            'Meta': {'unique_together': "(('cognate_class', 'source'),)", 'object_name': 'CognateClassCitation'},
            'cognate_class': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.CognateClass']"}),
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pages': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'reliability': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Source']"})
        },
        'lexicon.cognatejudgement': {
            'Meta': {'object_name': 'CognateJudgement'},
            'cognate_class': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.CognateClass']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lexeme': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Lexeme']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lexicon.Source']", 'through': "orm['lexicon.CognateJudgementCitation']", 'symmetrical': 'False'})
        },
        'lexicon.cognatejudgementcitation': {
            'Meta': {'unique_together': "(('cognate_judgement', 'source'),)", 'object_name': 'CognateJudgementCitation'},
            'cognate_judgement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.CognateJudgement']"}),
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pages': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'reliability': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Source']"})
        },
        'lexicon.dyencognateset': {
            'Meta': {'object_name': 'DyenCognateSet'},
            'cognate_class': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.CognateClass']"}),
            'doubtful': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '8'})
        },
        'lexicon.dyenname': {
            'Meta': {'ordering': "['name']", 'object_name': 'DyenName'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Language']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'lexicon.language': {
            'Meta': {'ordering': "['ascii_name']", 'object_name': 'Language'},
            'ascii_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iso_code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'utf8_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'lexicon.languagelist': {
            'Meta': {'ordering': "['name']", 'object_name': 'LanguageList'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'languages': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lexicon.Language']", 'through': "orm['lexicon.LanguageListOrder']", 'symmetrical': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'})
        },
        'lexicon.languagelistorder': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('language_list', 'language'), ('language_list', 'order'))", 'object_name': 'LanguageListOrder'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Language']"}),
            'language_list': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.LanguageList']"}),
            'order': ('django.db.models.fields.FloatField', [], {})
        },
        'lexicon.lexeme': {
            'Meta': {'ordering': "('_order',)", 'object_name': 'Lexeme'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'cognate_class': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lexicon.CognateClass']", 'symmetrical': 'False', 'through': "orm['lexicon.CognateJudgement']", 'blank': 'True'}),
            'denormalized_cognate_classes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'gloss': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Language']"}),
            'meaning': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Meaning']", 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'number_cognate_coded': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'phon_form': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lexicon.Source']", 'symmetrical': 'False', 'through': "orm['lexicon.LexemeCitation']", 'blank': 'True'}),
            'source_form': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'lexicon.lexemecitation': {
            'Meta': {'unique_together': "(('lexeme', 'source'),)", 'object_name': 'LexemeCitation'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lexeme': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Lexeme']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pages': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'reliability': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lexicon.Source']"})
        },
        'lexicon.meaning': {
            'Meta': {'ordering': "['gloss']", 'object_name': 'Meaning'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'gloss': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'percent_coded': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        'lexicon.meaninglist': {
            'Meta': {'ordering': "['name']", 'object_name': 'MeaningList'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meaning_ids': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '4096'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
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
    symmetrical = True
