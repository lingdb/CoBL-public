# tests specific to lexicon module
from django.test import TestCase
from ielex.lexicon.models import *
from ielex.lexicon.templatetags.lexicon_utils import wikilink

class WikilinkTest(TestCase):
    """Test internal links of the format /lexeme/1234/"""

    def setUp(self):
        self.src1 = "/lexeme/123/"
        self.dst1 = '<a href="/lexeme/123/">/lexeme/123/</a>'
        self.src2 = "/cognate/456/"
        self.dst2 = '<a href="/cognate/456/">/cognate/456/</a>'

    def test_make_link(self):
        self.assertEqual(wikilink(self.src1), self.dst1)
        self.assertEqual(wikilink(self.src2), self.dst2)

    def test_dont_link_date(self):
        DATE = "21/10/2012"
        self.assertEqual(wikilink(DATE), DATE)

    def test_make_embedded_link(self):
        src = "asdf %s asdf" % self.src1
        dst = "asdf %s asdf" % self.dst1
        self.assertEqual(wikilink(src), dst)

    def test_two_embedded_links(self):
        src = "asdf %s asdf %s asdf" % (self.src1, self.src2)
        dst = "asdf %s asdf %s asdf" % (self.dst1, self.dst2)
        self.assertEqual(wikilink(src), dst)


class LexemeGetCognateClassLinksTest(TestCase):
    """Functions to test the string formatting of denormalized cognate
    class information"""

    template = '<a href="/cognate/%s/">%s</a>'
    bracketted_template = '(<a href="/cognate/%s/">%s</a>)'

    def setUp(self):
        self.test_language = Language.objects.create(
                ascii_name="Test_Language",
                utf8_name="Test Language")
        self.test_meaning = Meaning.objects.create(
                gloss="test meaning")
        self.test_source = Source.objects.create(citation_text="a")
        self.cognate_class_A = CognateClass.objects.create(alias="A")
        self.cognate_class_B = CognateClass.objects.create(alias="B")
        self.cognate_class_L = CognateClass.objects.create(alias="L")
        self.cognate_class_X = CognateClass.objects.create(alias="X")
        self.lexeme = Lexeme.objects.create(source_form="a",
                meaning=self.test_meaning,
                language=self.test_language)

    def test_one_denormalized_cognate_class(self):
        # lexemes have the correct denormalized cognate class data appended
        # in the case of one cognate class
        denorm = "%s,%s" % (self.cognate_class_A.id,
                self.cognate_class_A.alias)
        CognateJudgement.objects.create(lexeme=self.lexeme,
                cognate_class=self.cognate_class_A)
        self.assertEqual(self.lexeme.denormalized_cognate_classes, denorm)

    def test_formatting_one_cognate_class(self):
        # CC links for lexemes with one CC are correctly formatted
        link = self.template % (self.cognate_class_A.id,
                self.cognate_class_A.alias)
        CognateJudgement.objects.create(lexeme=self.lexeme,
                cognate_class=self.cognate_class_A)
        self.assertEqual(self.lexeme.get_cognate_class_links(), link)

    def test_two_denormalized_cognate_class(self):
        # lexemes have the correct denormalized cognate class data appended
        # in the case that the lexeme belongs to two cognate classes
        denorm = "%s,%s,%s,%s" % (self.cognate_class_A.id,
                self.cognate_class_A.alias,
                self.cognate_class_B.id,
                self.cognate_class_B.alias )
        CognateJudgement.objects.create(lexeme=self.lexeme,
                cognate_class=self.cognate_class_A)
        CognateJudgement.objects.create(lexeme=self.lexeme,
                cognate_class=self.cognate_class_B)
        self.assertEqual(self.lexeme.denormalized_cognate_classes, denorm)

    def test_two_cognate_classes(self):
        # CC links for lexemes with two CC are correctly formatted
        link_A = self.template % (self.cognate_class_A.id,
                self.cognate_class_A.alias)
        link_B = self.template % (self.cognate_class_B.id,
                self.cognate_class_B.alias)
        link = "%s, %s" % (link_A, link_B)
        CognateJudgement.objects.create(lexeme=self.lexeme,
                cognate_class=self.cognate_class_A)
        CognateJudgement.objects.create(lexeme=self.lexeme,
                cognate_class=self.cognate_class_B)
        self.assertEqual(self.lexeme.get_cognate_class_links(), link)

    def test_loanword_cognate_class(self):
        link = self.bracketted_template % (self.cognate_class_L.id,
                self.cognate_class_L.alias)
        cognate_judgement = CognateJudgement.objects.create(
                lexeme=self.lexeme,
                cognate_class=self.cognate_class_L)
        CognateJudgementCitation.objects.create(
                source=self.test_source,
                cognate_judgement=cognate_judgement, 
                reliability="L")
        self.assertEqual(self.lexeme.get_cognate_class_links(), link)
