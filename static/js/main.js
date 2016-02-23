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
  requirejs(['require','jquery','lodash','js/base','js/colors'], function(require, $, _){
    var cells = [];
    _.each(require('js/colors').allColors, function(c){
      console.log('Got a color: ', c);
      cells.push('<li style="background-color: '+c+';">Lorem ipsum</li>');
    });
    $('body').append('<ul>'+cells.join('')+'</ul>');
  });
})();
