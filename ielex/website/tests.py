from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
import logging
import lxml.html
from lexicon.models import *

# TODO make sure settings has DEBUG set to False

logger = logging.getLogger("unittest")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("website/unittest.log", mode="w")
formatter = logging.Formatter('%(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

def make_basic_objects():
    """Make a basic website with one of each kind of object and return a
    dictionary keying classes to instances, e.g.::

        {..., Language:language_instance, ...}
    """
    User.objects.create_user('testuser', 'test@example.com', 'secret')
    user = User.objects.get(username='testuser')
    source = Source.objects.create(citation_text="SOURCE")
    language = Language.objects.create(ascii_name="LANGUAGE",
            utf8_name="LANGUAGE")
    meaning = Meaning.objects.create(gloss="MEANING")
    lexeme = Lexeme.objects.create(source_form="LEXEME", language=language,
            meaning=meaning)
    cogclass = CognateClass.objects.create(alias="X")
    cogjudge = CognateJudgement.objects.create(lexeme=lexeme,
            cognate_class=cogclass)
    cogjudgecit = CognateJudgementCitation.objects.create(
            cognate_judgement=cogjudge,
            source=source, reliability="A")
    lexemecit = LexemeCitation.objects.create(lexeme=lexeme, source=source,
            reliability="A")
    cogclasscit = CognateClassCitation.objects.create(cognate_class=cogclass,
            source=source, reliability="A")
    return {User: user,
            Source: source,
            Language: language,
            Meaning: meaning,
            Lexeme: lexeme,
            CognateClass: cogclass,
            CognateJudgement: cogjudge,
            CognateJudgementCitation: cogjudgecit,
            LexemeCitation: lexemecit,
            CognateClassCitation: cogclasscit}


class ViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        make_basic_objects()
        # self.seen_links = set()

    def walk_page(self, path, parent=None):
        new_links = []
        if path not in self.seen_links:
            self.seen_links.add(path)
            response = self.client.get(path, follow=True)
            logger.info("CHECKING: %s [%s] < %s" % (path,
                response.status_code, parent)) # want to include parent html
            self.assertEqual(response.status_code, 200)
            dom = lxml.html.fromstring(response.content)
            for element, attribute, link, pos in dom.iterlinks():
                if element.tag == "a" and link.startswith("/"):
                    if link in self.seen_links:
                        logger.info(" - CONTAINS (seen): %s" % link)
                    else:
                        logger.info(" - CONTAINS (new) : %s" % link)
                        new_links.append(link)
            for link in new_links:
                self.walk_page(link, path)
        return

    def test_unauthenticated_walk(self):
        "Test that an unauthenticated user can follow every link"
        logger.info("\n === WALK SITE (for unauthenticated user) ===")
        self.seen_links = set()
        self.walk_page("/")
        logger.info(" === end WALK SITE ===\n")

    def test_authenticated_walk(self):
        "Test that an authenticated user can follow every link"
        self.client.login(username='testuser', password='secret')
        logger.info("\n === WALK SITE (for authenticated user) ===")
        root = "/"
        self.seen_links = set()
        self.walk_page("/")
        logger.info(" === end WALK SITE ===\n")

    def test_trailing_slash(self):
        "test that all internal urls have a trailing slash"
        root = "/"
        self.seen_links = set()
        lacking_slash = []
        def walk_page(path, parent=None):
            if path not in self.seen_links:
                self.seen_links.add(path)
                if not path.endswith("/"):
                    if not path.split("/")[-1].startswith("#"): # anchor
                        lacking_slash.append((path, parent))
                response = self.client.get(path, follow=True)
                dom = lxml.html.fromstring(response.content)
                for element, attribute, link, pos in dom.iterlinks():
                    if element.tag == "a" and link.startswith("/"):
                        if link not in self.seen_links:
                            walk_page(link, path)
            return
        walk_page(root)
        if lacking_slash:
            logger.info("\n === LACKING SLASH ===")
            for link, parent in lacking_slash:
                logger.info("%s : %s" % (parent, link))
            logger.info(" === end LACKING SLASH ===\n")
        self.assertFalse(lacking_slash)


class UrlTests(TestCase):
    def test_unique_url_names(self):
        from ielex import urls
        names = []
        for u in urls.urlpatterns:
            try:
                assert u.name
                names.append(u.name)
            except(AttributeError,AssertionError):
                pass 
        self.assertEqual(len(names), len(set(names)))


class LanguageListTests(TestCase):

    def setUp(self):
        self.languages = []
        self.language_list = LanguageList.objects.create(name="LanguageListTests")
        for NAME in "abcd":
            language = Language.objects.create(ascii_name=NAME, utf8_name=NAME)
            self.languages.append(language)
            self.language_list.append(language)

    def test_append_to_language_list(self):
        self.assertEqual(self.languages,
                list(self.language_list.languages.all().order_by("languagelistorder")))

    def test_remove_from_language_list(self):
        language = self.languages[0]
        self.language_list.remove(language)
        self.assertEqual(self.languages[1:],
                list(self.language_list.languages.all().order_by("languagelistorder")))

    def test_insert_to_language_list(self):
        language = self.languages[-1]
        self.language_list.insert(0, language)
        self.assertEqual([self.languages[i] for i in (3,0,1,2)],
                list(self.language_list.languages.all().order_by("languagelistorder")))

    def test_swap_languages(self):
        l1 = self.languages[1]
        l2 = self.languages[2]
        self.language_list.swap(l1, l2)
        self.assertEqual([self.languages[0],self.languages[2],self.languages[1],self.languages[3]],
                list(self.language_list.languages.all().order_by("languagelistorder")))
        self.language_list.swap(l1, l2)
        self.assertEqual(self.languages,
                list(self.language_list.languages.all().order_by("languagelistorder")))

    def test_reorder_view_down(self):
        from ielex.views import move_language
        language = self.languages[0]
        orders =[(1,0,2,3),
                (1,2,0,3),
                (1,2,3,0),
                (0,1,2,3)]
        for i, order in enumerate(orders):
            move_language(language, self.language_list, 1)
            self.assertEqual([self.languages[i] for i in order],
                    list(self.language_list.languages.all().order_by("languagelistorder")))

    def test_reorder_view_up(self):
        from ielex.views import move_language
        language = self.languages[0]
        orders =[(1,2,3,0),
                (1,2,0,3),
                (1,0,2,3),
                (0,1,2,3)]
        for order in orders:
            move_language(language, self.language_list, -1)
            self.assertEqual([self.languages[i] for i in order],
                    list(self.language_list.languages.all().order_by("languagelistorder")))


class CognateClassCodeDenormalizationTests(TestCase):

    def setUp(self):
        self.db = make_basic_objects()

    def test_denormalized_cognate_classes_present(self):
        self.assertEqual(self.db[Lexeme].denormalized_cognate_classes,
                "1,X")

    def test_delete_cognate_judgement(self):
        "Test that post_delete hook updates denormalized data"
        self.db[CognateJudgement].delete()
        self.assertEqual(self.db[Lexeme].denormalized_cognate_classes,
                "")

    def test_add_cognate_judgement(self):
        "Test that post_save hook updates denormalized data"
        cogclass = CognateClass.objects.create(alias="Y")
        cogjudge = CognateJudgement.objects.create(lexeme=self.db[Lexeme],
                cognate_class=cogclass)
        CognateJudgementCitation.objects.create(
                cognate_judgement=cogjudge,
                source=self.db[Source], reliability="A")
        self.assertEqual(self.db[Lexeme].denormalized_cognate_classes,
                "1,X,2,Y")

class LoginTests(TestCase):

    def setUp(self):
        self.client = Client()
        make_basic_objects()

    def test_unauthenticated_edit(self): # proof of concept
        r = self.client.get("/lexeme/1234/edit/", follow=True)
        # parse r.content to find the <input> buttons
        doc = lxml.html.fromstring(r.content)
        inputs = doc.cssselect("input")
        names = set(i.name for i in inputs)
        self.assertTrue("username" in names)
        self.assertTrue("password" in names)

