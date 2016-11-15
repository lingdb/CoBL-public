(function(){
  "use strict";
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
      'intercom': 'bower_components/intercom/intercom.min'
    },
    shim: {
      'bootstrap': {deps: ['jquery']},
      'floatThead': {deps: ['jquery']},
      'lodash': {exports: '_'},
      'jquery': {exports: '$'},
      'markdown-it': {deps: ['jquery']},
      'awesomplete': {exports: 'Awesomplete'},
      'bootbox': {deps: ['bootstrap']},
      'intercom': {exports: 'intercom'}
    }
  });
  requirejs(['require','jquery','lodash',
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
             'js/updateCounts',
             'js/updatePercentages',
             'js/confirmSubmit',
             'js/copyRowFrom'],
            function(require, $, _){
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
