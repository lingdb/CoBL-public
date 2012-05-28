from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
import logging
import lxml.html
from lexicon.models import *

logger = logging.getLogger("unittest")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("unittest.log", mode="w")
formatter = logging.Formatter('%(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

class ViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        # put one of each kind of object into the database
        # TODO move this to a separate function so that other tests can
        # use or build upon it.
        source = Source.objects.create(citation_text="SOURCE")
        language = Language.objects.create(ascii_name="LANGUAGE", utf8_name="LANGUAGE")
        meaning = Meaning.objects.create(gloss="MEANING")
        lexeme = Lexeme.objects.create(source_form="LEXEME", language=language,
                meaning=meaning)
        cogclass = CognateClass.objects.create(alias="X")
        cogjudge = CognateJudgement.objects.create(lexeme=lexeme,
                cognate_class=cogclass)
        CognateJudgementCitation.objects.create(cognate_judgement=cogjudge,
                source=source, reliability="A")
        LexemeCitation.objects.create(lexeme=lexeme, source=source,
                reliability="A")
        CognateClassCitation.objects.create(cognate_class=cogclass,
                source=source, reliability="A")

    def test_frontpage(self):
        logger.info("tested /")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    # def test_login(self):
    #     User.objects.create_user('testuser', 'test@example.com', 'secret')
    #     user = self.client.login(username='testuser', password='secret')
    #     logger.info("tested /admin/")
    #     response = self.client.post('/admin/')
    #     self.assertEqual(response.status_code, 200)

    def test_unlogged_walk(self):
        "Test that an unauthenticated user can follow every link"
        logger.info("\n === WALK SITE (for unauthenticated user) ===")
        root = "/"
        seen_links = set()
        def walk_page(path, parent):
            new_links = []
            if path not in seen_links:
                seen_links.add(path)
                response = self.client.get(path, follow=True)
                logger.info("CHECKING: %s [%s] < %s" % (path,
                    response.status_code, parent))
                self.assertEqual(response.status_code, 200)
                dom = lxml.html.fromstring(response.content)
                for element, attribute, link, pos in dom.iterlinks():
                    if element.tag == "a" and link.startswith("/"):
                        if link in seen_links:
                            logger.info(" - CONTAINS (seen): %s" % link)
                        else:
                            logger.info(" - CONTAINS (new) : %s" % link)
                            new_links.append(link)
                for link in new_links:
                    walk_page(link, path)
            return
        walk_page(root, None)
        logger.info(" === end WALK SITE ===\n")

    def test_trailing_slash(self):
        "test that all internal urls have a trailing slash"
        root = "/"
        seen_links = set()
        lacking_slash = []
        def walk_page(path, parent):
            if path not in seen_links:
                if not path.endswith("/"):
                    if not path.split("/")[-1].startswith("#"): # anchor
                        lacking_slash.append((path, parent))
                seen_links.add(path)
                response = self.client.get(path, follow=True)
                dom = lxml.html.fromstring(response.content)
                for element, attribute, link, pos in dom.iterlinks():
                    if element.tag == "a" and link.startswith("/"):
                        if link not in seen_links:
                            walk_page(link, path)
            return
        walk_page(root, None)
        if lacking_slash:
            logger.info("\n === LACKING SLASH ===")
            for link, parent in lacking_slash:
                logger.info("%s : %s" % (parent, link))
            logger.info(" === end LACKING SLASH ===\n")
        self.assertFalse(lacking_slash)

