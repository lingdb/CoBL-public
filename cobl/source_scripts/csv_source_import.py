# -*- coding: utf-8 -*-
import codecs
from cobl.lexicon.models import Source


def parse_source_csv(path):
    csv_file = codecs.open(path, 'r', encoding='utf-8')
    data_dict = {}
    i = 1
    for row in csv_file:
        entry = row.rstrip().split('|')
        try:
            data_dict[int(entry[0])] = {'shorthand': entry[
                1], 'citation_text': entry[2]}
        except (IndexError, ValueError) as e:
            if e == IndexError:
                print('Parsing error in line %s of %s: returns %s'
                      % (i, path, entry))
            elif e == ValueError:
                print('Parsing error in line %s of %s: %s is not a valid ID'
                      % (i, path, entry[0]))
        i += 1
    csv_file.close()
    return data_dict


def import_csv_citations(path, model=Source):
    data_dict = parse_source_csv(path)
    for key in data_dict.keys():
        try:
            source_obj = model.objects.get(pk=key)
            source_obj.shorthand = data_dict[key]['shorthand']
            source_obj.citation_text = data_dict[key]['citation_text']
            source_obj.save()
        except model.DoesNotExist:
            pass
