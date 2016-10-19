from ielex.lexicon.models import Source
import bibtexparser
from bibtexparser.bparser import BibTexParser
from django.core.exceptions import ObjectDoesNotExist

def get_bibtex_data(filename):
  
  parser = BibTexParser()
  parser.ignore_nonstandard_types = False
  with open(filename) as f:
    bib_database = bibtexparser.loads(f.read(), parser)
  sources_dict_lst = []
  for entry in bib_database.entries:
    sources_dict_lst.append(entry)
  return sources_dict_lst

def bibtex_update(filename):

  sources_dict_lst = get_bibtex_data(filename)
  for entry in sources_dict_lst:
    try:
      source_obj = Source.objects.get(pk=entry['ID'])
      source_obj.populate_from_bibtex(entry)
    except (ValueError, ObjectDoesNotExist) as e:
        print 'Failed to handle BibTeX entry with ID %s: %s' %([entry['ID']], e)
