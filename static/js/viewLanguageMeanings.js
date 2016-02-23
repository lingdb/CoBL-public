(function(){
  "use strict";
  /**
    See if there is a table#viewLanguageMeanings on the site,
    and color it accordingly.
  */
  return define(['jquery','lodash','js/colors'], function($, _, colors){
    var table = $('table#viewLanguageMeanings');
    if(table.length !== 1) return;
    console.log('viewLanguageMeanings');
    var toColor = {colorGroups: [], notFounds: [], alones: []},
        buckets = {}; // :: cText -> [window.Element]
    //Filling buckets and notFounds:
    table.find('tbody > tr').each(function(){
      var t = $(this), cText = t.data('lexemeid');
      if(cText === ''){
        toColor.notFounds.push(t);
      }else if(cText in buckets){
        buckets[cText].push(t);
      }else{
        buckets[cText] = [t];
      }
    });
    //Distributing buckets into colorGroups and alones:
    _.each(buckets, function(xs){
      if(xs.length === 1){
        toColor.alones.push(xs);
      }else{
        toColor.colorGroups.push(xs);
      }
    });
    //Colorize it!
    colors.colorize(toColor);
  });
})();
