from django.test import TestCase
from django.test.client import Client
from ielex.website.tests import make_basic_objects
from ielex.website.tests import ViewBaseMethods
from ielex.extensional_semantics.models import SemanticExtension, \
                                               SemanticExtensionCitation, \
                                               SemanticRelation
from ielex.lexicon.models import Lexeme, Source
from ielex.settings import semantic_domains as SEMANTIC_DOMAINS


class ExtensionalSemanticsViewTests(TestCase, ViewBaseMethods):

    def setUp(self):
        self.client = Client()
        objects = make_basic_objects()
        # add additional objects here
        relation = SemanticRelation.objects.create(
                relation_code="R", long_name="RELATION")
        extension = SemanticExtension.objects.create(
                lexeme=objects[Lexeme],
                relation=relation)
        SemanticExtensionCitation.objects.create(
                extension=extension,
                source=objects[Source])
        self.seen_links = set()

    def test_module_activated(self):
        self.assertTrue(SEMANTIC_DOMAINS)
