from django.conf.urls import *
from ielex.extensional_semantics.views import *
from ielex.urls import R

# TODO move these views to:
# from ielex.extensional_semantics.views import *

urlpatterns = patterns('',

    # Semantic relations
    url(r'^relation/add/$', add_relation, name="add-relation"),
    url(r'^relation/%(RELATION)s/edit/$' % R, edit_relation,
            name="edit-relation"),
    url(r'^relation/%(RELATION)s/$' % R, view_relation,
            name="view-relation"),

    # Semantic domains (lists of semantic relations)
    url(r'^domains/$', domains_list, name="view-domains"),
    url(r'^domains/add-new/$', add_semantic_domain, name="add-semantic-domain"),
    url(r'^domain/%(DOMAIN)s/$' % R, view_semantic_domain,
            name="view-semantic-domain"),
    url(r'^domain/%(DOMAIN)s/edit/$' % R, edit_semantic_domain,
            name="edit-semantic-domain"),
    url(r'^domain/%(DOMAIN)s/delete/$' % R, delete_semantic_domain,
            name="delete-semantic-domain"),

    url(r'^language/%(LANGUAGE)s/domain/%(DOMAIN)s/$' % R,
            language_domain_view, name="language-domain-view"),
    url(r'^language/%(LANGUAGE)s/domains/$' % R,
            language_domains_list, name="language-domains-list"),

    # Semantic extensions of lexemes -- within a specified domain
    url(r'^lexeme/%(LEXEME_ID)s/domains/$' % R,
            lexeme_domains_list, name="lexeme-domains-list"),
    url(r'^lexeme/%(LEXEME_ID)s/domain/%(DOMAIN)s/$' % R,
            lexeme_domain_view, name="lexeme-domain-view"),
    url(r'^lexeme/%(LEXEME_ID)s/extensions/$' % R,
            lexeme_extensions_view, name="lexeme-extensions-view"),
    # TODO isn't working yet
    url(r'^lexeme/%(LEXEME_ID)s/domain/%(DOMAIN)s/edit/$' % R,
            lexeme_domain_view, {"action":"edit"}, name="edit-lexeme-extensions"),

    # Semantic extensions of lexemes -- individual extensions
    url(r'^domain/%(DOMAIN)s/extension/(?P<extension_id>\d+)/add-citation/$' % R,
            add_lexeme_extension_citation, name="add-domain-extension-citation"),
    url(r'^extension/(?P<extension_id>\d+)/add-citation/$',
            add_lexeme_extension_citation, name="extension-add-citation"),
    # url(r'^extension/(?P<extension_id>\d+)/$', 
    #         view_lexeme_extension_citation, name="view-extension"),


    # citation/object/id patterns
    url(r'^citation/extension/(?P<citation_id>\d+)/$',
            extension_citation_view, name="citation-extension-view"),
    )
