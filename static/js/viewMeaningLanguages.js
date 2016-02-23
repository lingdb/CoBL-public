(function(){
  "use strict";
  /**
    See if there is a table#viewMeaningLanguages on the site,
    and color it accordingly.
  */
  return define(['jquery','lodash','js/colors'], function($, _, colors){
    var table = $('table#viewMeaningLanguages');
    if(table.length !== 1) return;
    console.log('viewMeaningLanguages');
    //Colorize it!
    colors.colorize(colors.findToColor(
      table.find('tbody > tr'),
      function(el){return $('.cognateClasses', el).text().trim();}));
  });
})();
