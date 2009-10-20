#!/usr/bin/env python
"""
Usage: validate_csv.py
"""
import sys
from textwrap import dedent
import csv
excel_dialect = "excel"
#excel_dialect = "excel-tab"

def usage():
    print dedent("""\
        Usage:

          python validate_csv.py LANG_FILE BIBLIO_FILE

        where both files are saved as csv""")
    return

def main():
    try:
        assert len(sys.argv) == 3
    except AssertionError:
        return usage()
    biblio = []
    print "-> Scanning bibliography"
    for i, row in enumerate(csv.reader(file(sys.argv[2]), dialect=excel_dialect)):
        try:
            key, citation = row
            biblio.append(key.strip())
        except:
            print "Error on line %s" % i
            print "row:", row
    try:
        assert len(biblio) == len(set(biblio))
    except AssertionError:
        print "Error: repeated key in '%s'" % sys.argv[2]

    print "-> Validating data"
    reader = csv.reader(file(sys.argv[1]), dialect=excel_dialect)
    reader.next()
    for i, row in enumerate(reader):
        try:
            try:
                lex_id, source_form, phon_form, notes, raw_citation, cogset = row
            except ValueError:
                lex_id, source_form, phon_form, notes, raw_citation = row
            lex_id = lex_id.strip()
            source_form = source_form.strip()
            phon_form = phon_form.strip()
            notes = notes.strip()
            raw_citation = raw_citation.strip()
            try:
                int(lex_id)
            except TypeError:
                print "Error: ID '%s' on line %s is not a numeral" % (lex_id, i+1)
            citations = [e.strip() for e in raw_citation.split(",")]
            for citation in citations:
                if ":" in citation:
                    citation, pages = citation.split(":")
                try:
                    assert citation in biblio
                except AssertionError:
                    print "Error: Biblio key '%s' on line %s is not in '%s'" % \
                    (citation, i+1, sys.argv[2])
        except:
            if source_form == phon_form == raw_citation:
                pass
            else:
                print "Error on line %s" % i
                print "row:", row
    print "-> Finished"

if __name__ == "__main__":
    main()
