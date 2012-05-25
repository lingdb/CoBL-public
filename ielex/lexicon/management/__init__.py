import lexicon.models

def callback(sender, **kwargs):
    # according to # https://docs.djangoproject.com/en/dev/ref/signals/#post-syncdb 
    # it is risky to make database changes here, as it can cause the flush
    # management command to fail. 
    LanguageList.objects.get_or_create(name=LanguageList.DEFAULT)
    MeaningList.objects.get_or_create(name=MeaningList.DEFAULT)

    msg = """If the database has just been installed, you should now:

  * Customize ``local_settings.py`` with name of database etc.

  * Run ``python manage.py migrate`` to update all the database schemas etc to
    the most current version"""
    return

post_syncdb.connect(callback, sender=lexicon.models)


