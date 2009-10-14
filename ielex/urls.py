from django.conf.urls.defaults import *
from ielex.views import *
from ielex import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Front Page
    ('^$', view_frontpage),
    # List of languages in the database
    url('^languages/$', view_languages, name="language-listing"),
    # List of meanings in the database
    url('^words/$', view_words, name="word-listing"),
    # Swadesh list for one language
    url(r'^language/([a-zA-Z0-9_ ]+)/$', report_language,
            name="language-report"), # usage {% url language-report English %}
    # All forms in the database with a particular meaning
    url(r'^word/([a-zA-Z0-9_ ]+|\d+)/(edit/|add/)?$', report_word,
            name="word-report"),
    url(r'^word/([a-zA-Z0-9_ ]+|\d+)/(edit)/(\d+)/$', report_word,
            name="word-report"),
    url(r'^source/word/(\d+)/', word_source,
            name="word-source"),

    # Example:
    # (r'^ielex/', include('ielex.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    )


if settings.DEBUG: # additional urls for testing purposes
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',  
         {'document_root':     settings.MEDIA_ROOT}),

    # XXX zap me
    # (r'^test-form/$', test_form),
    (r'^test-form/new-word/$', test_form_newword),
    (r'^test-form/choose-source/$', test_form_choosesource),
    (r'^test-form/choose-language/$', test_form_chooselanguage),
    (r'^test-form/new-source/$', test_form_newsource),
    (r'^test-success/', test_success),

    )
