## This script should be called from the ipython shell launched using the
## manage.py script (which sets up the full django environment)
##
## 0. From a clean copy of LexDB, run './manage.py syncdb' and
##    './manage.py migrate' (from the ielex directory)
## 1. Open the shell using './manage.py shell'
## 2. Change the working directory of the ipython shell:
##    %cd ../dev/andronov
## 3. Run the script with the data file as an argument:
##    %run import_csv_data.py data.csv
## The import will take a while: stare in admiration at the screens of
## data scrolling past and imagine you're in the matrix. Once it stops:
## 4. Exit ipython (with 'exit')
## 5. Run the test server using './manage.py runserver' then open
##    http://127.0.0.1:8000/ in a browser

import sys
import codecs
import os
from ielex.lexicon.models import *

assert os.path.exists(sys.argv[0]) and sys.argv[0].endswith("import_csv_data.py")
assert os.path.exists(sys.argv[1]) and sys.argv[1].endswith("data.csv")

def get_next_alias(meaning):
    current_aliases = CognateClass.objects.filter(
            lexeme__meaning=meaning).distinct().values_list("alias", flat=True)
    for alias in "ABCDEFGHIJ":
        if alias not in current_aliases:
            return alias
    raise ValueError
    return

data = codecs.open(sys.argv[1], "rU", "utf-8")
header = data.next().rstrip().split("\t")

languages, meaning_ids  = [], []
print header[2:]
for full_name in header[2:]:
    language, created = Language.objects.get_or_create(ascii_name=full_name,
            utf8_name=full_name)
    languages.append(language)

try:
    andronov = Source.objects.get(citation_text__startswith="Andronov")
except Source.DoesNotExist:
    text = "Andronov, M. 1964. Lexicostatistic analysis of the chronology "\
            "of disintegration of proto-Dravidian. Indo-Iranian Journal 7, "\
            "no. 2: 170-186."
    andronov = Source.objects.create(citation_text=text, type_code="P")

dummy = [None] * 4
gloss = None
meaning_list = MeaningList.objects.create(name="Andronov-1964")
for line in data:
    row = [elem.strip() for elem in line.rstrip().split("\t")] + dummy
    if row[1]:
        gloss = row[1]
        if gloss.startswith("to "):
            gloss = gloss[3:]
    meaning, created = Meaning.objects.get_or_create(gloss=gloss,
            description=gloss)
    if created:
        meaning_list.append(meaning)
    alias = get_next_alias(meaning)
    cognate_class = CognateClass.objects.create(alias=alias)
    for language, form in zip(languages, row[2:]):
        if form:
            if form.startswith("*"):
                form = form[1:]
                reliability="L"
            else:
                reliability="B"
            lexeme = Lexeme.objects.create(language=language, meaning=meaning,
                    source_form=form)
            LexemeCitation.objects.create(lexeme=lexeme, source=andronov,
                    reliability=reliability)
            cognate_judgement = CognateJudgement.objects.create(lexeme=lexeme,
                    cognate_class=cognate_class)
            CognateJudgementCitation.objects.create(
                    cognate_judgement=cognate_judgement,
                    source=andronov,
                    reliability=reliability)
            print (meaning, language, lexeme, cognate_judgement)

