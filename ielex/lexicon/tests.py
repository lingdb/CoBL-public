# tests specific to lexicon module
from django.test import TestCase
from lexicon.models import *

class LexemeGetCognateClassLinksTest(TestCase):
    """Functions to test the string formatting of denormalized cognate
    class information"""

    template = '<a href="/cognate/%s/">%s</a>'

    def setUp(self):
        self.test_language = Language.objects.create(
                ascii_name="Test_Language",
                utf8_name="Test Language")
        self.test_meaning = Meaning.objects.create(
                gloss="test meaning")
        self.cognate_class_A = CognateClass.objects.create(alias="A")
        self.cognate_class_B = CognateClass.objects.create(alias="B")

    def test_one_denormalized_cognate_class(self):
        # lexemes have the correct denormalized cognate class data appended
        # in the case of one cognate class
        denorm = "%s,%s" % (self.cognate_class_A.id,
                self.cognate_class_A.alias)
        lexeme = Lexeme.objects.create(source_form="a",
                meaning=self.test_meaning,
                language=self.test_language)
        CognateJudgement.objects.create(lexeme=lexeme,
                cognate_class=self.cognate_class_A)
        self.assertEqual(lexeme.denormalized_cognate_classes, denorm)

    def test_formatting_one_cognate_class(self):
        # CC links for lexemes with one CC are correctly formatted
        link = self.template % (self.cognate_class_A.id,
                self.cognate_class_A.alias)
        lexeme = Lexeme.objects.create(source_form="a",
                meaning=self.test_meaning,
                language=self.test_language)
        CognateJudgement.objects.create(lexeme=lexeme,
                cognate_class=self.cognate_class_A)
        self.assertEqual(lexeme.get_cognate_class_links(), link)

    def test_two_denormalized_cognate_class(self):
        # lexemes have the correct denormalized cognate class data appended
        # in the case that the lexeme belongs to two cognate classes
        denorm = "%s,%s,%s,%s" % (self.cognate_class_A.id,
                self.cognate_class_A.alias,
                self.cognate_class_B.id,
                self.cognate_class_B.alias )
        lexeme = Lexeme.objects.create(source_form="a",
                meaning=self.test_meaning,
                language=self.test_language)
        CognateJudgement.objects.create(lexeme=lexeme,
                cognate_class=self.cognate_class_A)
        CognateJudgement.objects.create(lexeme=lexeme,
                cognate_class=self.cognate_class_B)
        self.assertEqual(lexeme.denormalized_cognate_classes, denorm)

    def test_two_cognate_classes(self):
        # CC links for lexemes with two CC are correctly formatted
        link_A = self.template % (self.cognate_class_A.id,
                self.cognate_class_A.alias)
        link_B = self.template % (self.cognate_class_B.id,
                self.cognate_class_B.alias)
        link = "%s, %s" % (link_A, link_B)
        lexeme = Lexeme.objects.create(source_form="a",
                meaning=self.test_meaning,
                language=self.test_language)
        CognateJudgement.objects.create(lexeme=lexeme,
                cognate_class=self.cognate_class_A)
        CognateJudgement.objects.create(lexeme=lexeme,
                cognate_class=self.cognate_class_B)
        self.assertEqual(lexeme.get_cognate_class_links(), link)
