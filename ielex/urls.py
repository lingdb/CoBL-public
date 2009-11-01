from django.conf.urls.defaults import *
from ielex.views import *
from ielex import settings
from ielex.lexicon.views import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

# additional arguments can be passed with a dictionary

urlpatterns = patterns('',
    # Front Page
    url(r'^$', view_frontpage, name="view-frontpage"),
    url(r'^backup/$', make_backup),

    # Languages
    url(r'^languages/$', view_languages, name="view-languages"),
    url(r'^languages/reorder/$', reorder_languages, name="language-reorder"),
    url(r'^languages/sort/(?P<ordered_by>sort_key|ascii_name)/$', sort_languages,
            name="language-sort"),

    # Language
    url(r'^language/([a-zA-Z0-9_ ]+)/$', report_language,
            name="language-report"), # usage {% url language-report English %}
    url(r'^language/(?P<language>[a-zA-Z0-9_ ]+)/edit/$', edit_language,
            name="language-edit"),
    url(r'^language/(?P<language>[a-zA-Z0-9_ ]+|\d+)/add-lexeme/',
            lexeme_add, {"return_to":"/language/%(language)s/"}),
    url(r'^language/(?P<language>[a-zA-Z0-9_ ]+|\d+)/add-lexeme/(?P<meaning>[a-zA-Z0-9_ ]+)/',
            lexeme_add, {"return_to":"/language/%(language)s/"}),

    # Meanings
    url(r'^meanings/$', view_meanings, name="view-meanings"),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/$', report_meaning,
            name="meaning-report"),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/add/$', report_meaning,
            name="meaning-add-lexeme"),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/(?P<lexeme_id>\d+)/add/$',
            report_meaning),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/(?P<lexeme_id>\d+)/(?P<cogjudge_id>\d+)/$',
            report_meaning),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/add-lexeme/',
            lexeme_add, {"return_to":"/meaning/%(meaning)s/"}),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/add-lexeme/(?P<language>[a-zA-Z0-9_ ]+)/',
            lexeme_add, {"return_to":"/meaning/%(meaning)s/"}),

    # Lexemes
    url(r'^lexeme/add/', lexeme_add, {"return_to":"/meanings/"}),
    url(r'^lexeme/(?P<lexeme_id>\d+)/duplicate', lexeme_add,
        {"return_to":"/meaning/%(meaning)s"}),
    url(r'^lexeme/(?P<lexeme_id>\d+)/$',
            lexeme_report, name="lexeme-report"),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>add-citation|edit-lexeme|add-cognate|add-new-citation)/$',
            lexeme_report),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>edit-citation|delink-citation)/(?P<citation_id>\d+)/$',
            lexeme_report),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>delink-cognate)/(?P<cogjudge_id>\d+)/$',
            lexeme_report),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>edit-cognate-citation)/(?P<citation_id>\d+)/$',
            lexeme_report), # just use <cogjudge_id>
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>delink-cognate-citation)/(?P<citation_id>\d+)/$',
            lexeme_report),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>add-cognate-citation|add-new-cognate-citation)/(?P<cogjudge_id>\d+)/$',
            lexeme_report),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>add-new-cognate)/$', lexeme_report),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>delete)/$', lexeme_report),

    # Sources
    url(r'^sources/$', source_list, name="view-sources"),
    url(r'^source/(?P<source_id>\d+)/$', source_edit),
    url(r'^source/(?P<source_id>\d+)/(?P<action>edit|delete)/$', source_edit),
    url(r'^source/(?P<action>add)/$', source_edit),
    url(r'^source/(?P<action>add)/cognate-judgement/(?P<cogjudge_id>\d+)/$', source_edit),
    url(r'^source/(?P<action>add)/lexeme/(?P<lexeme_id>\d+)/$', source_edit),

    # Cognates
    url(r'^cognate/(?P<cognate_id>\d+)/$', cognate_report),
    url(r'^cognate/(?P<cognate_id>\d+)/(?P<action>edit)/$', cognate_report),


    # Example:
    # (r'^ielex/', include('ielex.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    )

urlpatterns += patterns('',
        (r'^nexus/$', 'ielex.lexicon.views.list_nexus'),
        (r'^nexus/(?P<language_list>[a-zA-Z0-9_ ]+)/$', 'ielex.lexicon.views.write_nexus'),
        )

urlpatterns += patterns('django.contrib.auth',
    (r'^accounts/login/$','views.login', {'template_name': 'profiles/login.html'}),
    (r'^accounts/logout/$','views.logout'),
    )

urlpatterns += patterns('',
    (r'^accounts/profile/$', 'ielex.profiles.views.view_profile'),
    (r'^accounts/profile/alter/$', 'ielex.profiles.views.view_profile',
        {"action":"alter"}),
    )

if settings.DEBUG: # additional urls for testing purposes
    urlpatterns += patterns('',
    # this is needed for running the development server
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),
    )

# vim:nowrap
