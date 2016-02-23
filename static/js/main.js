(function(){
  "use strict";
  requirejs.config({
    baseUrl: '/ielex/static/',
    paths: {
      'jquery': 'bower_components/jquery/dist/jquery.min',
      'bootstrap': 'bower_components/bootstrap/dist/js/bootstrap.min'
    },
    shim: {
      'jquery': {exports: '$'},
      'bootstrap': {deps: ['jquery']}
    }
  });
  requirejs(['require','js/base','js/colors'], function(require){
    console.log('Hello World!');
    console.log(require('js/colors'));
  });
})();
