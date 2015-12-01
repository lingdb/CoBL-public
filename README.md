# IELex Django intermdiate staging repo

Here we are collecting changes to the code base of the original IELex Django project for staging, before eventually releasing this live for the IELex2 project.

## Changes:

06/11/15: 

- Added JSON type fields to the all relevant tables in `lexicon/model.py`
- Creating templates for editable versions of `language_wordlist.html` and `view_meaning.html`.
- Beginning development of `views.py`, specifically: *view_meaning* and *view_language_wordlist*.
- In `forms.py`, creating relevant forms for providing editing functionality: *LexemeRowForm*, *AddLexemesTableForm*.

13/11/15:

- Extending editable templates `language_wordlist_editable.html` and `view_meaning_editable.html`, to include additional fields.
- Extending `views.py`, to manage content served to `language/[LANGUAGE]/wordlist/all/` and `/meaning/[MEANING]/languagelist/all/`.
- Initiated Django tables code, in `tables.py`. TODO: complications with incorporating editing functionality, will come back to this later.

20/11/15:

- Extending editable templates `language_wordlist_editable.html` and `view_meaning_editable.html`, to include copying arrows. Specifically adding JavaScript to `base.html` for this purpose. TODO: need to move JavaScript to `static/js/ielex.js`.
- Extending `views.py`, to provide filtering functionality.
- In `forms.py`, creating relevant forms for filtering: *LexemeTableFilterForm*, *MeaningTableFilterForm*.

27/11/15:

- Latest version reconciled with latest PSQL dump.
- Various style changes in `static\css\ielex\css`.

30/11/15:

- Moved code base to new repository, ready for review, before publication.
