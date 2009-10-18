from django.conf.urls.defaults import *
from ielex.views import *
from ielex import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Front Page
    url('^$', view_frontpage, name="view-frontpage"),

    # Languages
    url('^languages/$', view_languages, name="view-languages"),
    url(r'^language/([a-zA-Z0-9_ ]+)/$', report_language,
            name="language-report"), # usage {% url language-report English %}

    ## # All forms in the database with a particular meaning
    ## url(r'^word/([a-zA-Z0-9_ ]+|\d+)/(edit/|add/)?$', report_word,
    ##         name="word-report"),
    ## url(r'^word/([a-zA-Z0-9_ ]+|\d+)/(edit)/(\d+)/$', report_word,
    ##         name="word-report"), # XXX

    # Meanings
    url(r'^meanings/$', view_meanings, name="view-meanings"),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/$', report_meaning,
            name="meaning-report"),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/(?P<lexeme_id>\d+)/$',
            report_meaning),

    # Lexemes
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>add-citation|edit-lexeme|add-cognate)?/$',
            lexeme_report, name="lexeme-report"),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>edit-citation)/(?P<citation_id>\d+)/$',
            lexeme_report),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>edit-cognate)/(?P<cognate_class_id>\d+)/(?P<citation_id>\d+)/$',
            lexeme_report),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>add-cognate-citation)/(?P<cognate_class_id>\d+)/$',
            lexeme_report),

    # Sources
    url(r'^sources/$', source_list),
    url(r'^source/(?P<source_id>\d+)/$', source_edit),
    url(r'^source/(?P<source_id>\d+)/(?P<action>edit)/$', source_edit),
    url(r'^source/(?P<action>add)$', source_edit),

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
    # this is needed for running the development server
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),

    (r'^test-form/$', test_form),
    (r'^test-form/new-word/$', test_form_newword),
    (r'^test-form/choose-source/$', test_form_choosesource),
    (r'^test-form/choose-language/$', test_form_chooselanguage),
    (r'^test-success/', test_success),

    )

# vim:nowrap
