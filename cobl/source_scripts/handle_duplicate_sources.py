import django
from cobl.lexicon.models import Source
from django.core.exceptions import ObjectDoesNotExist

django.setup()


def handle_sources(dic):
    merge_and_delete_sources(dic['merge'])
    deprecate_sources(dic['deprecate'])
    delete_sources(dic['delete'])


def delete_sources(lst):
    for pk in lst:
        try:
            source = Source.objects.get(pk=pk)
            source.delete()
        except ObjectDoesNotExist:
            print('Deleting sources exception: '
                  'source with id %s was already deleted'
                  % (pk))


def deprecate_sources(lst):
    for pk in lst:
        try:
            source = Source.objects.get(pk=pk)
            source.deprecated = True
            source.save()
        except ObjectDoesNotExist:
            print('Deprecation sources handling exception: '
                  'source with id %s is missing'
                  % (pk))


def merge_and_delete_sources(dic):
    """Function to merge and delete duplicate Source objects:
    Runs through a dictionary where the key is pk for obj to be merged
    to and value is a list of pk for the duplicate obj (relations
    merged, then obj deleted, see Source.merge_with()).
    """

    for key in dic.keys():
        source = Source.objects.get(pk=key)
        for pk in dic[key]:
            try:
                source.merge_with(pk)
            except ObjectDoesNotExist:
                print('Duplicate sources handling exception: '
                      'duplicate source with id %s was already deleted'
                      % (pk))


def sourcesExist(sources_changes, model):
    sIds = set()
    for k, v in sources_changes['merge'].items():
        sIds.add(k)
        sIds.update(v)
    sIds.update(sources_changes['delete'])
    sIds.update(sources_changes['deprecate'])
    sCount = model.objects.filter(id__in=sIds).count()
    return sCount == len(sIds)
