from django.test import TestCase
from django.test.client import Client
from website.tests import make_basic_objects
from website.tests import ViewTests
from extensional_semantics.models import *
from lexicon.models import Lexeme, Source

class ExtensionalSemanticsViewTests(ViewTests):

    def setUp(self):
        self.client = Client()
        objects = make_basic_objects()
        # add additional objects here
        relation = SemanticRelation.objects.create(
                relation_code="R", long_name="RELATION")
        extension = SemanticExtension.objects.create(
                lexeme=objects[Lexeme],
                relation=relation)
        extensioncit = SemanticExtensionCitation.objects.create(
                extension=extension,
                source=objects[Source])
        self.seen_links = set()
