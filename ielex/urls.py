import debug_toolbar
from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login, logout
from django.views.generic import DetailView, \
        ListView, RedirectView
from django.views.static import serve as serveStatic
from ielex.views import add_language_list, \
                        changeDefaults, \
                        cognate_report, \
                        delete_language, \
                        delete_language_list, \
                        delete_meaning, \
                        edit_language, \
                        edit_language_list, \
                        edit_meaning, \
                        edit_wordlist, \
                        overview_language, \
                        language_add_new, \
                        lexeme_add, \
                        lexeme_duplicate, \
                        lexeme_edit, \
                        lexeme_search, \
                        meaning_add_new, \
                        redirect_lexeme_citation, \
                        reorder_language_list, \
                        reorder_wordlist, \
                        revert_version, \
                        source_edit, \
                        source_list, \
                        source_view, \
                        source_import, \
                        source_cognacy, \
                        source_cogset, \
                        source_lexeme, \
                        SourceAutocomplete, \
                        export_bibtex, \
                        viewAbout, \
                        viewAuthors, \
                        view_changes, \
                        view_clades, \
                        view_cognateclasses, \
                        viewDefaultCognateClassList, \
                        viewDefaultLanguage, \
                        viewDefaultMeaning, \
                        view_frontpage, \
                        view_language_check, \
                        view_language_list, \
                        view_language_wordlist, \
                        view_lexeme, \
                        view_meaning, \
                        view_object_history, \
                        view_sndComp, \
                        view_wordlist, \
                        view_wordlists, \
                        view_nexus_export, \
                        view_two_languages_wordlist, \
                        view_language_progress, \
                        view_language_distributions, \
                        json_cognateClass_placeholders, \
                        view_cladecognatesearch, \
                        view_csvExport
from ielex.viewCsvImport import viewCsvImport
from ielex import settings
from ielex.lexicon.views import CognateClassCitationCreateView, \
                                cognate_class_citation_delete, \
                                CognateClassCitationUpdateView, \
                                DumpRawDataView, \
                                NexusExportView
from ielex.lexicon.models import CognateClassCitation, \
                                 CognateJudgement, \
                                 CognateJudgementCitation, \
                                 LanguageList, \
                                 LexemeCitation, \
                                 MeaningList
from django.contrib.staticfiles.urls \
    import staticfiles_urlpatterns
from ielex.profiles.views import view_profile, alter_profile, change_password

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# standard regexes for urls
# url_char = "a-zA-Z0-9$_.+!*'(),-" # unreserved
url_char = "A-Za-z0-9_.~-"  # unreserved
# http://tools.ietf.org/html/rfc3986#section-2.3
R = {
    "COGJUDGE_ID": r"(?P<cogjudge_id>\d+)",
    "COGNATE_NAME": r"(?P<cognate_name>[{0}]+)".format(url_char),
    "DOMAIN": r"(?P<domain>[{0}]+)".format(url_char),
    "LANGUAGE": r"(?P<language>[{0}]+)".format(url_char),
    "LANGUAGELIST": r"(?P<language_list>[{0}]+)".format(url_char),
    "LEXEME_ID": r"(?P<lexeme_id>\d+)",
    "MEANING_ID": r"(?P<meaning_id>\d+)",
    "MEANING": r"(?P<meaning>[{0}]+)".format(url_char),
    "RELATION": r"(?P<relation>[{0}]+)".format(url_char),
    "WORDLIST": r"(?P<wordlist>[{0}]+)".format(url_char),
    "USERNAME": r"(?P<username>[a-zA-Z0-9@.+_-]+)",
    "identifier": r"[a-zA-Z_][a-zA-Z0-9_]*",
    }

urlpatterns = [
    # Front Page
    url(r'^$', view_frontpage, name="view-frontpage"),
    url(r'^changes/$', view_changes, name="view-changes"),
    url(r'^changes/%(USERNAME)s/$' % R, view_changes,
        name="view-changes-user"),

    # csv Exports
    url(r'^csvExport/$', view_csvExport, name="view-csvExport"),

    # Language list
    url(r'^languages/$', view_language_list),
    url(r'^languagelist/add-new/$', add_language_list,
        name="add-language-list"),
    url(r'^languagelist/%(LANGUAGELIST)s/$' % R, view_language_list,
        name="view-language-list"),
    url(r'^languagelist/%s/$' % LanguageList.DEFAULT, view_language_list,
        name="view-all-languages"),
    url(r'^languagelist/%(LANGUAGELIST)s/edit/$' % R, edit_language_list,
        name="edit-language-list"),
    url(r'^languagelist/%(LANGUAGELIST)s/reorder/$' % R, reorder_language_list,
        name="reorder-language-list"),
    url(r'^languagelist/%(LANGUAGELIST)s/delete/$' % R, delete_language_list,
        name="delete-language-list"),
    url(r'^languagelist/$',  # view all language lists
        ListView.as_view(
            queryset=LanguageList.objects.all(),
            context_object_name="language_lists"),
        name="view-language-lists"),

    # Language progress (#311):
    url(r'^languageprogress/%(LANGUAGELIST)s/$' % R, view_language_progress,
        name="view-language-progress"),

    # Language distributions:
    url(r'^languagedistributions/%(LANGUAGELIST)s/$' % R,
        view_language_distributions,
        name="view-language-distributions"),

    # Language check (#159):
    url(r'^language/check$' % R, view_language_check),
    url(r'^language/%(LANGUAGE)s/check$' % R, view_language_check,
        {"wordlist": MeaningList.DEFAULT}),
    url(r'^language/%(LANGUAGE)s/wordlist/%(WORDLIST)s/check$' % R,
        view_language_check),

    # Language
    url(r'^language/$' % R, viewDefaultLanguage),
    url(r'^language/%(LANGUAGE)s/$' % R, view_language_wordlist,
        {"wordlist": MeaningList.DEFAULT}, name="language-report"),
    url(r'^language/%(LANGUAGE)s/wordlist/%(WORDLIST)s/$' % R,
        view_language_wordlist, name="view-language-wordlist"),
    url(r'^language/%(LANGUAGE)s/edit/$' % R, edit_language,
        name="language-edit"),
    url(r'^language/%(LANGUAGE)s/overview/$' % R, overview_language,
        name="language-overview"),
    url(r'^language/%(LANGUAGE)s/delete/$' % R, delete_language,
        name="language-delete"),
    url(r'^language/%(LANGUAGE)s/add-lexeme/' % R,
        lexeme_add, name="language-add-lexeme"),
    # this should be
    # url(r'^language/%(LANGUAGE)s/meaning/%(MEANING)s/add/' % R,
    url(r'^language/%(LANGUAGE)s/meaning/%(MEANING)s/add-lexeme/' % R,
        lexeme_add, name="language-meaning-add-lexeme"),
    # add new language to a language list # XXX do we need this?
    url(r'^languagelist/%(LANGUAGELIST)s/add-new/$' % R, language_add_new,
        name="language-add-new"),

    # Clades:
    url(r'^clades/$' % R, view_clades),
    # SndComp sets:
    url(r'^sndComp/$' % R, view_sndComp),
    # Clade cognate search:
    url(r'^cladecognatesearch/$' % R, view_cladecognatesearch),

    # Meanings (aka wordlist)
    url(r'^wordlists/$', view_wordlists, name="view-wordlists"),
    url(r'^wordlist/%(WORDLIST)s/$' % R, view_wordlist, name="view-wordlist"),
    url(r'^wordlist/%(WORDLIST)s/edit/$' % R, edit_wordlist,
        name="edit-wordlist"),
    url(r'^wordlist/%(WORDLIST)s/reorder/$' % R, reorder_wordlist,
        name="reorder-wordlist"),
    url(r'^meanings/$', view_wordlist,
        {"wordlist": MeaningList.DEFAULT}, name="view-meanings"),
    url(r'^meanings/add-new/$', meaning_add_new, name="meaning-add-new"),
    url(r'^meaning/%(MEANING)s/edit/$' % R, edit_meaning,
        name="edit-meaning"),

    # Meaning
    # TODO
    # - refactor out remaining report_meaning calls
    url(r'^meaning/%(MEANING)s/add-lexeme/$' % R, lexeme_add,
        name="meaning-add-lexeme"),
    url(r'^meaning/%(MEANING)s/languagelist/%(LANGUAGELIST)s/$' % R,
        view_meaning,
        name="view-meaning-languages"),
    url(r'^meaning/%(MEANING)s/languagelist/'
        '%(LANGUAGELIST)s/add-cognate/%(LEXEME_ID)s/$' % R,
        view_meaning, name="view-meaning-languages-add-cognate"),
    url(r'^meaning/%(MEANING)s/$' % R, view_meaning, {"language_list": None},
        name="meaning-report"),
    url(r'^meaning/%(MEANING)s/delete/$' % R, delete_meaning,
        name="delete-meaning"),  # XXX needs confirm dialog
    url(r'^meaning/%(MEANING)s/language/%(LANGUAGE)s/add-lexeme/' % R,
        lexeme_add, name="meaning-language-add-lexeme"),
    url(r'^meaning/$' % R, viewDefaultMeaning),

    # Lexemes
    url(r'^lexeme/add/', lexeme_add),
    url(r'^lexeme/search/$', lexeme_search, name="lexeme-search"),

    url(r'^lexeme/%(LEXEME_ID)s/duplicate/$' % R, lexeme_duplicate),
    url(r'^lexeme/%(LEXEME_ID)s/$' % R,
        view_lexeme, name="view-lexeme"),
    url(r'^lexeme/%(LEXEME_ID)s/edit/$' % R,
        lexeme_edit, {"action": "edit"}, name="edit-lexeme"),
    url(r'^lexeme/%(LEXEME_ID)s/add-cognate/$' % R,
        lexeme_edit, {"action": "add-cognate"},
        name="lexeme-add-cognate"),
    url(r'^lexeme/%(LEXEME_ID)s/add-new-citation/$' % R,
        lexeme_edit, {"action": "add-new-citation"},
        name="lexeme-add-new-citation"),
    url(r'^lexeme/%(LEXEME_ID)s/add-citation/$' % R,
        lexeme_edit, {"action": "add-citation"}, name="lexeme-add-citation"),
    url(r'^lexeme/%(LEXEME_ID)s/edit-citation/(?P<citation_id>\d+)/$' % R,
        lexeme_edit, {"action": "edit-citation"}, name="lexeme-edit-citation"),
    url(r'^lexeme/%(LEXEME_ID)s/delink-citation/(?P<citation_id>\d+)/$' % R,
        lexeme_edit, {"action": "delink-citation"},
        name="lexeme-delink-citation"),
    url(r'^lexeme/%(LEXEME_ID)s/delink-cognate/%(COGJUDGE_ID)s/$' % R,
        lexeme_edit, {"action": "delink-cognate"},
        name="lexeme-delink-cognate"),
    url(r'^lexeme/%(LEXEME_ID)s/edit-cognate-citation/'
        '(?P<citation_id>\d+)/$' % R,
        lexeme_edit, {"action": "edit-cognate-citation"},
        name="lexeme-edit-cognate-citation"),  # just use <cogjudge_id>
    url(r'^lexeme/%(LEXEME_ID)s/delink-cognate-citation/'
        '(?P<citation_id>\d+)/$' % R,
        lexeme_edit, {"action": "delink-cognate-citation"},
        name="lexeme-delink-cognate-citation"),
    url(r'^lexeme/%(LEXEME_ID)s/add-cognate-citation/%(COGJUDGE_ID)s/$' % R,
        lexeme_edit, {"action": "add-cognate-citation"},
        name="lexeme-add-cognate-citation"),
    url(r'^lexeme/%(LEXEME_ID)s/add-new-cognate-citation'
        '/%(COGJUDGE_ID)s/$' % R,
        lexeme_edit, {"action": "add-new-cognate-citation"}),
    url(r'^lexeme/%(LEXEME_ID)s/add-new-cognate/$' % R,
        lexeme_edit, {"action": "add-new-cognate"},
        name="lexeme-add-new-cognate"),
    url(r'^lexeme/%(LEXEME_ID)s/delete/$' % R,
        lexeme_edit, {"action": "delete"}),
    # url(r'^lexeme/(?P<lexeme_id>\d+)/citation/(?P<pk>\d+)/$',
    #         DetailView.as_view(model=LexemeCitation,
    #                 context_object_name="citation"),
    #         name="lexeme-citation-detail"),
    url(r'^lexeme/citation/(?P<pk>\d+)/$',
        DetailView.as_view(
            model=LexemeCitation,
            context_object_name="citation"),
        name="lexeme-citation-detail"),
    url(r'^lexeme/%(LEXEME_ID)s/citation/$' % R, redirect_lexeme_citation),

    # Sources
    url(r'^sources/$', source_list, name="view-sources"),
    url(r'^sources/(?P<source_id>\d+)/$', source_view, name="view-source"),
    url(r'^sources/(?P<source_id>\d+)/edit/$', source_edit, {"action": "edit"},
        name="edit-source"),
    url(r'^sources/(?P<source_id>\d+)/delete/$',
        source_edit, {"action": "delete"},
        name="delete-source"),
    url(r'^sources/add/$', source_edit, {"action": "add"}),
    url(r'^sources/add/cognate-judgement/%(COGJUDGE_ID)s/$' % R,
        source_edit, {"action": "add"}, name="cogjudge-add-new-source"),
    url(r'^sources/add/lexeme/%(LEXEME_ID)s/$' % R,
        source_edit, {"action": "add"},
        name="lexeme-add-new-source"),
    url(r'^sources/import/$', source_import.as_view(), name="import-sources"),
    url(r'^sources/export/$', export_bibtex, name="export-sources-bibtex"),

    url(r'^sources/(?P<source_id>\d+)/cognacy/$',
        source_cognacy, name="source-cognacy"),
    url(r'^sources/(?P<source_id>\d+)/cogset/$',
        source_cogset, name="source-cogset"),
    url(r'^sources/(?P<source_id>\d+)/lexeme/$',
        source_lexeme, name="source-lexeme"),
    url(
        r'^source-autocomplete/$',
        SourceAutocomplete.as_view(),
        name='source-autocomplete',
    ),

    # Cognate
    url(r'^cognate/(?P<cognate_id>\d+)/$', cognate_report, name="cognate-set"),
    url(r'^cognate/%(COGNATE_NAME)s/$' % R, cognate_report),
    url(r'^meaning/%(MEANING)s/cognate/(?P<code>[A-Z]+[0-9]*)/$' % R,
        cognate_report),
    url(r'^cognateclasslist/$' % R, viewDefaultCognateClassList),
    url(r'^meaning/%(MEANING)s/cognateclasslist/$' % R,
        view_cognateclasses, name="edit-cogclasses"),

    # About pages:
    url(r'about/(.+)/' % R, viewAbout, name="viewAbout"),

    # Authors:
    url(r'^authors/$' % R, viewAuthors, name='viewAuthors'),

    # Changing defaults:
    url(r'^changeDefaults/$' % R, changeDefaults),

    # Cognate citation :: detail
    url(r'^cognate/citation/(?P<pk>\d+)/$',
        DetailView.as_view(
            model=CognateClassCitation,
            context_object_name="citation"),
        name="cognate-class-citation-detail"),
    # handle redundant cognate_id
    url(r'^cognate/(?P<cognate_id>\d+)/citation/(?P<pk>\d+)/$',
        RedirectView.as_view(url="/cognate/citation/%(pk)s/",
                             permanent=True),
        name="cognate-class-citation-view"),
    # Cognate citation :: update
    url(r'^cognate/citation/(?P<pk>\d+)/edit/$',
        login_required(CognateClassCitationUpdateView.as_view()),
        name="cognate-citation-edit"),
    # handle redundant cognate_id
    url(r'^cognate/(?P<cognate_id>\d+)/citation/(?P<pk>\d+)/edit/$',
        RedirectView.as_view(url="/cognate/citation/%(pk)s/edit/",
                             permanent=True),
        name="cognate-class-citation-edit"),
    # Cognate citation :: add
    url(r'^cognate/(?P<cognate_id>\d+)/add-citation/$',
        login_required(CognateClassCitationCreateView.as_view()),
        name="cognate-class-citation-create"),
    # Cognate citation :: delete
    url(r'^cognate/citation/(?P<pk>\d+)/delete/$',
        login_required(cognate_class_citation_delete),
        name="cognate-citation-delete"),


    # Cognate judgement :: detail
    url(r'^cognate/judgement/(?P<pk>\d+)/$',
        DetailView.as_view(model=CognateJudgement,
                           context_object_name="judgement"),
        name="cognate-judgement-detail"),
    # Cognate judgement citation :: detail
    url(r'^cognate/judgement/(?P<judgement_id>\d+)/citation/(?P<pk>\d+)/$',
        DetailView.as_view(model=CognateJudgementCitation,
                           context_object_name="citation"),
        name="cognate-judgement-citation-detail"),

    # Added for #256:
    url(r'^twoLanguages/$', view_two_languages_wordlist),
    url(r'^twoLanguages/([^\/]+)/$', view_two_languages_wordlist),
    url(r'^twoLanguages/([^\/]+)/([^\/]+)/$', view_two_languages_wordlist),
    url(r'^twoLanguages/([^\/]+)/([^\/]+)/([^\/]+)/$',
        view_two_languages_wordlist,
        name="view-two-languages"),

    # Added for #51:
    url(r'^json/cognateClassPlaceholders/$', json_cognateClass_placeholders),

    url(r'^revert/(?P<revision_id>\d+)/$', revert_version, name="revert-item"),
    url(r'^object-history/(?P<version_id>\d+)/$', view_object_history),
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    ]

# urls to include iff the extensional semantic module is activated
if settings.semantic_domains:
    urlpatterns += [('', include('ielex.extensional_semantics.urls'))]

urlpatterns += [
    url(r'^nexus/$', login_required(NexusExportView.as_view()), name="nexus"),
    url(r'^nexus/export/(?P<exportId>\d+)/$',
        view_nexus_export,
        name="view_nexus_export"),
    url(r'^nexus/export/$', view_nexus_export, name="view_nexus_export_base"),
    url(r'^dump/$', login_required(DumpRawDataView.as_view()), name="dump")]

urlpatterns += [
    url(r'^login/$', login,
        {'template_name': 'profiles/login.html'},
        name="login"),
    url(r'^logout/$', logout, {'template_name':
        'profiles/logout.html'}, name="logout")]

urlpatterns += [
    url(r'^admin/viewCsvImport', viewCsvImport, name="viewCsvImport")]

urlpatterns += [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^user/$', view_profile, name="view-profile"),
    url(r'^user/alter/$', alter_profile, name='alter-profile'),
    url(r'^user/change-password/$', change_password, name='change-password'),
    # public profile
    url(r'^user/%(USERNAME)s/$' % R, view_profile, name="view-profile-user"),
    ]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:  # additional urls for testing purposes
    urlpatterns += [
        # this is needed for running the development server
        url(r'^static/(?P<path>.*)$', serveStatic,
            {'document_root': settings.STATIC_ROOT}),
        url(r'^__debug__/', include(debug_toolbar.urls))
    ]

# vim:nowrap
