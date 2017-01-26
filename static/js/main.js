(function(){
  "use strict";
  /* global requirejs */
  requirejs.config({
    baseUrl: '/ielex/static/',
    paths: {
      'jquery': 'bower_components/jquery/dist/jquery.min',
      'floatThead': 'bower_components/jquery.floatThead/dist/jquery.floatThead.min',
      'bootstrap': 'bower_components/bootstrap/dist/js/bootstrap.min',
      'lodash': 'bower_components/lodash/dist/lodash.min',
      'markdown-it': 'bower_components/markdown-it/dist/markdown-it.min',
      'bootbox': 'bower_components/bootbox.js/bootbox',
      'awesomplete': 'bower_components/awesomplete/awesomplete.min',
      'c3': 'bower_components/c3/c3.min',
      'd3': 'bower_components/d3/d3.min',
      'intercom': 'bower_components/intercom/intercom.min',
      'dal-init1': 'bower_components/django-autocomplete-light/src/dal/static/admin/js/jquery.init',
      'dal-init2': 'bower_components/django-autocomplete-light/src/dal/static/autocomplete_light/jquery.init',
      'dal-init': 'bower_components/django-autocomplete-light/src/dal/static/autocomplete_light/autocomplete.init',
      'dal-forward': 'bower_components/django-autocomplete-light/src/dal/static/autocomplete_light/forward',
      'dal-select2': 'bower_components/django-autocomplete-light/src/dal_select2/static/autocomplete_light/select2',
      'select2': 'bower_components/select2/dist/js/select2.full.min',
      'django-dynamic-formset': 'bower_components/django-dynamic-formset/src/jquery.formset'
    },
    shim: {
      'bootstrap': {deps: ['jquery']},
      'floatThead': {deps: ['jquery']},
      'lodash': {exports: '_'},
      'jquery': {exports: '$'},
      'markdown-it': {deps: ['jquery']},
      'awesomplete': {exports: 'Awesomplete'},
      'bootbox': {deps: ['bootstrap']},
      'intercom': {exports: 'intercom'},
      //Stiched together by djanoAutocompleteInclusion:
      'dal-init1': {deps: ['jquery'], exports: 'django'},
      'dal-init2': {deps: ['dal-init1'], exports: 'yl'},
      'dal-forward': {deps: ['jquery'], exports: 'get_forwards'},
      'dal-select2': {deps: ['dal-init2', 'dal-forward', 'select2']},
      'dal-init': {deps: ['dal-init2', 'dal-forward', 'dal-select2']},
      'select2': {deps: ['jquery']},
      'django-dynamic-formset': {deps: ['jquery']}
    }
  });
  requirejs(['require','jquery',
             'bootstrap',
             'js/base',
             'js/mirrorTextInputs',
             'js/viewMeaningLanguages',
             'js/viewLanguageMeanings',
             'js/viewTableFilter',
             'js/viewMarkDown',
             'js/distributionSelection',
             'js/cloneLanguage',
             'js/mergeCognateClasses',
             'js/typeahead',
             'js/bootboxHtmlSnippet',
             'js/inputDepends',
             'js/editCognateClass',
             'js/gatherDistributions',
             'js/plotDistributions',
             'js/nexus',
             'js/datetooltip',
             'js/longInput',
             'js/updateCounts',
             'js/updatePercentages',
             'js/confirmSubmit',
             'js/copyCognateClass',
             'js/djangoAutocompleteInclusion',
             'js/sourcePopUpScript',
             'js/source_list',
             'js/problematicRomanised'
            ], function(require, $){
    //Initializing viewTableFilter:
    require('js/viewTableFilter').init('table.viewTableFilter');
    require('js/updateCounts').init();
    require('js/updatePercentages').init();
    //Rendering MarkDown:
    (function(viewMarkDown){
      $('.markdown').each(function(){
        var target = $(this);
        viewMarkDown.render(target);
        target.removeClass('markdown');
      });
    })(require('js/viewMarkDown'));

    require('js/editCognateClass').init();
    require('js/confirmSubmit').init();
  });
})();
