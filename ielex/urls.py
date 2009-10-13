from django.conf.urls.defaults import *
from ielex.views import *

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

    # Select which languages to consider (e.g. Germanic)
    #('^select\/languages/$', view_languages),
    # Select which words to consider (e.g. Swadesh 100)
    #('^select\/words/$', view_words),

    (r'^test-form/$', test_form),

    # Example:
    # (r'^ielex/', include('ielex.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
