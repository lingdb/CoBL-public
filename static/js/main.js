(function(){
  "use strict";
  requirejs.config({
    baseUrl: '/ielex/static/',
    paths: {
      'jquery': 'bower_components/jquery/dist/jquery.min',
      'bootstrap': 'bower_components/bootstrap/dist/js/bootstrap.min',
      'lodash': 'bower_components/lodash/dist/lodash.min'
    },
    shim: {
      'bootstrap': {deps: ['jquery']},
      'lodash': {exports: '_'},
      'jquery': {exports: '$'}
    }
  });
  requirejs(['require','jquery','lodash',
             'js/base',
             'js/viewMeaningLanguages',
             'js/viewLanguageMeanings',
             'js/viewTableFilter'],
            function(require, $, _){
    //Initializing viewTableFilter:
    require('js/viewTableFilter').init('table.viewTableFilter');
  });
})();
