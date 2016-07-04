(function(){
  "use strict";
  /**
    See if there is a table#viewLanguageMeanings on the site,
    and color it accordingly.
  */
  return define(['jquery','lodash','js/colors'], function($, _, colors){
    var table = $('table#viewLanguageMeanings');
    if(table.length !== 1) return;
    //Colorize it!
    colors.colorize(colors.findToColor(
      table.find('tbody > tr'),
      function(el){return $(el).data('lexemeid');}));
  });
})();
