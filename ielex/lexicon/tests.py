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
        source = Source.objects.create(citation_text="Source")
        language = Language.objects.create(ascii_name="Language", utf8_name="Language")
        meaning = Meaning.objects.create(gloss="Meaning")
        lexeme = Lexeme.objects.create(source_form="Lexeme", language=language,
                meaning=meaning)
        cogclass = CognateClass.objects.create(alias="CognateClass")
        cogjudge = CognateJudgement.objects.create(lexeme=lexeme, cognate_class=cogclass)
        CognateJudgementCitation.objects.create(cognate_judgement=cogjudge,
                source=source)
        LexemeCitation.objects.create(lexeme=lexeme, source=source)
        CognateClassCitation.objects.create(cognate_class=cogclass,
                source=source)

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
        "Walk though every link of the database to see that it renders"
        root = "/"
        seen_links = set()
        def walk_page(path, parent):
            if path not in seen_links:
                seen_links.add(path)
                response = self.client.get(path)
                logger.info("CHECKING: %s %s < %s" % (path,
                    response.status_code, parent))
                self.assertEqual(response.status_code, 200)
                dom = lxml.html.fromstring(response.content)
                for element, attribute, link, pos in dom.iterlinks():
                    if element.tag == "a" and link.startswith("/"):
                        if link in seen_links:
                            logger.info(" - CONTAINS (seen): %s" % link)
                        else:
                            logger.info(" - CONTAINS (new) : %s" % link)
                        walk_page(link, path)
            return
        walk_page(root, None)


