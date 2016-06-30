(function(){
  "use strict";
  return define(['lodash', 'jquery'], function(_, $){
    $('.typeaheadText').each(function(){
      var input = $(this);
      /*
        Parsing the typeahead map requires unescaping unicode,
        which is inspired by [1].
        [1]: https://stackoverflow.com/a/7885499/448591
      */
      var data = $.parseJSON(input.data('typeahead').replace(
        /\\u([\d\w]{4})/gi,
        function(match, grp){
          return String.fromCharCode(parseInt(grp, 16));
      }));
      console.log('DEBUG', data);
      //Initialize typeahead magic:
///   input.typeahead({
///     hint: true,
///     highlight: true,
///     minLength: 1
///   },{
///     name: 'data-typeahead',
///     source: function(q, λ){
///       // See https://twitter.github.io/typeahead.js/examples/#the-basics
///       var r = new RegExp(q, 'i');
///       λ(_.filter(_.keys(data), function(k){
///         return r.test(k);
///       }));
///     }
///   });
    });
  });
})();
