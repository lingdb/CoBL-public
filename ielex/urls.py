from django.conf.urls.defaults import *
from ielex.views import *
from ielex import settings
from ielex.lexicon.views import *
from ielex.lexicon.models import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# additional arguments can be passed with a dictionary

# TODO: refactoring. Make standard patterns/capture names into a dictionary of
# centralized # variables (DNRY), e.g. 
# regex_patterns = # {LANGUAGE:"(?P<language>[a-zA-Z0-9_ -]+)" ,
#               MEANING:"(?P<meaning>[a-zA-Z0-9_ ]+|\d+)"} etc., 
# then build the urls as url(r'/language/%(LANGUAGE)s/' % patterns ... )

R = {"DOMAIN":"(?P<domain>[a-zA-Z0-9_.-]+)",
    "RELATION":"(?P<relation>[a-zA-Z0-9_.-]+)",  
    }

urlpatterns = patterns('',
    # Front Page
    url(r'^$', view_frontpage, name="view-frontpage"),
    url(r'^backup/$', make_backup),
    url(r'^changes/$', view_changes, name="view-changes"),
    # url(r'^touch/(?P<model_name>[a-zA-Z0-9_ ]+)/(?P<model_id>\d+)/', touch),

    # Languages
    url(r'^languages/$', view_language_list, name="view-languages"),
    url(r'^languages/reorder/$', language_reorder, name="language-reorder"),
    url(r'^languages/add-new/$', language_add_new, name="language-add-new"),
    url(r'^languages/sort/(?P<ordered_by>sort_key|utf8_name)/$', sort_languages,
            name="language-sort"),
    # TODO add something to edit language_list descriptions

    # Language
    url(r'^language/([a-zA-Z0-9_ -]+)/$', report_language,
            name="language-report"), # usage {% url language-report English %}
    url(r'^language/(?P<language>[a-zA-Z0-9_ -]+)/edit/$', edit_language,
            name="language-edit"),
    url(r'^language/(?P<language>[a-zA-Z0-9_ -]+)/add-lexeme/',
            lexeme_add, {"return_to":"/language/%(language)s/"}),
    url(r'^language/(?P<language>[a-zA-Z0-9_ -]+)/add-lexeme/(?P<meaning>[a-zA-Z0-9_ ]+)/',
            lexeme_add, {"return_to":"/language/%(language)s/"}),

    # Meanings
    url(r'^meanings/$', view_meanings, name="view-meanings"),
    url(r'^meanings/add-new/$', meaning_add_new, name="meaning-add-new"), # NEW XXX
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+)/edit/$', edit_meaning,
            name="meaning-edit"), # NEW XXX

    # Meaning
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+)/add-lexeme/$', lexeme_add,
            {"return_to":"/meaning/%(meaning)s/"}),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/$', report_meaning,
            name="meaning-report"),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/add/$', report_meaning,
            name="meaning-add-lexeme"),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/(?P<lexeme_id>\d+)/$',
            report_meaning, {"action":"goto"}),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/(?P<lexeme_id>\d+)/add/$',
            report_meaning, {"action":"add"}),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/(?P<lexeme_id>\d+)/(?P<cogjudge_id>\d+)/$',
            report_meaning),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/add-lexeme/',
            lexeme_add, {"return_to":"/meaning/%(meaning)s/"}),
    url(r'^meaning/(?P<meaning>[a-zA-Z0-9_ ]+|\d+)/add-lexeme/(?P<language>[a-zA-Z0-9_ ]+)/',
            lexeme_add, {"return_to":"/meaning/%(meaning)s/"}),

    # Lexemes
    url(r'^lexeme/add/', lexeme_add, {"return_to":"/meanings/"}),
    url(r'^lexeme/search/$', lexeme_search, name="lexeme-search"),

    url(r'^lexeme/(?P<lexeme_id>\d+)/duplicate/$', lexeme_duplicate),
    url(r'^lexeme/(?P<lexeme_id>\d+)/$',
            view_lexeme, name="view-lexeme"),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>add-citation|edit|add-cognate|add-new-citation)/$',
            lexeme_edit),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>edit-citation|delink-citation)/(?P<citation_id>\d+)/$',
            lexeme_edit),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>delink-cognate)/(?P<cogjudge_id>\d+)/$',
            lexeme_edit),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>edit-cognate-citation)/(?P<citation_id>\d+)/$',
            lexeme_edit), # just use <cogjudge_id>
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>delink-cognate-citation)/(?P<citation_id>\d+)/$',
            lexeme_edit),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>add-cognate-citation|add-new-cognate-citation)/(?P<cogjudge_id>\d+)/$',
            lexeme_edit),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>add-new-cognate)/$', lexeme_edit),
    url(r'^lexeme/(?P<lexeme_id>\d+)/(?P<action>delete)/$', lexeme_edit),

    # Sources
    url(r'^sources/$', source_list, name="view-sources"),
    url(r'^source/(?P<source_id>\d+)/$', source_edit),
    url(r'^source/(?P<source_id>\d+)/(?P<action>edit|delete)/$', source_edit),
    url(r'^source/(?P<action>add)/$', source_edit),
    url(r'^source/(?P<action>add)/cognate-judgement/(?P<cogjudge_id>\d+)/$', source_edit),
    url(r'^source/(?P<action>add)/lexeme/(?P<lexeme_id>\d+)/$', source_edit),

    # Cognates
    url(r'^cognate/(?P<cognate_id>\d+)/$', cognate_report, name="cognate-set"),
    url(r'^cognate/(?P<cognate_id>\d+)/(?P<action>edit)/$', cognate_report),
    url(r'^cognate/(?P<meaning>[a-zA-Z0-9_ ]+)/(?P<code>[A-Z]+)/$',
            cognate_report),

    url(r'^revert/(?P<version_id>\d+)/$', revert_version),
    url(r'^object-history/(?P<version_id>\d+)/$', view_object_history),

    # Semantic relations
    url(r'^relation/add/$', add_relation, name="add-relation"),
    url(r'^relation/%(RELATION)s/edit/$' % R, edit_relation,
            name="edit-relation"),
    url(r'^relation/%(RELATION)s/$' % R, view_relation,
            name="view-relation"),

    # Semantic domains (lists of Semantic relations)
    url(r'^domains/$', view_domains, name="view-domains"),
    url(r'^domains/add-new/$', add_relation_list, name="add-relation-list"),
    url(r'^domain/%(DOMAIN)s/$' % R, view_relation_list,
            name="view-relation-list"),
    url(r'^domain/%(DOMAIN)s/edit/$' % R, edit_relation_list,
            name="edit-relation-list"),
    url(r'^domain/%(DOMAIN)s/delete/$' % R, delete_relation_list,
            name="delete-relation-list"),

    # Semantic extensions of lexemes
    url(r'^lexeme/(?P<lexeme_id>\d+)/domains/$',
            view_lexeme_semantic_domains, name="view-all-lexeme-extensions"),
    url(r'^lexeme/(?P<lexeme_id>\d+)/domain/(?P<domain>[a-zA-Z0-9_]+)/$',
            view_lexeme_semantic_extensions, name="view-lexeme-extensions"),
    # TODO isn't working yet
    url(r'^lexeme/(?P<lexeme_id>\d+)/domain/(?P<domain>[a-zA-Z0-9_]+)/edit/$',
            view_lexeme_semantic_extensions, {"action":"edit"}, name="edit-lexeme-extensions"),
    url(r'^domain/(?P<domain>[a-zA-Z0-9_]+)/extension/(?P<extension_id>\d+)/add-citation/$',
            add_lexeme_extension_citation, name="add-domain-extension-citation"),
    url(r'^extension/(?P<extension_id>\d+)/add-citation/$',
            add_lexeme_extension_citation, name="add-extension-citation"),
    # url(r'^extension/(?P<extension_id>\d+)/$', 
    #         view_lexeme_extension_citation, name="view-extension"),
    url(r'^citation/extension/(?P<citation_id>\d+)/$',
            view_extension_citation, name="view-extension-citation"),

    url(r'^language/(?P<language>[a-zA-Z0-9_ -]+)/domain/%(DOMAIN)s/$' % R,
            view_language_semantic_domain, name="view-language-domain"),
    url(r'^language/(?P<language>[a-zA-Z0-9_ -]+)/domains/$',
            view_language_semantic_domains, name="view-language-domains"),

    # Example:
    # (r'^ielex/', include('ielex.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    )

urlpatterns += patterns('',
        (r'^nexus/$', 'ielex.lexicon.views.list_nexus'),
        (r'^nexus-data/$', 'ielex.lexicon.views.write_nexus'),
        )

urlpatterns += patterns('django.contrib.auth',
    (r'^accounts/login/$','views.login', {'template_name':
        'profiles/login.html'}),
    (r'^accounts/logout/$','views.logout', {'template_name':
        'profiles/logout.html'}),
    )

urlpatterns += patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/profile/$', 'ielex.profiles.views.view_profile'),
    (r'^accounts/alter/profile/$', 'ielex.profiles.views.alter_profile'),
    (r'^accounts/change-password/$', 'ielex.profiles.views.change_password'),
    (r'^accounts/profile/(?P<username>.+)/$',
        'ielex.profiles.views.view_profile'),
    (r'^accounts/alter/profile/(?P<username>.+)/$',
        'ielex.profiles.views.alter_profile'),
    )

if settings.DEBUG: # additional urls for testing purposes
    urlpatterns += patterns('',
    # this is needed for running the development server
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),
    )

# vim:nowrap
