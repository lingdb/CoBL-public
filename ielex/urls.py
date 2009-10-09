from django.conf.urls.defaults import *
from ielex.views import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Front Page
    ('^$', view_frontpage),
    # List of languages in the database
    ('^languages/$', view_languages),
    # List of meanings in the database
    ('^words/$', view_words),
    # Swadesh list for one language
    (r'^language/([a-zA-Z0-9_ ]+)/$', report_language),
    # All forms in the database with a particular meaning
    (r'^word/([a-zA-Z0-9_ ]+|\d+)/$', report_word),
    # Select which languages to consider (e.g. Germanic)
    #('^select\/languages/$', view_languages),
    # Select which words to consider (e.g. Swadesh 100)
    #('^select\/words/$', view_words),


    # Example:
    # (r'^ielex/', include('ielex.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
